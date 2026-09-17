import time
from collections import defaultdict

class RateLimiter:
    """Sliding window rate limiter ?" tracks calls per session per minute."""

    def __init__(self, max_per_minute: int = 15):
        self.max_per_minute = max_per_minute
        # session_id -> list of timestamps
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._cleanup_counter = 0

    def check(self, session_id: str = "default") -> bool:
        """Returns True if the request is allowed, False if rate limited."""
        now = time.time()
        
        # Periodic O(N) cleanup to prevent memory leaks from idle IPs
        self._cleanup_counter += 1
        if self._cleanup_counter > 100:
            self._cleanup_counter = 0
            idle_keys = [k for k, w in self._windows.items() if not w or (now - w[-1] >= 60)]
            for k in idle_keys:
                del self._windows[k]
                
        window = self._windows[session_id]

        # drop entries older than 60 seconds
        window[:] = [t for t in window if now - t < 60]

        if len(window) >= self.max_per_minute:
            return False

        window.append(now)
        return True

# Singleton shared instance
rate_limiter = RateLimiter()
