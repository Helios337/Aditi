from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status

from app.auth import AuthUser, get_current_user
from app.config import get_settings
from app.models import QuestionCreateResponse, QuestionResponse
from app.services.pipeline import process_question
from app.services.supabase_client import get_supabase

router = APIRouter(prefix="/questions", tags=["questions"])


def _signed_image_url(storage_path: str) -> str:
    settings = get_settings()
    supabase = get_supabase()
    return supabase.storage.from_(settings.storage_bucket).create_signed_url(storage_path, 3600)["signedURL"]


def _row_to_response(row: dict) -> QuestionResponse:
    image_url = row.get("image_url")
    if image_url and not image_url.startswith("http"):
        try:
            image_url = _signed_image_url(image_url)
        except Exception:
            pass

    return QuestionResponse(
        id=UUID(row["id"]),
        status=row["status"],
        image_url=image_url,
        ocr_text=row.get("ocr_text"),
        ocr_confidence=row.get("ocr_confidence"),
        subject=row.get("subject"),
        topic=row.get("topic"),
        question_type=row.get("question_type"),
        solver_used=row.get("solver_used"),
        verified=row.get("verified", False),
        confidence_flag=row.get("confidence_flag", "needs_review"),
        final_answer=row.get("final_answer"),
        explanation=row.get("explanation"),
        error_message=row.get("error_message"),
        reviewed=row.get("reviewed", False),
        reviewed_at=row.get("reviewed_at"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


@router.post("", response_model=QuestionCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_question(
    background_tasks: BackgroundTasks,
    user: Annotated[AuthUser, Depends(get_current_user)],
    image: UploadFile = File(...),
) -> QuestionCreateResponse:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Upload must be an image")

    image_bytes = await image.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty image upload")
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be under 10MB")

    question_id = uuid4()
    extension = (image.filename or "upload.jpg").split(".")[-1].lower()
    if extension not in {"jpg", "jpeg", "png", "webp"}:
        extension = "jpg"
    storage_path = f"{user.user_id}/{question_id}.{extension}"

    settings = get_settings()
    supabase = get_supabase()
    supabase.storage.from_(settings.storage_bucket).upload(
        storage_path,
        image_bytes,
        {"content-type": image.content_type, "upsert": "true"},
    )

    supabase.table("questions").insert(
        {
            "id": str(question_id),
            "student_id": user.user_id,
            "image_url": storage_path,
            "status": "pending",
            "confidence_flag": "needs_review",
        }
    ).execute()

    background_tasks.add_task(process_question, question_id, image_bytes, image.content_type)
    return QuestionCreateResponse(id=question_id, status="pending")


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: UUID,
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> QuestionResponse:
    supabase = get_supabase()
    result = (
        supabase.table("questions")
        .select("*")
        .eq("id", str(question_id))
        .eq("student_id", user.user_id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Question not found")
    return _row_to_response(result.data)


@router.get("", response_model=list[QuestionResponse])
async def list_my_questions(
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> list[QuestionResponse]:
    supabase = get_supabase()
    result = (
        supabase.table("questions")
        .select("*")
        .eq("student_id", user.user_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return [_row_to_response(row) for row in result.data or []]
