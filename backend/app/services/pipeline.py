import traceback
from uuid import UUID

from app.auth import utc_now_iso
from app.services.llm import generate_explanation, model_problem
from app.services.ocr import mathpix_ocr
from app.services.solver import solve_problem
from app.services.supabase_client import get_supabase


def _update_question(question_id: UUID, payload: dict) -> None:
    supabase = get_supabase()
    payload["updated_at"] = utc_now_iso()
    supabase.table("questions").update(payload).eq("id", str(question_id)).execute()


async def process_question(question_id: UUID, image_bytes: bytes, content_type: str) -> None:
    try:
        _update_question(question_id, {"status": "processing"})

        ocr_text, ocr_confidence = await mathpix_ocr(image_bytes, content_type)
        _update_question(
            question_id,
            {"ocr_text": ocr_text, "ocr_confidence": ocr_confidence},
        )

        problem = await model_problem(ocr_text, ocr_confidence)
        solve_result = solve_problem(problem)

        confidence_flag = solve_result.confidence_flag
        if problem.needs_review_reason and confidence_flag == "verified":
            confidence_flag = "needs_review"

        final_answer = solve_result.final_answer
        if confidence_flag == "needs_review":
            final_answer = None

        explanation = await generate_explanation(
            ocr_text=ocr_text,
            problem=problem,
            final_answer=solve_result.final_answer,
            solve_steps=solve_result.solve_steps,
            confidence_flag=confidence_flag,
        )

        _update_question(
            question_id,
            {
                "status": "completed",
                "subject": problem.subject,
                "topic": problem.topic,
                "question_type": problem.question_type,
                "solver_used": solve_result.solver_used,
                "verified": solve_result.verified,
                "confidence_flag": confidence_flag,
                "final_answer": final_answer,
                "explanation": explanation,
            },
        )
    except Exception as exc:
        _update_question(
            question_id,
            {
                "status": "failed",
                "error_message": str(exc),
                "confidence_flag": "needs_review",
            },
        )
        traceback.print_exc()
