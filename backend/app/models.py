from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


QuestionStatus = Literal["pending", "processing", "completed", "failed"]
ConfidenceFlag = Literal["verified", "unverified", "needs_review"]
SolverUsed = Literal["sympy", "wolfram", "llm_only"]


class QuestionCreateResponse(BaseModel):
    id: UUID
    status: QuestionStatus


class QuestionResponse(BaseModel):
    id: UUID
    status: QuestionStatus
    image_url: str | None = None
    ocr_text: str | None = None
    ocr_confidence: float | None = None
    subject: str | None = None
    topic: str | None = None
    question_type: str | None = None
    solver_used: SolverUsed | None = None
    verified: bool = False
    confidence_flag: ConfidenceFlag = "needs_review"
    final_answer: str | None = None
    explanation: str | None = None
    error_message: str | None = None
    reviewed: bool = False
    reviewed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AdminQuestionSummary(BaseModel):
    id: UUID
    status: QuestionStatus
    student_id: UUID | None = None
    subject: str | None = None
    topic: str | None = None
    confidence_flag: ConfidenceFlag
    verified: bool
    reviewed: bool
    final_answer: str | None = None
    created_at: datetime | None = None


class ReviewUpdate(BaseModel):
    reviewed: bool = True
    final_answer: str | None = None
    explanation: str | None = None
    confidence_flag: ConfidenceFlag | None = None


class ProblemModel(BaseModel):
    subject: str = Field(description="math, physics, or chemistry")
    topic: str = Field(description="e.g. calculus, algebra, kinematics")
    question_type: str = Field(description="e.g. solve_equation, differentiate, integrate")
    sympy_expression: str | None = Field(
        default=None,
        description="LaTeX or plain expression SymPy can parse, or null if not applicable",
    )
    sympy_variable: str = Field(default="x", description="Primary variable to solve for")
    llm_answer: str | None = Field(
        default=None,
        description="LLM's proposed answer when SymPy cannot handle the problem",
    )
    needs_review_reason: str | None = Field(
        default=None,
        description="Why manual review may be needed",
    )


class SolveResult(BaseModel):
    solver_used: SolverUsed
    verified: bool
    confidence_flag: ConfidenceFlag
    final_answer: str | None
    solve_steps: list[str] = Field(default_factory=list)
    verification_notes: str | None = None
