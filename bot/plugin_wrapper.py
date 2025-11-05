"""Plugin wrapper utilities for automatic command logging"""

import logging
from functools import wraps

logger = logging.getLogger(__name__)

def create_logged_handler(handler, plugin_name, bot):
    """Wrap a plugin handler with logging"""
    @wraps(handler)
    async def logged_handler(event):
        if logger.isEnabledFor(logging.DEBUG):
            try:
                sender = await event.get_sender()
                sender_info = f"{sender.first_name} (@{sender.username or 'no_username'}, ID: {sender.id})"
                
                if hasattr(event, 'pattern_match') and event.pattern_match:
                    command = event.pattern_match.string
                    logger.debug(f"[PLUGIN:{plugin_name}] Command: '{command}' from {sender_info}")
                else:
                    logger.debug(f"[PLUGIN:{plugin_name}] Event from {sender_info}")
            except Exception as e:
                logger.debug(f"[PLUGIN:{plugin_name}] Could not log event details: {e}")
        
        # Increment command counter if available
        if hasattr(bot, 'commands_processed'):
            bot.commands_processed += 1
        
        # Call original handler
        try:
            result = await handler(event)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"[PLUGIN:{plugin_name}] Success")
            return result
        except Exception as e:
            logger.error(f"[PLUGIN:{plugin_name}] Error: {e}")
            if logger.isEnabledFor(logging.DEBUG):
                import traceback
                logger.debug(traceback.format_exc())
            raise
    
    return logged_handler
