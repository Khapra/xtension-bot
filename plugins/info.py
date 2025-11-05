"""System and bot information plugin - v1.1.0"""

from telethon import events
from datetime import datetime
import platform
import psutil
import os

class TelethonPlugin:
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.now()
        self.commands_count = 0
        self.commands = {
            "/info": "Show bot system information",
            "/sysinfo": "Detailed system information",
            "/botinfo": "Bot-specific information"
        }
        
    def register_handlers(self):
        @self.bot.on(events.NewMessage(pattern='/info'))
        async def info(event):
            self.commands_count += 1
            uptime = datetime.now() - self.start_time
            memory = psutil.virtual_memory()
            
            info_text = f"""🤖 **Bot Information**

**Bot:** @{self.bot.me.username}
**Version:** {self.bot.version}
**Uptime:** {str(uptime).split('.')[0]}
**Commands processed:** {self.commands_count}

**System:**
• Python: {platform.python_version()}
• OS: {platform.system()} {platform.release()}
• Architecture: {platform.machine()}
• Memory: {memory.percent:.1f}% used
• CPU: {psutil.cpu_percent()}%
"""
            await event.reply(info_text, parse_mode='md')
        
        @self.bot.on(events.NewMessage(pattern='/sysinfo'))
        async def sysinfo(event):
            self.commands_count += 1
            
            # Get system information
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            
            sys_text = f"""💻 **System Information**

**Platform:** {platform.platform()}
**Processor:** {platform.processor() or 'Unknown'}
**Python:** {platform.python_version()}
**Boot Time:** {boot_time.strftime('%Y-%m-%d %H:%M:%S')}

**Memory:**
• Total: {memory.total // (1024**3):.1f} GB
• Used: {memory.used // (1024**3):.1f} GB ({memory.percent}%)
• Available: {memory.available // (1024**3):.1f} GB

**Disk:**
• Total: {disk.total // (1024**3):.1f} GB
• Used: {disk.used // (1024**3):.1f} GB ({disk.percent}%)
• Free: {disk.free // (1024**3):.1f} GB

**CPU:**
• Cores: {psutil.cpu_count()} (Physical: {psutil.cpu_count(logical=False)})
• Usage: {psutil.cpu_percent(interval=1)}%
"""
            await event.reply(sys_text, parse_mode='md')
        
        @self.bot.on(events.NewMessage(pattern='/botinfo'))
        async def botinfo(event):
            self.commands_count += 1
            
            plugin_list = ", ".join(sorted(self.bot.plugins.keys()))
            total_cmds = sum(len(p.commands) for p in self.bot.plugins.values() if hasattr(p, 'commands'))
            
            bot_text = f"""🤖 **Bot Details**

**Name:** @{self.bot.me.username}
**ID:** `{self.bot.me.id}`
**Version:** {self.bot.version}

**Plugins:** {len(self.bot.plugins)} loaded
• {plugin_list}

**Total Plugin Commands:** {total_cmds}
**Session Type:** {self.bot.config.session_type}
**Plugin Directory:** {self.bot.config.plugin_dir}
"""
            await event.reply(bot_text, parse_mode='md')
