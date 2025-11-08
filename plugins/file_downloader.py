"""
Xtension Bot File Downloader Plugin (Telethon)

Robust plugin for asynchronous, persistent file downloads from monitored channels and private admin commands.
Features:
- Add/remove channels to monitor by channel ID (admin only in private chat).
- Queue all channel media messages and allow manual file save (/save command).
- Persistent SQLite WAL queue: survives restarts/crash.
- Async background workers, configurable count (MAX_WORKERS).
- Dedupe and retry with exponential backoff.
- Unified admin system: core bot admin + plugin allowlist, all sensitive/admin ops are private-only.
- Clear, human-readable, and enriched logging (file + console, respects LOG_LEVEL).
- Guards against double worker/log startup (see comments for details).
- All management commands are private/admin only for maximum security.

Commands:
/addchannel <chat_id>     - Monitor a new channel (private admin chat)
/removechannel <chat_id>  - Remove monitored channel (private admin chat)
/listchannels             - Show all monitored channel IDs
/save (on reply)          - Save the replied-to message's file (admin/private only)
/status                   - Show queue/download stats
/queuesize                - Show current queue length
/allowuser <id|@username> - Add plugin admin (admin/private only)
/revokeuser <id|@username>- Remove plugin admin (admin/private only)
/confirm <token>          - Confirm admin change
/listadmins               - Show all core/plugin admins
/lasterrors [n]           - Show last n plugin error logs

Author: Copilot for Khapra – Nov 2025
"""

import os
import re
import sqlite3
import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from telethon import events

