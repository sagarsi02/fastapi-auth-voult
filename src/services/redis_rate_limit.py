"""Redis-backed sliding-window limiter for login endpoint."""

from __future__ import annotations

import time
from uuid import uuid4

import redis.asyncio as redis
from redis.exceptions import RedisError

from src.config import settings
from src.logging import get_logger

logger = get_logger(__name__)


def _build_client() -> redis.Redis | None:
    if not settings.REDIS_URL:
        return None
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


class AsyncSlidingWindowRateLimiter:
    def __init__(self, redis_client: redis.Redis | None, limit: int, window_seconds: int):
        self.redis = redis_client
        self.limit = limit
        self.window = window_seconds

    async def is_allowed(self, key: str) -> bool:
        if self.redis is None or self.limit <= 0 or self.window <= 0:
            return True

        current_time = int(time.time() * 1000)
        window_start = current_time - (self.window * 1000)
        member = f"{current_time}-{uuid4().hex}"

        try:
            async with self.redis.pipeline(transaction=True) as pipe:
                (
                    pipe.zremrangebyscore(key, 0, window_start)
                    .zadd(key, {member: current_time})
                    .zcard(key)
                    .expire(key, self.window)
                )
                results = await pipe.execute()
                request_count = int(results[2])
                return request_count <= self.limit
        except RedisError:
            logger.exception("Redis rate limit check failed, allowing request.")
            return True


login_limiter = AsyncSlidingWindowRateLimiter(
    _build_client(),
    limit=settings.LOGIN_RATE_LIMIT_MAX_REQUESTS,
    window_seconds=settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS,
)

signup_user_limiter = AsyncSlidingWindowRateLimiter(
    _build_client(),
    limit=settings.SIGNUP_RATE_LIMIT_USER_MAX_REQUESTS,
    window_seconds=settings.SIGNUP_RATE_LIMIT_WINDOW_SECONDS,
)

signup_non_user_limiter = AsyncSlidingWindowRateLimiter(
    _build_client(),
    limit=settings.SIGNUP_RATE_LIMIT_NON_USER_MAX_REQUESTS,
    window_seconds=settings.SIGNUP_RATE_LIMIT_WINDOW_SECONDS,
)

user_details_limiter = AsyncSlidingWindowRateLimiter(
    _build_client(),
    limit=settings.USER_DETAILS_RATE_LIMIT_MAX_REQUESTS,
    window_seconds=settings.USER_DETAILS_RATE_LIMIT_WINDOW_SECONDS,
)
