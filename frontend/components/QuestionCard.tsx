import Link from "next/link";

import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import type { Question } from "@/lib/types";

export function QuestionCard({ question }: { question: Question }) {
  return (
    <Link
      href={`/question/${question.id}`}
      className="block rounded-xl border border-zinc-200 bg-white p-4 shadow-sm transition hover:border-indigo-200 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-zinc-900">
            {question.topic || question.subject || "Question"}
          </p>
          <p className="mt-1 line-clamp-2 text-sm text-zinc-500">
            {question.ocr_text || "Processing OCR..."}
          </p>
        </div>
        <ConfidenceBadge flag={question.confidence_flag} />
      </div>
      <div className="mt-3 flex items-center justify-between text-xs text-zinc-400">
        <span className="capitalize">{question.status}</span>
        <span>{question.created_at ? new Date(question.created_at).toLocaleString() : ""}</span>
      </div>
    </Link>
  );
}