# --- Config ---
STORAGE_DIR = Path(os.getenv("FILEDL_STORAGE_DIR", "/app/downloads"))
DB_PATH = Path(os.getenv("FILEDL_DB_PATH", "/app/data/file_downloader.db"))
LOG_PATH = Path(os.getenv("FILEDL_LOG_PATH", "/app/data/file_downloader.log"))
MAX_WORKERS = int(os.getenv("FILEDL_MAX_WORKERS", "2"))
MAX_RETRIES = int(os.getenv("FILEDL_MAX_RETRIES", "5"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# --- Logging ---
logger = logging.getLogger("filedl")
logger.handlers.clear()
file_handler = RotatingFileHandler(str(LOG_PATH), maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
console_handler = logging.StreamHandler(sys.stdout)
file_fmt = logging.Formatter("[%(asctime)s] %(levelname)-8s | %(message)s")
console_fmt = logging.Formatter("[%(asctime)s] %(levelname)-8s | %(name)s: %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(file_fmt)
console_handler.setFormatter(console_fmt)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

def log_debug(msg, **ctx):
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(msg + (" | " + " ".join(f"{k}={v}" for k, v in ctx.items()) if ctx else ""))

def log_info(msg, **ctx):
    logger.info(msg + (" | " + " ".join(f"{k}={v}" for k, v in ctx.items()) if ctx else ""))

def log_error(msg, **ctx):
    logger.error(msg + (" | " + " ".join(f"{k}={v}" for k, v in ctx.items()) if ctx else ""))

# --- DB and helpers ---
def _safe_filename(name):
    if not name: return "file.bin"
    return re.sub(r"[^\w\-_. ]+", "_", name)[:200]

def _gen_token():
    return hashlib.sha1(f"{time.time()}-{os.urandom(8)}".encode()).hexdigest()[:12]

def _get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def _init_db():
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("""CREATE TABLE IF NOT EXISTS channels (
            chat_id INTEGER PRIMARY KEY,
            added_by INTEGER,
            added_at TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT,
            file_unique TEXT,
            chat_id INTEGER,
            message_id INTEGER,
            filename TEXT,
            path TEXT,
            status TEXT,
            retries INTEGER DEFAULT 0,
            md5 TEXT,
            sha256 TEXT,
            created_at TEXT,
            updated_at TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT,
            file_unique TEXT,
            chat_id INTEGER,
            message_id INTEGER,
            filename TEXT,
            retries INTEGER DEFAULT 0,
            status TEXT DEFAULT 'queued',
            created_at TEXT,
            last_attempt TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS plugin_admins (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            added_by INTEGER,
            added_at TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS pending_admins (
            token TEXT PRIMARY KEY,
            action TEXT,
            user_id INTEGER,
            username TEXT,
            requested_by INTEGER,
            requested_at TEXT,
            expires_at TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            message TEXT,
            context_json TEXT,
            created_at TEXT)""")
        conn.commit()

def _compute_hashes(path):
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
            sha256.update(chunk)
    return md5.hexdigest(), sha256.hexdigest()

def sender_display(sender):
    """Get the sender name/title for reply messages."""
    if hasattr(sender, "first_name") and sender.first_name:
        who = sender.first_name
    elif hasattr(sender, "title") and sender.title:
        who = sender.title
    else:
        who = getattr(sender, "username", "unknown")
    return who

# --- Main Plugin Class ---
class TelethonPlugin:
    # Shared set so even if core loads/reloads, only one instance logs as "initialized"
    instance_ids = set()
    def __init__(self, bot):
        self.bot = bot
        self.commands = {
            "/addchannel":  "Add channel (private admin chat)",
            "/removechannel":"Remove channel (private admin chat)",
            "/listchannels": "Show monitored channels",
            "/save":        "Reply to file, queue/save (private admin chat)",
            "/status":      "Show download/queue status",
            "/queuesize":   "Queue size",
            "/allowuser":   "Add plugin admin (private chat)",
            "/revokeuser":  "Remove plugin admin (private chat)",
            "/confirm":     "Confirm pending admin change",
            "/listadmins":  "Show core/plugin admins",
            "/lasterrors":  "Show recent error logs"
        }
        self._in_memory_queue = asyncio.Queue()
        _init_db()
        self._workers_started = False
        self.instance_id = id(self)
        # Only log instance creation once per actual instance
        if self.instance_id not in TelethonPlugin.instance_ids:
            TelethonPlugin.instance_ids.add(self.instance_id)
            log_info("FileDownloader plugin instance initialized", instance_id=self.instance_id, loglevel=LOG_LEVEL)

    async def _is_admin(self, user_id):
        if hasattr(self.bot, "admin_ids") and user_id in self.bot.admin_ids:
            return True
        loop = asyncio.get_running_loop()
        def admin_in_db(uid):
            with _get_conn() as conn:
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM plugin_admins WHERE user_id=?", (uid,))
                return cur.fetchone() is not None
        return await loop.run_in_executor(None, admin_in_db, user_id)

    async def _enqueue_db(self, file_id, file_unique, chat_id, message_id, filename):
        """Add file to persistent DB + memory queue."""
        now = datetime.utcnow().isoformat()
        def insert_queue():
            with _get_conn() as conn:
                cur = conn.cursor()
                cur.execute("INSERT OR IGNORE INTO files (file_id, file_unique, chat_id, message_id, filename, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                    (str(file_id), file_unique, chat_id, message_id, filename, "queued", now, now))
                cur.execute("INSERT INTO queue (file_id, file_unique, chat_id, message_id, filename, status, created_at) VALUES (?,?,?,?,?,?,?)",
                    (str(file_id), file_unique, chat_id, message_id, filename, "queued", now))
                conn.commit()
                return cur.lastrowid
        loop = asyncio.get_running_loop()
        qid = await loop.run_in_executor(None, insert_queue)
        log_info("Enqueued file for download", file_id=file_id, filename=filename, chat_id=chat_id, queue_id=qid)
        await self._in_memory_queue.put({
            "id": qid, "file_id": str(file_id), "file_unique": file_unique,
            "chat_id": chat_id, "message_id": message_id, "filename": filename,
            "retries": 0, "status": "queued"
        })

    async def _worker(self, worker_id):
        """Async background downloader for queued files."""
        log_info("Downloader worker started", worker=worker_id, instance_id=self.instance_id)
        while True:
            item = await self._in_memory_queue.get()
            if item is None: break
            qid = item.get("id")
            file_id = item.get("file_id")
            file_unique = item.get("file_unique")
            chat_id = item.get("chat_id")
            message_id = item.get("message_id")
            filename = item.get("filename")
            retries = item.get("retries", 0)
            try:
                msg = await self.bot.get_messages(chat_id, ids=message_id)
                if not msg: raise RuntimeError("Cannot fetch telegram message")
                safe_chat = str(chat_id).lstrip("-")
                target_dir = Path(STORAGE_DIR) / safe_chat
                target_dir.mkdir(parents=True, exist_ok=True)
                safe_name = _safe_filename(filename or str(file_unique or message_id))
                target_path = target_dir / safe_name
                log_info("Worker downloading file...", worker=worker_id, file=safe_name, chat_id=chat_id, message_id=message_id, instance_id=self.instance_id)
                path = await self.bot.download_media(msg, file=str(target_path))
                if not path: raise RuntimeError("Failed to download media")
                md5, sha256 = await asyncio.get_running_loop().run_in_executor(None, _compute_hashes, str(path))
                def finish_db():
                    with _get_conn() as conn:
                        cur = conn.cursor()
                        cur.execute("UPDATE files SET path=?, status=?, retries=?, md5=?, sha256=?, updated_at=? WHERE file_unique=?",
                            (str(path), "downloaded", retries, md5, sha256, datetime.utcnow().isoformat(), file_unique))
                        cur.execute("UPDATE queue SET status=? WHERE id=?", ("done", qid))
                        conn.commit()
                await asyncio.get_running_loop().run_in_executor(None, finish_db)
                log_info("Downloaded and saved file", worker=worker_id, target_path=str(target_path), md5=md5, sha256=sha256, instance_id=self.instance_id)
                try: await self.bot.send_message(chat_id, f"File saved: {safe_name}")
                except Exception: log_debug("Chat notify failed (nonfatal)", chat_id=chat_id)
            except Exception as e:
                log_error("Worker download error", worker=worker_id, message=str(e), file=filename, queue_id=qid, retries=retries, instance_id=self.instance_id)
                def err_db():
                    with _get_conn() as conn:
                        cur = conn.cursor()
                        cur.execute("INSERT INTO events (level, message, context_json, created_at) VALUES (?,?,?,?)",
                            ("ERROR", str(e), str(item), datetime.utcnow().isoformat()))
                        if retries+1 >= MAX_RETRIES:
                            cur.execute("UPDATE files SET status=?, retries=?, updated_at=? WHERE file_unique=?",
                                ("failed", retries+1, datetime.utcnow().isoformat(), file_unique))
                            cur.execute("UPDATE queue SET status=? WHERE id=?", ("failed", qid))
                        else:
                            cur.execute("UPDATE queue SET retries=retries+1, status=? WHERE id=?", ("retry", qid))
                        conn.commit()
                await asyncio.get_running_loop().run_in_executor(None, err_db)
                if retries+1 < MAX_RETRIES:
                    log_info("Retrying failed download after backoff", file=filename, attempt=retries+1, worker=worker_id, instance_id=self.instance_id)
                    await asyncio.sleep(min(60, 2**retries))
                    item["retries"] = retries+1
                    await self._in_memory_queue.put(item)
            finally:
                self._in_memory_queue.task_done()

    def register_handlers(self):
        # Double-start protection: only start workers for first instance (prevents duplicate logs/workers in reload)
        if not self._workers_started and self.instance_id in TelethonPlugin.instance_ids:
            for i in range(MAX_WORKERS):
                asyncio.create_task(self._worker(i + 1))  # Only once per plugin per process
            self._workers_started = True
            log_info("Downloader plugin started workers", workers=MAX_WORKERS, instance_id=self.instance_id)

        # --- Admin/private commands ---
        @self.bot.on(events.NewMessage(pattern=r'/hello'))
        async def hello_handler(event):
            sender = await event.get_sender()
            who = sender_display(sender)
            await event.reply(f'Hello {who}! 👋\nFile Downloader plugin active.')

        @self.bot.on(events.NewMessage(pattern=r'^/addchannel(?:\s+(-?\d+))?$'))
        async def addchannel(event):
            if not await self._is_admin(event.sender_id):
                return await event.reply("Admins only.")
            if not event.is_private:
                return await event.reply("Please run /addchannel in private chat.")
            m = event.pattern_match
            if not m or not m.group(1):
                return await event.reply("Usage: /addchannel <chat_id> (e.g. -1001234567890)")
            try:
                chat_id = int(m.group(1).strip())
            except Exception:
                return await event.reply("Invalid channel ID, must be integer.")
            now = datetime.utcnow().isoformat()
            def doit():
                with _get_conn() as conn:
                    cur = conn.cursor()
                    cur.execute("INSERT OR REPLACE INTO channels (chat_id, added_by, added_at) VALUES (?,?,?)",
                        (chat_id, event.sender_id, now))
                    conn.commit()
            await asyncio.get_running_loop().run_in_executor(None, doit)
            log_info("Channel added for monitoring", chat_id=chat_id, sender_id=event.sender_id)
            await event.reply(f"Added channel to monitor: {chat_id}")

        @self.bot.on(events.NewMessage(pattern=r'^/removechannel(?:\s+(-?\d+))?$'))
        async def removechannel(event):
            if not await self._is_admin(event.sender_id):
                return await event.reply("Admins only.")
            if not event.is_private:
                return await event.reply("Please run /removechannel in private chat.")
            m = event.pattern_match
            if not m or not m.group(1):
                return await event.reply("Usage: /removechannel <chat_id>")
            try:
                chat_id = int(m.group(1).strip())
            except Exception:
                return await event.reply("Invalid channel ID.")
            def doit():
                with _get_conn() as conn:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM channels WHERE chat_id=?", (chat_id,)); conn.commit()
            await asyncio.get_running_loop().run_in_executor(None, doit)
            log_info("Channel removed from monitoring", chat_id=chat_id, sender_id=event.sender_id)
            await event.reply(f"Removed channel: {chat_id}")

        @self.bot.on(events.NewMessage(pattern=r'^/listchannels$'))
        async def listchannels(event):
            if not await self._is_admin(event.sender_id):
                return await event.reply("Admins only.")
            def doit():
                with _get_conn() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT chat_id FROM channels")
                    return cur.fetchall()
            rows = await asyncio.get_running_loop().run_in_executor(None, doit)
            lines = [f"{r['chat_id']}" for r in rows]
            await event.reply("Monitored channel IDs:\n" + ("\n".join(lines) if lines else "None"))
            log_info("Listed monitored channels", sender_id=event.sender_id, num_channels=len(lines))

        @self.bot.on(events.NewMessage(pattern=r"^/save$"))
        async def save_cmd(event):
            if not await self._is_admin(event.sender_id): return await event.reply("Admins only.")
            if not event.is_private: return await event.reply("Please use /save in private chat.")
            if not event.is_reply: return await event.reply("Reply to the message that contains the file and use /save.")
            msg = await event.get_reply_message()
            log_info("Manual save requested", sender_id=event.sender_id, reply_id=msg.id)
            await self._process_and_enqueue(msg, event)

        @self.bot.on(events.NewMessage(pattern=r"^/status$"))
        async def status_cmd(event):
            def doit():
                with _get_conn() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT COUNT(*) as total FROM files WHERE status='downloaded'")
                    dl = cur.fetchone()["total"]
                    cur.execute("SELECT COUNT(*) as queued FROM queue WHERE status IN ('queued','retry')")
                    q = cur.fetchone()["queued"]
                    return dl, q
            dl, q = await asyncio.get_running_loop().run_in_executor(None, doit)
            await event.reply(f"Downloaded: {dl}\nQueue size: {q}")
            log_info("Plugin status requested", sender_id=event.sender_id, downloaded=dl, queued=q)

        @self.bot.on(events.NewMessage(pattern=r"^/queuesize$"))
        async def queuesize_cmd(event):
            await event.reply(f"In-memory queue size: {self._in_memory_queue.qsize()}")
            log_debug("Queue size reported", sender_id=event.sender_id, queuesize=self._in_memory_queue.qsize())

        @self.bot.on(events.NewMessage(pattern=r"^/allowuser(?:\s+(.+))?$"))
        async def allowuser_cmd(event):
            if not await self._is_admin(event.sender_id): return await event.reply("Admins only.")
            if not event.is_private: return await event.reply("Please use /allowuser in private chat.")
            m = event.pattern_match
            if not m or not m.group(1): return await event.reply("Usage: /allowuser <user_id|@username>")
            target = m.group(1).strip()
            user_id = None
            username = None
            try:
                if target.startswith("@"):
                    ent = await self.bot.get_entity(target)
                    user_id = ent.id
                    username = ent.username
                else:
                    user_id = int(target)
            except Exception: return await event.reply("Invalid user identifier")
            token = _gen_token()
            now = datetime.utcnow()
            expires = (now + timedelta(minutes=10)).isoformat()
            def doit():
                with _get_conn() as conn:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO pending_admins (token, action, user_id, username, requested_by, requested_at, expires_at) VALUES (?,?,?,?,?,?,?)",
                        (token, "add", user_id, username, event.sender_id, now.isoformat(), expires))
                    conn.commit()
            await asyncio.get_running_loop().run_in_executor(None, doit)
            log_info("Allowuser: token generated", target=target, token=token)
            await event.reply(f"Confirm adding user {user_id} by sending:\n/confirm {token}\nExpires at {expires} UTC")

        @self.bot.on(events.NewMessage(pattern=r"^/revokeuser(?:\s+(.+))?$"))
        async def revokeuser_cmd(event):
            if not await self._is_admin(event.sender_id): return await event.reply("Admins only.")
            if not event.is_private: return await event.reply("Please use /revokeuser in private chat.")
            m = event.pattern_match
            if not m or not m.group(1): return await event.reply("Usage: /revokeuser <user_id|@username>")
            target = m.group(1).strip()
            user_id = None
            username = None
            try:
                if target.startswith("@"):
                    ent = await self.bot.get_entity(target)
                    user_id = ent.id
                    username = ent.username
                else:
                    user_id = int(target)
            except Exception: return await event.reply("Invalid user identifier")
            token = _gen_token()
            now = datetime.utcnow()
            expires = (now + timedelta(minutes=10)).isoformat()
            def doit():
                with _get_conn() as conn:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO pending_admins (token, action, user_id, username, requested_by, requested_at, expires_at) VALUES (?,?,?,?,?,?,?)",
                        (token, "revoke", user_id, username, event.sender_id, now.isoformat(), expires))
                    conn.commit()
            await asyncio.get_running_loop().run_in_executor(None, doit)
            log_info("Revokeuser: token generated", target=target, token=token)
            await event.reply(f"Confirm revoking user {user_id} by sending:\n/confirm {token}\nExpires at {expires} UTC")

        @self.bot.on(events.NewMessage(pattern=r"^/confirm(?:\s+(.+))?$"))
        async def confirm_cmd(event):
            if not await self._is_admin(event.sender_id): return await event.reply("Admins only.")
            if not event.is_private: return await event.reply("Please use /confirm in private chat.")
            m = event.pattern_match
            if not m or not m.group(1): return await event.reply("Usage: /confirm <token>")
            token = m.group(1).strip()
            def doit():
                with _get_conn() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT * FROM pending_admins WHERE token=?", (token,))
                    row = cur.fetchone()
                    if not row: return False,"Token not found"
                    if datetime.fromisoformat(row["expires_at"]) < datetime.utcnow():
                        cur.execute("DELETE FROM pending_admins WHERE token=?", (token,))
                        conn.commit()
                        return False,"Token expired"
                    action = row["action"]
                    user_id = row["user_id"]
                    username = row["username"]
                    if action == "add":
                        cur.execute("INSERT OR IGNORE INTO plugin_admins (user_id, username, added_by, added_at) VALUES (?, ?, ?, ?)",
                            (user_id, username, row["requested_by"], datetime.utcnow().isoformat()))
                        cur.execute("DELETE FROM pending_admins WHERE token=?", (token,))
                        conn.commit()
                        return True,f"User {user_id} added to plugin admins"
                    if action == "revoke":
                        cur.execute("DELETE FROM plugin_admins WHERE user_id=?", (user_id,))
                        cur.execute("DELETE FROM pending_admins WHERE token=?", (token,))
                        conn.commit()
                        return True,f"User {user_id} removed from plugin admins"
                    return False,"Unknown action"
            ok, msg = await asyncio.get_running_loop().run_in_executor(None, doit)
            log_info("Admin token confirmation", token=token, status=ok, message=msg)
            await event.reply(msg)

        @self.bot.on(events.NewMessage(pattern=r"^/listadmins$"))
        async def listadmins_cmd(event):
            core_admin_ids = getattr(self.bot, "admin_ids", [])
            def doit():
                with _get_conn() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT user_id, username FROM plugin_admins"); rows = cur.fetchall()
                    return rows
            plugin_admins = await asyncio.get_running_loop().run_in_executor(None, doit)
            text = "**Core Bot Admins:**\n"
            text += "\n".join(str(x) for x in core_admin_ids) if core_admin_ids else "None"
            text += "\n\n**Plugin Extra Admins:**\n"
            if plugin_admins:
                for adm in plugin_admins:
                    text += f"- {adm['user_id']} (@{adm['username']})\n"
            else:
                text += "None"
            await event.reply(text)
            log_info("Listed admins", sender_id=event.sender_id, core_admins=len(core_admin_ids), plugin_admins=len(plugin_admins))

        @self.bot.on(events.NewMessage(pattern=r"^/lasterrors(?:\s+(\d+))?$"))
        async def lasterrors_cmd(event):
            num = 10
            m = event.pattern_match
            if m and m.group(1):
                try: num = int(m.group(1)); assert num > 0
                except: num = 10
            def doit():
                with _get_conn() as conn: cur = conn.cursor()
                cur.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (num,))
                return cur.fetchall()
            rows = await asyncio.get_running_loop().run_in_executor(None, doit)
            lines = []
            for r in rows:
                lines.append(f"[{r['created_at']}] {r['level']} {r['message']} ctx={r['context_json']}")
            await event.reply("Recent errors:\n" + ("\n".join(lines) if lines else "None"))
            log_info("Listed recent errors", sender_id=event.sender_id, error_count=len(lines))

        # --- Channel/media watcher ---
        @self.bot.on(events.NewMessage())
        async def monitor_channel(event):
            msg = event.message
            if not getattr(msg, "media", None): return
            chat = await event.get_chat()
            def is_mon():
                with _get_conn() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT 1 FROM channels WHERE chat_id=?", (chat.id,))
                    return cur.fetchone() is not None
            if not await asyncio.get_running_loop().run_in_executor(None, is_mon): return
            log_debug("File/media message detected for monitored channel", chat_id=chat.id, message_id=msg.id)
            await self._process_and_enqueue(msg, event)

    async def _process_and_enqueue(self, msg, event):
        """Deduplicate and queue file/download for worker task."""
        file_id = None
        file_unique = None
        filename = None
        if getattr(msg, "file", None):
            file_id = getattr(msg.file, "id", None)
            filename = getattr(msg.file, "name", None) or getattr(msg.file, "file_name", None)
            file_unique = f"{getattr(msg.file, 'id', None)}:{getattr(msg.file, 'size', None)}"
        if not file_unique:
            file_unique = f"msg:{msg.id}"
        if not filename:
            filename = f"{file_unique}.bin"
        def dedupe():
            with _get_conn() as conn:
                cur = conn.cursor()
                cur.execute("SELECT status, path FROM files WHERE file_unique=?", (file_unique,))
                r = cur.fetchone()
                return r
        existing = await asyncio.get_running_loop().run_in_executor(None, dedupe)
        if existing:
            log_info("File deduplicated: already downloaded", file_unique=file_unique, path=existing['path'])
            return await event.reply(f"File already processed/downloaded: {existing['path']}")
        await self._enqueue_db(file_id, file_unique, msg.chat_id, msg.id, filename)
        log_info("Queued file for download", file_unique=file_unique, filename=filename)
        await event.reply(f"Queued {filename} for download")