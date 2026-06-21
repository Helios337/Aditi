export type QuestionStatus = "pending" | "processing" | "completed" | "failed";
export type ConfidenceFlag = "verified" | "unverified" | "needs_review";
export type SolverUsed = "sympy" | "wolfram" | "llm_only";

export interface Question {
  id: string;
  status: QuestionStatus;
  image_url?: string | null;
  ocr_text?: string | null;
  ocr_confidence?: number | null;
  subject?: string | null;
  topic?: string | null;
  question_type?: string | null;
  solver_used?: SolverUsed | null;
  verified: boolean;
  confidence_flag: ConfidenceFlag;
  final_answer?: string | null;
  explanation?: string | null;
  error_message?: string | null;
  reviewed: boolean;
  reviewed_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AdminQuestionSummary {
  id: string;
  status: QuestionStatus;
  student_id?: string | null;
  subject?: string | null;
  topic?: string | null;
  confidence_flag: ConfidenceFlag;
  verified: boolean;
  reviewed: boolean;
  final_answer?: string | null;
  created_at?: string | null;
}
