import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


class LLMRateLimitError(Exception):
    """Raised when LLM API quota/rate limits are exceeded after retries."""


class LLMServiceError(Exception):
    """Raised for other LLM API failures with a short user-facing message."""


def is_rate_limit_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    return any(
        token in message
        for token in ("429", "quota", "rate limit", "rate_limit", "resource exhausted", "too many requests")
    )


def friendly_llm_error(exc: BaseException) -> str:
    message = str(exc).lower()
    if "401" in message or "invalid api key" in message or "authentication" in message:
        return (
            "NVIDIA API key is invalid or missing. Create a key at "
            "https://build.nvidia.com and set NVIDIA_API_KEY in .env, "
            "then restart the backend."
        )
    if is_rate_limit_error(exc):
        return (
            "NVIDIA API rate limit reached. Wait 1–2 minutes, then upload the question again."
        )
    if "api key" in message:
        return "NVIDIA API key is missing or invalid. Check NVIDIA_API_KEY in backend/.env."
    return "The AI service could not process this image right now. Please try again in a minute."


async def call_with_rate_limit_retry(
    fn: Callable[[], T | Awaitable[T]],
    *,
    max_attempts: int = 3,
    base_delay_seconds: float = 15.0,
) -> T:
    last_error: Exception | None = None

    for attempt in range(max_attempts):
        try:
            if asyncio.iscoroutinefunction(fn):
                return await fn()
            return await asyncio.to_thread(fn)
        except Exception as exc:
            last_error = exc
            if not is_rate_limit_error(exc) or attempt >= max_attempts - 1:
                break
            await asyncio.sleep(base_delay_seconds * (attempt + 1))

    if last_error and is_rate_limit_error(last_error):
        raise LLMRateLimitError(friendly_llm_error(last_error)) from last_error
    if last_error:
        raise LLMServiceError(friendly_llm_error(last_error)) from last_error
    raise LLMServiceError("LLM request failed.")
