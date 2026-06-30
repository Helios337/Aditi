"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { Header } from "@/components/Header";
import { getQuestion } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import type { Question } from "@/lib/types";

export default function QuestionPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [question, setQuestion] = useState<Question | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let interval: ReturnType<typeof setInterval> | undefined;

    async function load() {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        router.push("/login");
        return;
      }

      if (active) setEmail(session.user.email ?? null);

      try {
        const data = await getQuestion(session.access_token, params.id);
        if (active) {
          setQuestion(data);
          setError(null);
        }
        if (data.status === "pending" || data.status === "processing") {
          interval = setInterval(async () => {
            const updated = await getQuestion(session.access_token, params.id);
            if (active) setQuestion(updated);
            if (updated.status === "completed" || updated.status === "failed") {
              clearInterval(interval);
            }
          }, 3000);
        }
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Failed to load question");
      }
    }

    load();
    return () => {
      active = false;
      if (interval) clearInterval(interval);
    };
  }, [params.id, router]);

  return (
    <div className="min-h-screen bg-zinc-50">
      <Header email={email} />
      <main className="mx-auto max-w-3xl px-4 py-8">
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        {!question ? (
          <p className="text-sm text-zinc-500">Loading question...</p>
        ) : (
          <article className="space-y-6 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm uppercase tracking-wide text-zinc-400">{question.status}</p>
                <h1 className="text-2xl font-semibold text-zinc-900">
                  {question.topic || "Your question"}
                </h1>
              </div>
              <ConfidenceBadge flag={question.confidence_flag} />
            </div>

            {question.image_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={question.image_url}
                alt="Uploaded question"
                className="max-h-96 w-full rounded-xl border border-zinc-200 object-contain"
              />
            ) : null}

            <section>
              <h2 className="text-sm font-medium text-zinc-700">OCR text</h2>
              <pre className="mt-2 whitespace-pre-wrap rounded-xl bg-zinc-50 p-4 text-sm text-zinc-700">
                {question.ocr_text || "Waiting for OCR..."}
              </pre>
            </section>

            {question.final_answer ? (
              <section>
                <h2 className="text-sm font-medium text-zinc-700">Answer</h2>
                <p className="mt-2 rounded-xl bg-emerald-50 p-4 text-lg font-medium text-emerald-900">
                  {question.final_answer}
                </p>
              </section>
            ) : question.status === "failed" ? (
              <section className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
                <p className="font-medium">Processing failed</p>
                <p className="mt-2">{question.error_message || "Please try uploading again."}</p>
              </section>
            ) : question.confidence_flag === "needs_review" ? (
              <section className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
                This answer needs manual review. Working explanation is shown below, but no verified
                final answer is displayed yet.
              </section>
            ) : null}

            {question.explanation ? (
              <section>
                <h2 className="text-sm font-medium text-zinc-700">Explanation</h2>
                <div className="prose prose-sm mt-2 max-w-none whitespace-pre-wrap text-zinc-700">
                  {question.explanation}
                </div>
              </section>
            ) : null}

            {question.error_message && question.status !== "failed" ? (
              <p className="text-sm text-rose-600">{question.error_message}</p>
            ) : null}

            <div className="flex flex-wrap gap-3 text-xs text-zinc-500">
              {question.solver_used ? <span>Solver: {question.solver_used}</span> : null}
              {question.ocr_confidence != null ? (
                <span>OCR confidence: {(question.ocr_confidence * 100).toFixed(0)}%</span>
              ) : null}
              {question.verified ? <span>SymPy verified</span> : null}
            </div>
          </article>
        )}
      </main>
    </div>
  );
}
