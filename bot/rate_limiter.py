"""Rate limiting system for Xtension Bot"""

import time
import logging
from collections import defaultdict, deque
from typing import Dict, Deque, Tuple
from functools import wraps

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiting implementation with sliding window"""
    
    def __init__(self, 
                 commands_per_minute: int = 30,
                 commands_per_hour: int = 300,
                 burst_limit: int = 5,
                 burst_window: int = 10,
                 cooldown_time: int = 60):
        """
        Initialize rate limiter
        
        Args:
            commands_per_minute: Max commands per user per minute
            commands_per_hour: Max commands per user per hour
            burst_limit: Max commands in burst window
            burst_window: Seconds for burst detection
            cooldown_time: Seconds to wait after hitting limit
        """
        self.commands_per_minute = commands_per_minute
        self.commands_per_hour = commands_per_hour
        self.burst_limit = burst_limit
        self.burst_window = burst_window
        self.cooldown_time = cooldown_time
        
        # User tracking: user_id -> deque of timestamps
        self.user_commands: Dict[int, Deque[float]] = defaultdict(deque)
        self.user_cooldowns: Dict[int, float] = {}
        
        # Global stats
        self.total_limited = 0
        self.total_allowed = 0
    
    def is_rate_limited(self, user_id: int) -> Tuple[bool, str]:
        """
        Check if user is rate limited
        
        Returns:
            (is_limited, reason_message)
        """
        current_time = time.time()
        
        # Check if user is in cooldown
        if user_id in self.user_cooldowns:
            cooldown_end = self.user_cooldowns[user_id]
            if current_time < cooldown_end:
                remaining = int(cooldown_end - current_time)
                self.total_limited += 1
                return True, f"⏳ Rate limited. Please wait {remaining} seconds."
            else:
                del self.user_cooldowns[user_id]
        
        # Get user's command history
        user_history = self.user_commands[user_id]
        
        # Remove old commands (older than 1 hour)
        cutoff_hour = current_time - 3600
        while user_history and user_history[0] < cutoff_hour:
            user_history.popleft()
        
        # Check burst (too many commands in short time)
        recent_burst = [t for t in user_history if t > current_time - self.burst_window]
        if len(recent_burst) >= self.burst_limit:
            self.user_cooldowns[user_id] = current_time + self.cooldown_time
            self.total_limited += 1
            logger.warning(f"User {user_id} triggered burst limit: {len(recent_burst)} commands in {self.burst_window}s")
            return True, f"🚫 Too many commands too quickly! Please wait {self.cooldown_time} seconds."
        
        # Check minute limit
        recent_minute = [t for t in user_history if t > current_time - 60]
        if len(recent_minute) >= self.commands_per_minute:
            self.user_cooldowns[user_id] = current_time + 30  # 30 second cooldown
            self.total_limited += 1
            logger.warning(f"User {user_id} hit minute limit: {len(recent_minute)} commands")
            return True, f"⚠️ Rate limit reached ({self.commands_per_minute} commands/minute). Please wait 30 seconds."
        
        # Check hour limit
        if len(user_history) >= self.commands_per_hour:
            self.user_cooldowns[user_id] = current_time + 300  # 5 minute cooldown
            self.total_limited += 1
            logger.warning(f"User {user_id} hit hourly limit: {len(user_history)} commands")
            return True, f"📊 Hourly limit reached ({self.commands_per_hour} commands/hour). Please wait 5 minutes."
        
        # User is not rate limited - record this command
        user_history.append(current_time)
        self.total_allowed += 1
        return False, ""
    
    def reset_user(self, user_id: int):
        """Reset rate limiting for a specific user"""
        if user_id in self.user_commands:
            del self.user_commands[user_id]
        if user_id in self.user_cooldowns:
            del self.user_cooldowns[user_id]
        logger.info(f"Reset rate limits for user {user_id}")
    
    def get_user_stats(self, user_id: int) -> dict:
        """Get rate limit stats for a user"""
        current_time = time.time()
        user_history = self.user_commands.get(user_id, deque())
        
        # Clean old entries
        cutoff_hour = current_time - 3600
        user_history = deque([t for t in user_history if t > cutoff_hour])
        
        recent_minute = sum(1 for t in user_history if t > current_time - 60)
        recent_hour = len(user_history)
        
        in_cooldown = user_id in self.user_cooldowns and self.user_cooldowns[user_id] > current_time
        cooldown_remaining = 0
        if in_cooldown:
            cooldown_remaining = int(self.user_cooldowns[user_id] - current_time)
        
        return {
            "commands_last_minute": recent_minute,
            "commands_last_hour": recent_hour,
            "limit_per_minute": self.commands_per_minute,
            "limit_per_hour": self.commands_per_hour,
            "in_cooldown": in_cooldown,
            "cooldown_remaining": cooldown_remaining
        }
    
    def get_global_stats(self) -> dict:
        """Get global rate limiting statistics"""
        total_users = len(self.user_commands)
        users_in_cooldown = sum(1 for cd in self.user_cooldowns.values() if cd > time.time())
        
        return {
            "total_users_tracked": total_users,
            "users_in_cooldown": users_in_cooldown,
            "total_commands_allowed": self.total_allowed,
            "total_commands_limited": self.total_limited,
            "limit_percentage": round(self.total_limited / max(1, self.total_allowed + self.total_limited) * 100, 2)
        }

def rate_limit_decorator(limiter: RateLimiter, admin_ids: list = None):
    """Decorator to apply rate limiting to handlers"""
    def decorator(func):
        @wraps(func)
        async def wrapper(event):
            user_id = event.sender_id
            
            # Skip rate limiting for admins
            if admin_ids and user_id in admin_ids:
                return await func(event)
            
            # Check rate limit
            is_limited, message = limiter.is_rate_limited(user_id)
            if is_limited:
                await event.reply(message)
                return
            
            # Execute the handler
            return await func(event)
        return wrapper
    return decorator
