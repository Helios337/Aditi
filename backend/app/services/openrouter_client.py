"""OpenRouter chat completions client (OpenAI-compatible endpoint).

Uses https://openrouter.ai/api/v1/chat/completions with the standard
OpenAI-style request/response shape. Vision models accept ``messages`` with
text parts and ``image_url`` parts (public URL or base64 data URI).

By default we request ``response_format`` = ``{"type": "json_object"}`` only
for models known to support it. Callers in this app gate JSON mode so free
models without structured-output support fall back to prompt-only JSON.
"""

import httpx

from app.config import get_settings

OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

# Models that reliably support strict ``json_object`` structured output.
_JSON_MODE_MODELS = frozenset(
    {
        "meta-llama/llama-3.3-70b-instruct:free",
        "openai/gpt-oss-120b:free",
        "qwen/qwen2.5-vl-72b-instruct:free",
    }
)


def _supports_json_mode(model: str) -> bool:
    return model in _JSON_MODE_MODELS


def openrouter_chat_completion(
    *,
    model: str,
    messages: list[dict],
    temperature: float = 0.6,
    top_p: float = 0.95,
    max_tokens: int = 8192,
    json_mode: bool = False,
) -> str:
    settings = get_settings()
    api_key = settings.openrouter_api_key
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not configured")

    payload: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if json_mode and _supports_json_mode(model):
        payload["response_format"] = {"type": "json_object"}

    response = httpx.post(
        settings.openrouter_base_url or OPENROUTER_CHAT_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": settings.openrouter_site_url or OPENROUTER_CHAT_URL,
            "X-Title": settings.openrouter_site_name or "Aditi",
        },
        json=payload,
        timeout=120.0,
    )

    if response.status_code >= 400:
        detail = response.text[:500]
        raise RuntimeError(f"OpenRouter API error {response.status_code}: {detail}")

    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        # OpenRouter can return an empty ``choices`` array for image inputs that
        # are unreadable or filtered. Surface it as a service error so the
        # pipeline reports it cleanly instead of an opaque IndexError.
        raise RuntimeError(
            "OpenRouter API returned no choices (image content may have been filtered or undecodable)."
        )
    content = choices[0].get("message", {}).get("content")
    if not content:
        raise RuntimeError("OpenRouter API returned an empty response")
    return content
