import time
from collections import defaultdict

class RateLimiter:
    """Sliding window rate limiter ?" tracks calls per session per minute."""

    def __init__(self, max_per_minute: int = 15):
        self.max_per_minute = max_per_minute
        # session_id -> list of timestamps
        self._windows: dict[str, list[float]] = defaultdict(list)

    def check(self, session_id: str = "default") -> bool:
        """Returns True if the request is allowed, False if rate limited."""
        now = time.time()
        window = self._windows[session_id]

        # drop entries older than 60 seconds
        window[:] = [t for t in window if now - t < 60]

        if len(window) >= self.max_per_minute:
            return False

        window.append(now)
        return True

# Singleton shared instance
rate_limiter = RateLimiter()
