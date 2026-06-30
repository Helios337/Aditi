from typing import Annotated
from datetime import UTC, datetime

from fastapi import Depends, Header, HTTPException, status

from app.config import get_settings
from app.services.supabase_client import get_supabase


class AuthUser:
    def __init__(self, user_id: str, email: str | None = None):
        self.user_id = user_id
        self.email = (email or "").lower()


def get_current_user(authorization: Annotated[str | None, Header()] = None) -> AuthUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    supabase = get_supabase()
    try:
        response = supabase.auth.get_user(token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user = response.user
    if not user or not user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return AuthUser(user_id=user.id, email=user.email)


def require_admin(user: Annotated[AuthUser, Depends(get_current_user)]) -> AuthUser:
    settings = get_settings()
    if user.email not in settings.admin_email_list:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()
