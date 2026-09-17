import time
import pytest
from app.security.rate_limiter import RateLimiter

def test_rate_limiter_allows_under_limit():
    limiter = RateLimiter(max_per_minute=5)
    for _ in range(4):
        assert limiter.check("session_1") is True
        
def test_rate_limiter_blocks_over_limit():
    limiter = RateLimiter(max_per_minute=2)
    assert limiter.check("session_2") is True
    assert limiter.check("session_2") is True
    # The 3rd request should be blocked
    assert limiter.check("session_2") is False

def test_rate_limiter_isolates_sessions():
    limiter = RateLimiter(max_per_minute=1)
    assert limiter.check("user_a") is True
    assert limiter.check("user_a") is False # Blocked
    
    # user_b should not be affected by user_a
    assert limiter.check("user_b") is True 
