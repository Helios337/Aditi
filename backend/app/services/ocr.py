import base64
import re

import httpx

from app.config import get_settings


LATEX_TO_SYMPY = {
    r"\\frac": " ",
    r"\\sqrt": "sqrt",
    r"\\pi": "pi",
    r"\\infty": "oo",
    r"\\cdot": "*",
    r"\\times": "*",
    r"\\left": "",
    r"\\right": "",
    r"\\,": "",
    r"\\;": "",
    r"\\!": "",
    r"\\text": "",
    r"\\mathrm": "",
}


def normalize_for_sympy(expression: str) -> str:
    text = expression.strip()
    text = text.replace("$", "")
    text = text.replace("^", "**")
    for latex, replacement in LATEX_TO_SYMPY.items():
        text = re.sub(latex, replacement, text)
    text = re.sub(r"\{([^}]*)\}", r"(\1)", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


async def mathpix_ocr(image_bytes: bytes, content_type: str = "image/jpeg") -> tuple[str, float]:
    settings = get_settings()
    if not settings.mathpix_app_id or not settings.mathpix_app_key:
        return "[Mathpix not configured — set MATHPIX_APP_ID and MATHPIX_APP_KEY]", 0.0

    payload = {
        "src": f"data:{content_type};base64,{base64.b64encode(image_bytes).decode()}",
        "formats": ["text", "latex_styled"],
        "data_options": {"include_asciimath": True, "include_latex": True},
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.mathpix.com/v3/text",
            json=payload,
            headers={
                "app_id": settings.mathpix_app_id,
                "app_key": settings.mathpix_app_key,
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        data = response.json()

    text = data.get("text") or data.get("latex_styled") or ""
    confidence = float(data.get("confidence", data.get("confidence_rate", 0.5)) or 0.5)
    if isinstance(confidence, (int, float)) and confidence > 1:
        confidence = confidence / 100.0
    return text.strip(), max(0.0, min(1.0, confidence))
