"""
Self-contained File Downloader plugin for xtension-bot
- Uses python-telegram-bot (async) Application interface; exposes setup(app)
- Stores metadata, channels and queue in a local SQLite DB (default plugins/file_downloader.db)
- Has an asyncio background worker pool (configurable) that processes a persistent queue with retry/backoff
- Optional S3 offload (requires boto3 and AWS creds in env), uploaded after successful download
- Admin-only commands (controlled by FILEDL_ADMIN_IDS env or permissive if not set):
  /addchannel, /removechannel, /listchannels, /save (reply to forwarded file), /status, /queuesize
- Self-contained: creates DB/tables and storage path automatically; no changes required to main bot

Config via environment variables:
- FILEDL_STORAGE_DIR (default: downloads)
- FILEDL_DB_PATH (default: plugins/file_downloader.db)
- FILEDL_ADMIN_IDS (comma separated user ids; if empty all users are allowed)
- FILEDL_MAX_WORKERS (default: 2)
- FILEDL_MAX_RETRIES (default: 5)
- FILEDL_S3_BUCKET (optional; when set plugin tries to upload to this S3 bucket)
- FILEDL_AWS_REGION (optional; default aws region)

Notes:
- This expects your main bot to load the plugin and call setup(application).
- Requires python-telegram-bot v20+ and optionally boto3 for S3.
"""

import os
import asyncio
import sqlite3
import json
import logging
import time
import hashlib
from pathlib import Path
from typing import Optional
from contextlib import closing
from datetime import datetime

from telegram import Update, Message
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, Application

# Configuration
STORAGE_DIR = Path(os.environ.get("FILEDL_STORAGE_DIR", "downloads"))
DB_PATH = Path(os.environ.get("FILEDL_DB_PATH", "plugins/file_downloader.db"))
ADMIN_USER_IDS = {int(u) for u in os.environ.get("FILEDL_ADMIN_IDS", "").split(",") if u.strip().isdigit()}
MAX_WORKERS = int(os.environ.get("FILEDL_MAX_WORKERS", "2"))
MAX_RETRIES = int(os.environ.get("FILEDL_MAX_RETRIES", "5"))
S3_BUCKET = os.environ.get("FILEDL_S3_BUCKET")
AWS_REGION = os.environ.get("FILEDL_AWS_REGION")

# Ensure storage
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    h = logging.StreamHandler()
    fmt = logging.Formatter("[filedl] %(asctime)s %(levelname)s: %(message)s")
    h.setFormatter(fmt)
    logger.addHandler(h)
logger.setLevel(logging.INFO)

