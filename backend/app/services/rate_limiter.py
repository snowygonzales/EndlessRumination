"""Redis-backed rate limiting for takes and problems per day."""

from datetime import datetime, timezone

import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()

_redis: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


def _day_key(prefix: str, user_id: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{prefix}:{user_id}:{today}"


async def check_rate_limit(
    user_id: str, is_pro: bool, resource: str = "problems"
) -> dict:
    """Check if user is within rate limits.

    Args:
        user_id: UUID string
        is_pro: whether user has pro subscription
        resource: "problems" or "takes"

    Returns:
        {"allowed": bool, "used": int, "limit": int, "remaining": int}
    """
    r = await get_redis()
    key = _day_key(resource, user_id)

    if resource == "problems":
        limit = settings.pro_problems_per_day if is_pro else settings.free_problems_per_day
    else:
        limit = 999999 if is_pro else settings.free_takes_per_day

    current = await r.get(key)
    used = int(current) if current else 0

    return {
        "allowed": used < limit,
        "used": used,
        "limit": limit,
        "remaining": max(0, limit - used),
    }


async def increment_usage(user_id: str, resource: str = "problems") -> int:
    """Increment usage counter. Returns new count. Key expires at end of day."""
    r = await get_redis()
    key = _day_key(resource, user_id)

    count = await r.incr(key)
    # Set TTL to expire at end of UTC day (max 24h)
    if count == 1:
        await r.expire(key, 86400)

    return count


async def get_usage(user_id: str, resource: str = "problems") -> int:
    """Get current usage count."""
    r = await get_redis()
    key = _day_key(resource, user_id)
    current = await r.get(key)
    return int(current) if current else 0
