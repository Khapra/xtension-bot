# Xtension Bot: Plugins Directory

This folder is **empty in all release builds and Docker images**.  
To use plugins, download `.py` files you want from the [official GitHub repository](https://github.com/Khapra/xtension-bot/tree/main/plugins) and put them here.

## 🛠️ How to Add Plugins

1. Browse available plugins at  
   https://github.com/Khapra/xtension-bot/tree/main/plugins

2. Download the `.py` files you wish to use.

3. Place those files inside this directory.

- **For Docker Compose users:**  
  Mount your plugin directory into the container at `/app/plugins`:
  ```
  - ./plugins:/app/plugins
  ```

- **When running the bot, all `.py` files in this folder will be loaded automatically.**

---

Official plugin repository: https://github.com/Khapra/xtension-bot/tree/main/plugins

*This README stays in the release to help all users find and add plugins themselves.*
