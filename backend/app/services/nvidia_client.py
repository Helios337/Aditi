"""NVIDIA build.nvidia.com chat completions client (model: minimaxai/minimax-m3).

MiniMax-M3 is multimodal: ``messages`` may contain text parts and
``image_url`` / ``video_url`` parts (public URL or base64 data URI), matching
the official NVIDIA snippet.

The endpoint is OpenAI-compatible, so ``response_format`` =
``{"type": "json_object"}`` is supported for structured extraction.
"""

import httpx

from app.config import get_settings

NVIDIA_CHAT_URL = "https://integrate.api.nvidia.com/v1/chat/completions"


def nvidia_chat_completion(
    *,
    model: str,
    messages: list[dict],
    temperature: float = 0.6,
    top_p: float = 0.95,
    max_tokens: int = 8192,
    json_mode: bool = False,
) -> str:
    settings = get_settings()
    api_key = settings.nvidia_api_key
    if not api_key:
        raise ValueError("NVIDIA_API_KEY is not configured")

    payload: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    response = httpx.post(
        settings.nvidia_base_url or NVIDIA_CHAT_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120.0,
    )

    if response.status_code >= 400:
        detail = response.text[:500]
        raise RuntimeError(f"NVIDIA API error {response.status_code}: {detail}")

    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        # NVIDIA can return an empty ``choices`` array for image inputs that are
        # unreadable or filtered. Surface it as a service error so the pipeline
        # reports it cleanly instead of an opaque IndexError.
        raise RuntimeError(
            "NVIDIA API returned no choices (image content may have been filtered or undecodable)."
        )
    content = choices[0].get("message", {}).get("content")
    if not content:
        raise RuntimeError("NVIDIA API returned an empty response")
    return content
