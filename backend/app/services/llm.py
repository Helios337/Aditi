import base64
import json
import re

from app.config import get_settings
from app.models import ProblemModel
from app.services.nvidia_client import nvidia_chat_completion
from app.services.llm_utils import (
    LLMRateLimitError,
    LLMServiceError,
    call_with_rate_limit_retry,
)

__all__ = [
    "LLMRateLimitError",
    "LLMServiceError",
    "extract_and_model_from_image",
    "generate_explanation",
    "model_problem",
]

SYSTEM_PROMPT = """You are ADITI, a JEE math assistant. Given OCR text from a student question image,
return ONLY valid JSON matching this schema:
{
  "subject": "math|physics|chemistry",
  "topic": "short topic label",
  "question_type": "solve_equation|differentiate|integrate|limit|simplify|other",
  "sympy_expression": "expression SymPy can parse, or null if not algebra/calculus",
  "sympy_variable": "x",
  "llm_answer": "proposed final answer string or null",
  "needs_review_reason": "reason manual review is needed, or null"
}

Rules:
- For algebra/calculus, provide a clean sympy_expression using ** for powers.
- Do NOT invent a numeric answer unless the problem is trivially readable from OCR.
- If OCR is garbled or the problem needs a diagram, set needs_review_reason.
- Use plain ASCII math where possible (e.g. x**2 + 3*x - 4 = 0).
"""

VISION_EXTRACT_PROMPT = """You are ADITI, a JEE math assistant. Read the student's question image carefully.

Return ONLY valid JSON matching this schema:
{
  "ocr_text": "full question text transcribed from the image",
  "ocr_confidence": 0.0,
  "subject": "math|physics|chemistry",
  "topic": "short topic label",
  "question_type": "solve_equation|differentiate|integrate|limit|simplify|other",
  "sympy_expression": "expression SymPy can parse, or null if not algebra/calculus",
  "sympy_variable": "x",
  "llm_answer": "proposed final answer string or null",
  "needs_review_reason": "reason manual review is needed, or null"
}

Rules:
- Transcribe all readable text and math from the image into ocr_text.
- Set ocr_confidence between 0 and 1 based on legibility (1.0 = fully clear).
- For algebra/calculus, provide a clean sympy_expression using ** for powers.
- Do NOT invent a numeric answer unless the problem is trivially readable.
- If the image is blurry, cropped, or needs a diagram you cannot read, set needs_review_reason.
- Use plain ASCII math where possible (e.g. x**2 + 3*x - 4 = 0).
"""


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


def _unconfigured_problem(reason: str) -> ProblemModel:
    return ProblemModel(
        subject="math",
        topic="unknown",
        question_type="other",
        sympy_expression=None,
        llm_answer=None,
        needs_review_reason=reason,
    )


def _image_data_url(image_bytes: bytes, content_type: str) -> str:
    mime_type = content_type if content_type.startswith("image/") else "image/jpeg"
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


async def extract_and_model_from_image(
    image_bytes: bytes,
    content_type: str = "image/jpeg",
) -> tuple[str, float, ProblemModel]:
    settings = get_settings()
    if not settings.nvidia_api_key:
        return "[NVIDIA API key not configured — set NVIDIA_API_KEY]", 0.0, _unconfigured_problem(
            "NVIDIA API key not configured"
        )

    data_url = _image_data_url(image_bytes, content_type)

    def _call() -> str:
        return nvidia_chat_completion(
            model=settings.nvidia_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_EXTRACT_PROMPT},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            json_mode=True,
            temperature=0.1,
        )

    raw = await call_with_rate_limit_retry(_call)
    data = _extract_json(raw)

    ocr_text = (data.get("ocr_text") or "").strip()
    if not ocr_text:
        ocr_text = "[Could not extract readable text from the image]"

    try:
        ocr_confidence = float(data.get("ocr_confidence", 0.5))
    except (TypeError, ValueError):
        ocr_confidence = 0.5
    ocr_confidence = max(0.0, min(1.0, ocr_confidence))

    problem_data = {key: data.get(key) for key in ProblemModel.model_fields if key in data}
    problem = ProblemModel.model_validate(problem_data)

    if ocr_confidence < 0.6 and not problem.needs_review_reason:
        problem.needs_review_reason = "Low OCR confidence"

    return ocr_text, ocr_confidence, problem


async def model_problem(ocr_text: str, ocr_confidence: float) -> ProblemModel:
    settings = get_settings()
    if not settings.nvidia_api_key:
        return _unconfigured_problem("NVIDIA API key not configured")

    user_prompt = f"""OCR confidence: {ocr_confidence:.2f}

OCR text:
{ocr_text}
"""

    def _call() -> str:
        return nvidia_chat_completion(
            model=settings.nvidia_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            json_mode=True,
            temperature=0.1,
        )

    raw = await call_with_rate_limit_retry(_call)
    data = _extract_json(raw)
    problem = ProblemModel.model_validate(data)

    if ocr_confidence < 0.6 and not problem.needs_review_reason:
        problem.needs_review_reason = "Low OCR confidence"

    return problem


async def generate_explanation(
    ocr_text: str,
    problem: ProblemModel,
    final_answer: str | None,
    solve_steps: list[str],
    confidence_flag: str,
) -> str:
    settings = get_settings()
    if not settings.nvidia_api_key:
        steps = "\n".join(f"- {step}" for step in solve_steps)
        return f"Verified answer: {final_answer}\n\nSteps:\n{steps}"

    prompt = f"""Write a clear JEE-style explanation for a student.

OCR question:
{ocr_text}

Topic: {problem.topic} ({problem.question_type})
Confidence flag: {confidence_flag}
Verified final answer: {final_answer or "None — do not state a bare final numeric answer"}

Solver steps:
{chr(10).join(solve_steps)}

Rules:
- Ground the explanation ONLY in the solver steps above.
- If confidence_flag is needs_review, explain the approach but do NOT present an unverified final answer as certain.
- If confidence_flag is unverified, clearly say the answer was not independently verified.
- Use short numbered steps suitable for exam prep.
"""

    def _call() -> str:
        return nvidia_chat_completion(
            model=settings.nvidia_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

    return (await call_with_rate_limit_retry(_call)).strip()
