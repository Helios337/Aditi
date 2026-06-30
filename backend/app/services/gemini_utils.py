import asyncio
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class GeminiRateLimitError(Exception):
    """Raised when Gemini API quota/rate limits are exceeded after retries."""


class GeminiServiceError(Exception):
    """Raised for other Gemini API failures with a short user-facing message."""


def is_rate_limit_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    return any(
        token in message
        for token in ("429", "quota", "rate limit", "rate_limit", "resource exhausted")
    )


def is_per_minute_quota_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    return is_rate_limit_error(exc) and any(
        token in message for token in ("per minute", "per-minute", "request limit per minute")
    )


def friendly_gemini_error(exc: BaseException) -> str:
    if is_rate_limit_error(exc):
        return (
            "Gemini API rate limit reached. Wait 1–2 minutes, then upload the question again. "
            "Free tier allows about 15 requests/minute."
        )
    if "api key" in str(exc).lower():
        return "Gemini API key is missing or invalid. Check GEMINI_API_KEY in backend/.env."
    return "Gemini could not process this image right now. Please try again in a minute."


async def call_with_rate_limit_retry(
    fn: Callable[[], T],
    *,
    max_attempts: int = 2,
    base_delay_seconds: float = 10.0,
) -> T:
    last_error: Exception | None = None

    for attempt in range(max_attempts):
        try:
            return await asyncio.to_thread(fn)
        except Exception as exc:
            last_error = exc
            if is_per_minute_quota_error(exc):
                break
            if not is_rate_limit_error(exc) or attempt >= max_attempts - 1:
                break
            await asyncio.sleep(base_delay_seconds * (attempt + 1))

    if last_error and is_rate_limit_error(last_error):
        raise GeminiRateLimitError(friendly_gemini_error(last_error)) from last_error
    if last_error:
        raise GeminiServiceError(friendly_gemini_error(last_error)) from last_error
    raise GeminiServiceError("Gemini request failed.")
