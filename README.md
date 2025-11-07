# 🚀 Xtension Bot v1.3.1 – Fast, Modular Telegram Bot Framework

Run in seconds with Docker.  
Add features with plugins you choose—no bloat, no surprises!

---

## 🚦 Quick Start with Docker

```bash
docker run -d \
  -e BOT_TOKEN="YOUR_BOT_TOKEN" \
  -e LOG_LEVEL="INFO" \
  --name xtension-bot \
  -v $(pwd)/plugins:/app/plugins \
  khapra/xtension-bot:latest
```

**Plugins not included:**  
Create a `plugins` directory beside `docker-compose.yml` or where you run `docker run`.  
Download only the `.py` plugin files you want from  
https://github.com/Khapra/xtension-bot/tree/main/plugins  
and put them in your `plugins` folder before you run the bot!

---

## 🐳 Docker Compose Example

```yaml
version: '3.8'
services:
  xtension-bot:
    image: khapra/xtension-bot:latest
    environment:
      BOT_TOKEN: YOUR_BOT_TOKEN_HERE
      ADMIN_IDS: YOUR_TELEGRAM_ID  # Optional
      LOG_LEVEL: INFO
      PUID: 1000   # Optional, see advanced permissions
      PGID: 1000
    volumes:
      - ./plugins:/app/plugins
      - ./sessions:/app/sessions
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```
- **Place the `.py` plugins you want in your `./plugins/` — the container loads them at startup.**
- All data will persist in the mounted directories.

---

## ⚡ What's New in v1.3.1?

- Enhanced release pipeline with secure, automated PR-based versioning.
- Faster startup and hot-reload system for plugins.
- Improved environment variable management and runtime warnings.
- [List other new features, major fixes, or improvements]

---

## ⚡ Why Xtension Bot?

- **No bundled plugins:** Choose only what you want.
- **Safe to update:** No user code is ever overwritten.
- **Hot-reload plugins:** Drop new files in and go!
- **Production-ready:** Modern, MIT-licensed.

---

## 🌱 Manual Setup

1. Clone:
    ```bash
    git clone https://github.com/Khapra/xtension-bot.git
    cd xtension-bot
    ```
2. Setup venv:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3. Copy your plugins from GitHub into `plugins/`
4. Create `.env` (see Environment Variables below)
5. Start:
    ```bash
    python -m bot
    ```

---

## ⚙️ Environment Variables

| Variable               | Description                        | Required / Default |
|------------------------|------------------------------------|--------------------|
| BOT_TOKEN              | Telegram Bot Token                 | **Required**       |
| ADMIN_IDS              | Comma-separated admin IDs          | Optional           |
| LOG_LEVEL              | Logging level (INFO/DEBUG)         | INFO               |
| RATE_LIMIT_PER_MINUTE  | Commands per minute                | 30                 |
| RATE_LIMIT_PER_HOUR    | Commands per hour                  | 300                |
| PUID                   | UID inside container               | 1000               |
| PGID                   | GID inside container               | 1000               |

---

## 🔌 Plugins

- Browse official plugins:  
  https://github.com/Khapra/xtension-bot/tree/main/plugins
- Place `.py` files in your `plugins` directory (mapped to `/app/plugins` in Docker).
- Remove a `.py` file to instantly disable that plugin.

---

## 🛡️ Rate Limiting

- Prevent spam with minute/hour/burst limits.
- Admins are always exempt.
- All limits are easily tuned via env or `.env`.

---

## 🛠️ Logs & Management

- View logs:
    ```bash
    docker logs -f xtension-bot
    ```
- Update:
    ```bash
    docker pull khapra/xtension-bot:latest
    docker restart xtension-bot
    ```
- All persistent data is in `./sessions`, `./data`, `./logs`.

---

## ⚠️ Disclaimer

**This bot uses [Telegram Demo API keys](https://my.telegram.org/auth) by default (149344, '1c760da900d9a3e28b17c16410680dae') for demo/testing only.  
For production, [register your own API ID/Hash](https://my.telegram.org) and set them in your `.env`.**

---

## 📈 Version

- **Current version:** [`v1.3.1`](./VERSION)
- **Release notes:** https://github.com/Khapra/xtension-bot/releases

---

## 💡 Enjoy!  
Questions? [Open an Issue](https://github.com/Khapra/xtension-bot/issues) — Feedback & PRs welcome!

**Author:** [Khapra](https://github.com/Khapra)  
**License:** MIT  
**Docker Hub:** [khapra/xtension-bot](https://hub.docker.com/r/khapra/xtension-bot)

<!-- Docker Hub: https://hub.docker.com/r/khapra/xtension-bot -->