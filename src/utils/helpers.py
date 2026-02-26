"""Helpers for common route concerns like normalization and rate limiting."""

from fastapi import HTTPException, Request, status

from src.config import settings
from src.services.redis_rate_limit import (
    login_limiter,
    signup_non_user_limiter,
    signup_user_limiter,
    user_details_limiter,
)

def normalize_email(email: str) -> str:
    """Return normalized email for consistent lookup and storage."""
    return email.strip().lower()


def get_client_ip(request: Request) -> str:
    """Return client IP, preferring X-Forwarded-For when present."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


async def enforce_login_rate_limit(request: Request, identifier: str) -> None:
    """Raise HTTP 429 when login attempts exceed configured limits."""
    ip_address = get_client_ip(request)
    user_ip_key = f"login:user-ip:{identifier}:{ip_address}"

    if not await login_limiter.is_allowed(user_ip_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
            headers={"Retry-After": str(settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS)},
        )


async def enforce_signup_rate_limit(request: Request, role: str = "user") -> None:
    """
    Enforce signup rate limit by IP:
    - role 'user' -> stricter limit
    - other roles -> relaxed limit
    """
    normalized_role = (role or "user").strip().lower()
    ip_address = get_client_ip(request)
    signup_ip_key = f"signup:role-ip:{normalized_role}:{ip_address}"

    limiter = signup_user_limiter if normalized_role == "user" else signup_non_user_limiter
    if not await limiter.is_allowed(signup_ip_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many signup attempts. Try again later.",
            headers={"Retry-After": str(settings.SIGNUP_RATE_LIMIT_WINDOW_SECONDS)},
        )


async def enforce_user_details_rate_limit(request: Request, user_id: str) -> None:
    """Raise HTTP 429 when /me is called too frequently by user or IP."""
    ip_address = get_client_ip(request)
    user_key = f"user-details:user:{user_id}"
    ip_key = f"user-details:ip:{ip_address}"

    user_allowed = await user_details_limiter.is_allowed(user_key)
    ip_allowed = await user_details_limiter.is_allowed(ip_key)
    if not user_allowed or not ip_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many profile requests. Try again later.",
            headers={"Retry-After": str(settings.USER_DETAILS_RATE_LIMIT_WINDOW_SECONDS)},
        )
