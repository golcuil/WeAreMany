import os


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


API_VERSION = os.getenv("API_VERSION", "0.1.0")
AUTH_TOKEN_PREFIX = os.getenv("AUTH_TOKEN_PREFIX", "dev_")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

MAX_BODY_BYTES = _get_int("MAX_BODY_BYTES", 8 * 1024)

READ_RATE_LIMIT = _get_int("READ_RATE_LIMIT", 60)
READ_RATE_WINDOW_SECONDS = _get_int("READ_RATE_WINDOW_SECONDS", 60)
WRITE_RATE_LIMIT = _get_int("WRITE_RATE_LIMIT", 20)
WRITE_RATE_WINDOW_SECONDS = _get_int("WRITE_RATE_WINDOW_SECONDS", 60)

LEAK_ATTEMPT_LIMIT = _get_int("LEAK_ATTEMPT_LIMIT", 3)
LEAK_ATTEMPT_WINDOW_SECONDS = _get_int("LEAK_ATTEMPT_WINDOW_SECONDS", 300)

MATCH_MIN_POOL_K = _get_int("MATCH_MIN_POOL_K", 3)
MATCH_COOLDOWN_SECONDS = _get_int("MATCH_COOLDOWN_SECONDS", 3600)
MATCH_SAMPLE_LIMIT = _get_int("MATCH_SAMPLE_LIMIT", 50)
ELIGIBLE_RECENCY_HOURS = _get_int("ELIGIBLE_RECENCY_HOURS", 72)
