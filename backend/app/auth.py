import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request

from app.config import get_settings
from app.services.supabase_client import get_supabase

logger = logging.getLogger("aditi.auth")


class AuthUser:
    def __init__(self, user_id: str, email: str | None = None):
        self.user_id = user_id
        self.email = (email or "").lower()


def get_current_user(request: Request) -> AuthUser:
    authorization = request.headers.get("authorization") or ""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing bearer token",
        )

    token = authorization.removeprefix("Bearer ").strip()
    supabase = get_supabase()
    try:
        response = supabase.auth.get_user(token)
    except Exception as exc:
        logger.debug("Supabase auth.get_user failed: %s", exc)
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        ) from exc

    user = response.user
    if not user or not getattr(user, "id", None):
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    return AuthUser(user_id=user.id, email=getattr(user, "email", None))


def require_admin(user: Annotated[AuthUser, Depends(get_current_user)]) -> AuthUser:
    settings = get_settings()
    admin_set = {e.strip().lower() for e in settings.admin_email_list}
    if (user.email or "") not in admin_set:
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )
    return user


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()
