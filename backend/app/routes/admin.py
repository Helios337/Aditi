from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.auth import AuthUser, require_admin, utc_now_iso
from app.models import AdminQuestionSummary, ReviewUpdate
from app.services.supabase_client import get_supabase

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/questions", response_model=list[AdminQuestionSummary])
async def list_all_questions(
    _: Annotated[AuthUser, Depends(require_admin)],
) -> list[AdminQuestionSummary]:
    supabase = get_supabase()
    result = (
        supabase.table("questions")
        .select(
            "id, status, student_id, subject, topic, confidence_flag, verified, reviewed, final_answer, created_at"
        )
        .order("created_at", desc=True)
        .limit(200)
        .execute()
    )
    return [
        AdminQuestionSummary(
            id=UUID(row["id"]),
            status=row["status"],
            student_id=UUID(row["student_id"]) if row.get("student_id") else None,
            subject=row.get("subject"),
            topic=row.get("topic"),
            confidence_flag=row.get("confidence_flag", "needs_review"),
            verified=row.get("verified", False),
            reviewed=row.get("reviewed", False),
            final_answer=row.get("final_answer"),
            created_at=row.get("created_at"),
        )
        for row in result.data or []
    ]


@router.patch("/questions/{question_id}/review")
async def review_question(
    question_id: UUID,
    payload: ReviewUpdate,
    _: Annotated[AuthUser, Depends(require_admin)],
) -> dict:
    supabase = get_supabase()
    update_payload = {
        "reviewed": payload.reviewed,
        "reviewed_at": utc_now_iso() if payload.reviewed else None,
        "updated_at": utc_now_iso(),
    }
    if payload.final_answer is not None:
        update_payload["final_answer"] = payload.final_answer
    if payload.explanation is not None:
        update_payload["explanation"] = payload.explanation
    if payload.confidence_flag is not None:
        update_payload["confidence_flag"] = payload.confidence_flag

    result = supabase.table("questions").update(update_payload).eq("id", str(question_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"ok": True, "question_id": str(question_id)}