# DB helpers
def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER UNIQUE NOT NULL,
                title TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_unique_id TEXT UNIQUE,
                chat_id INTEGER,
                message_id INTEGER,
                filename TEXT,
                path TEXT,
                status TEXT,
                retries INTEGER DEFAULT 0,
                md5 TEXT,
                sha256 TEXT,
                s3_url TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_unique_id TEXT,
                file_id TEXT,
                chat_id INTEGER,
                message_id INTEGER,
                filename TEXT,
                retries INTEGER DEFAULT 0,
                status TEXT DEFAULT 'queued',
                created_at TEXT,
                last_attempt TEXT
            )
            """
        )
        conn.commit()

# small helpers
def is_admin(user_id: int) -> bool:
    if not ADMIN_USER_IDS:
        return True
    return user_id in ADMIN_USER_IDS

async def run_in_executor(func, *args):
    return await asyncio.get_event_loop().run_in_executor(None, lambda: func(*args))

# S3 uploader (optional)
def s3_upload_sync(local_path: str, key: str) -> Optional[str]:
    try:
        import boto3
    except Exception:
        logger.exception("boto3 not available; skipping S3 upload")
        return None
    sess = boto3.session.Session()
    s3 = sess.client("s3", region_name=AWS_REGION) if AWS_REGION else sess.client("s3")
    # key should be relative path in bucket
    s3.upload_file(local_path, S3_BUCKET, key)
    # construct public / path (not necessarily public)
    return f"s3://{S3_BUCKET}/{key}"

# queue and worker
class Downloader:
    def __init__(self, app: Application):
        self.app = app
        self.queue = asyncio.Queue()
        self.workers = []
        self.running = False

    async def start(self):
        if self.running:
            return
        self.running = True
        init_db()
        # load pending queued items from DB into in-memory queue
        await self._load_pending()
        for _ in range(max(1, MAX_WORKERS)):
            w = asyncio.create_task(self._worker_loop())
            self.workers.append(w)
        logger.info(f"Started {len(self.workers)} downloader workers")

    async def stop(self):
        self.running = False
        for _ in self.workers:
            await self.queue.put(None)
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

    async def _load_pending(self):
        with closing(get_conn()) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM queue WHERE status IN ('queued','retry') ORDER BY id")
            rows = cur.fetchall()
            for r in rows:
                # push into queue tuples
                await self.queue.put(dict(r))
            logger.info(f"Loaded {len(rows)} pending items into queue")

    async def enqueue(self, file_unique_id: str, file_id: str, chat_id: int, message_id: int, filename: str):
        now = datetime.utcnow().isoformat()
        with closing(get_conn()) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO files (file_unique_id, chat_id, message_id, filename, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                (file_unique_id, chat_id, message_id, filename, 'queued', now, now),
            )
            cur.execute(
                "INSERT INTO queue (file_unique_id, file_id, chat_id, message_id, filename, status, created_at) VALUES (?,?,?,?,?,?,?)",
                (file_unique_id, file_id, chat_id, message_id, filename, 'queued', now),
            )
            conn.commit()
            qid = cur.lastrowid
        await self.queue.put({
            'id': qid,
            'file_unique_id': file_unique_id,
            'file_id': file_id,
            'chat_id': chat_id,
            'message_id': message_id,
            'filename': filename,
            'retries': 0,
            'status': 'queued',
        })
        logger.info(f"Enqueued {filename} ({file_unique_id})")

    async def _worker_loop(self):
        while True:
            item = await self.queue.get()
            if item is None:
                # shutdown sentinel
                break
            await self._process_item(item)
            self.queue.task_done()

    async def _process_item(self, item):
        qid = item.get('id')
        file_unique_id = item.get('file_unique_id')
        file_id = item.get('file_id')
        chat_id = item.get('chat_id')
        message_id = item.get('message_id')
        filename = item.get('filename')
        retries = item.get('retries', 0)

        attempt = retries + 1
        try:
            # update queue last_attempt
            with closing(get_conn()) as conn:
                cur = conn.cursor()
                cur.execute("UPDATE queue SET last_attempt=? WHERE id=?", (datetime.utcnow().isoformat(), qid))
                conn.commit()

            # download via bot API (blocking call through PTB async file download)
            # get chat and message using app.bot
            bot = self.app.bot
            # We need to call get_file and download_to_drive; both are async in PTB
            file_obj = await bot.get_file(file_id)
            safe_chat = "".join(c for c in (str(chat_id)) if c.isalnum())
            target_dir = STORAGE_DIR / safe_chat
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / filename

            logger.info(f"Starting download {filename} for message {message_id}")
            await file_obj.download_to_drive(custom_path=str(target_path))

            # compute hashes
            md5, sha256 = await run_in_executor(_compute_hashes, str(target_path))

            # update files table
            with closing(get_conn()) as conn:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE files SET path=?, status=?, retries=?, md5=?, sha256=?, updated_at=? WHERE file_unique_id=?",
                    (str(target_path), 'downloaded', retries, md5, sha256, datetime.utcnow().isoformat(), file_unique_id),
                )
                cur.execute("UPDATE queue SET status=? WHERE id= ?", ('done', qid))
                conn.commit()

            # optionally upload to S3
            if S3_BUCKET:
                key = f"{safe_chat}/{filename}"
                try:
                    s3_url = await asyncio.to_thread(s3_upload_sync, str(target_path), key)
                    with closing(get_conn()) as conn:
                        cur = conn.cursor()
                        cur.execute("UPDATE files SET s3_url=? WHERE file_unique_id=?", (s3_url, file_unique_id))
                        conn.commit()
                    logger.info(f"Uploaded to {s3_url}")
                except Exception:
                    logger.exception("S3 upload failed; continuing")

            # notify chat (best effort, use send_message in context)
            try:
                await bot.send_message(chat_id=chat_id, text=f"File saved: {filename}")
            except Exception:
                # ignore failures to notify (channel may not accept messages from bot)
                logger.debug("Could not send notification to chat")

        except Exception as e:
            logger.exception("Download failed")
            # exponential backoff and retry
            if retries + 1 >= MAX_RETRIES:
                # mark failed
                with closing(get_conn()) as conn:
                    cur = conn.cursor()
                    cur.execute("UPDATE files SET status=?, retries=?, updated_at=? WHERE file_unique_id=?",
                                ('failed', retries + 1, datetime.utcnow().isoformat(), file_unique_id))
                    cur.execute("UPDATE queue SET status=? WHERE id=?", ('failed', qid))
                    conn.commit()
                logger.error(f"Giving up on {filename} after {retries+1} attempts")
            else:
                backoff = min(60, 2 ** retries)
                await asyncio.sleep(backoff)
                # schedule retry: increment retries in DB and re-enqueue
                with closing(get_conn()) as conn:
                    cur = conn.cursor()
                    cur.execute("UPDATE queue SET retries=retries+1, status=? WHERE id=?", ('retry', qid))
                    conn.commit()
                item['retries'] = retries + 1
                await self.queue.put(item)


def _compute_hashes(path: str):
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
            sha256.update(chunk)
    return md5.hexdigest(), sha256.hexdigest()

# Plugin commands and handlers
_downloader: Optional[Downloader] = None

async def cmd_addchannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("You are not allowed to use this command.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /addchannel <@channelusername or channel_id>")
        return
    chat_ref = context.args[0]
    try:
        chat = await context.bot.get_chat(chat_ref)
    except Exception as e:
        await update.message.reply_text(f"Cannot find chat: {e}")
        return
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO channels (chat_id, title) VALUES (?,?)", (chat.id, chat.title))
        conn.commit()
    await update.message.reply_text(f"Added channel to monitor: {chat.title or chat.id}")

async def cmd_removechannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("You are not allowed to use this command.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /removechannel <@channelusername or channel_id>")
        return
    chat_ref = context.args[0]
    try:
        chat = await context.bot.get_chat(chat_ref)
    except Exception as e:
        await update.message.reply_text(f"Cannot find chat: {e}")
        return
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM channels WHERE chat_id=?", (chat.id,))
        conn.commit()
    await update.message.reply_text(f"Removed channel: {chat.title or chat.id}")

async def cmd_listchannels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("You are not allowed to use this command.")
        return
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT chat_id, title FROM channels")
        rows = cur.fetchall()
    if not rows:
        await update.message.reply_text("No channels monitored.")
        return
    lines = [f"{r['title'] or r['chat_id']} ({r['chat_id']})" for r in rows]
    await update.message.reply_text("Monitored channels:\n" + "\n".join(lines))

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("You are not allowed to use this command.")
        return
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as total FROM files WHERE status='downloaded'")
        downloaded = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) as queued FROM queue WHERE status IN ('queued','retry')")
        queued = cur.fetchone()[0]
    await update.message.reply_text(f"Downloaded files: {downloaded}\nQueue size: {queued}")

async def cmd_queuesize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = _downloader.queue.qsize() if _downloader else 0
    await update.message.reply_text(f"In-memory queue size: {q}")

async def cmd_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # save a forwarded message: reply to the message with /save
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message containing a file and run /save.")
        return
    msg = update.message.reply_to_message
    await _process_and_enqueue(msg, context)

async def channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post
    if not msg:
        return
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM channels WHERE chat_id=?", (msg.chat.id,))
        ok = cur.fetchone()
    if not ok:
        return
    await _process_and_enqueue(msg, context)

async def _process_and_enqueue(msg: Message, context: ContextTypes.DEFAULT_TYPE):
    # detect available media and gather file_id and unique id
    file_id = None
    file_unique_id = None
    filename = None
    if msg.document:
        file_id = msg.document.file_id
        file_unique_id = msg.document.file_unique_id
        filename = msg.document.file_name or f"{file_unique_id}.bin"
    elif msg.video:
        file_id = msg.video.file_id
        file_unique_id = msg.video.file_unique_id
        filename = msg.video.file_name or f"{file_unique_id}.mp4"
    elif msg.audio:
        file_id = msg.audio.file_id
        file_unique_id = msg.audio.file_unique_id
        filename = msg.audio.file_name or f"{file_unique_id}.mp3"
    elif msg.animation:
        file_id = msg.animation.file_id
        file_unique_id = msg.animation.file_unique_id
        filename = msg.animation.file_name or f"{file_unique_id}.gif"
    elif msg.voice:
        file_id = msg.voice.file_id
        file_unique_id = msg.voice.file_unique_id
        filename = f"{file_unique_id}.ogg"
    elif msg.photo:
        photo = msg.photo[-1]
        file_id = photo.file_id
        file_unique_id = photo.file_unique_id
        filename = f"{file_unique_id}.jpg"
    else:
        try:
            await msg.reply_text("No downloadable file found in the message.")
        except Exception:
            pass
        return

    # dedupe: check files table
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT status, path FROM files WHERE file_unique_id=?", (file_unique_id,))
        r = cur.fetchone()
        if r:
            try:
                await msg.reply_text(f"File already processed: {r['path']}")
            except Exception:
                pass
            return
    # enqueue
    await _downloader.enqueue(file_unique_id=file_unique_id, file_id=file_id, chat_id=msg.chat.id, message_id=msg.message_id, filename=filename)
    try:
        await msg.reply_text(f"Queued {filename} for download")
    except Exception:
        pass

# plugin setup

def setup(app: Application):
    global _downloader
    _downloader = Downloader(app)
    # register handlers
    app.add_handler(CommandHandler("addchannel", cmd_addchannel))
    app.add_handler(CommandHandler("removechannel", cmd_removechannel))
    app.add_handler(CommandHandler("listchannels", cmd_listchannels))
    app.add_handler(CommandHandler("save", cmd_save))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("queuesize", cmd_queuesize))
    # channel posts
    app.add_handler(MessageHandler(filters.CHANNEL & filters.ALL, channel_post_handler))

    # start background downloader when bot is ready
    async def _on_startup(_: Application):
        await _downloader.start()

    async def _on_shutdown(_: Application):
        await _downloader.stop()

    app.post_init(_on_startup)
    app.stop(_on_shutdown)

# allow running directly for testing
if __name__ == '__main__':
    print("This plugin is intended to be loaded by xtension-bot. Run the main bot to use it.")
