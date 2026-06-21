import json
import re

import google.generativeai as genai

from app.config import get_settings
from app.models import ProblemModel


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


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


async def model_problem(ocr_text: str, ocr_confidence: float) -> ProblemModel:
    settings = get_settings()
    if not settings.gemini_api_key:
        return ProblemModel(
            subject="math",
            topic="unknown",
            question_type="other",
            sympy_expression=None,
            llm_answer=None,
            needs_review_reason="Gemini API key not configured",
        )

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

    user_prompt = f"""OCR confidence: {ocr_confidence:.2f}

OCR text:
{ocr_text}
"""
    response = model.generate_content(
        [SYSTEM_PROMPT, user_prompt],
        generation_config={"temperature": 0.1, "response_mime_type": "application/json"},
    )
    data = _extract_json(response.text or "{}")
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
    if not settings.gemini_api_key:
        steps = "\n".join(f"- {step}" for step in solve_steps)
        return f"Verified answer: {final_answer}\n\nSteps:\n{steps}"

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

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
    response = model.generate_content(prompt, generation_config={"temperature": 0.3})
    return (response.text or "").strip()
