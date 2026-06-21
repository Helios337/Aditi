"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { Header } from "@/components/Header";
import { listAdminQuestions, markReviewed } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import type { AdminQuestionSummary } from "@/lib/types";

export default function AdminPage() {
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [questions, setQuestions] = useState<AdminQuestionSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        router.push("/login");
        return;
      }

      setEmail(session.user.email ?? null);
      setToken(session.access_token);

      try {
        const data = await listAdminQuestions(session.access_token);
        setQuestions(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Admin access failed");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [router]);

  async function handleMarkReviewed(id: string) {
    if (!token) return;
    await markReviewed(token, id, { reviewed: true, confidence_flag: "verified" });
    setQuestions((current) =>
      current.map((question) =>
        question.id === id ? { ...question, reviewed: true, confidence_flag: "verified" } : question
      )
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50">
      <Header email={email} />
      <main className="mx-auto max-w-5xl px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-zinc-900">Review queue</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Manually review flagged answers. Set your email in backend `ADMIN_EMAILS`.
          </p>
        </div>

        {loading ? <p className="text-sm text-zinc-500">Loading...</p> : null}
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}

        <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-zinc-50 text-zinc-500">
              <tr>
                <th className="px-4 py-3 font-medium">Topic</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Confidence</th>
                <th className="px-4 py-3 font-medium">Answer</th>
                <th className="px-4 py-3 font-medium">Reviewed</th>
                <th className="px-4 py-3 font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {questions.map((question) => (
                <tr key={question.id} className="border-t border-zinc-100">
                  <td className="px-4 py-3">
                    <div className="font-medium text-zinc-900">{question.topic || question.subject || "—"}</div>
                    <div className="text-xs text-zinc-400">
                      {question.created_at ? new Date(question.created_at).toLocaleString() : ""}
                    </div>
                  </td>
                  <td className="px-4 py-3 capitalize">{question.status}</td>
                  <td className="px-4 py-3">
                    <ConfidenceBadge flag={question.confidence_flag} />
                  </td>
                  <td className="px-4 py-3 max-w-xs truncate">{question.final_answer || "—"}</td>
                  <td className="px-4 py-3">{question.reviewed ? "Yes" : "No"}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <a
                        href={`/question/${question.id}`}
                        className="rounded-lg border border-zinc-200 px-2 py-1 text-xs hover:bg-zinc-50"
                      >
                        Open
                      </a>
                      {!question.reviewed ? (
                        <button
                          type="button"
                          onClick={() => handleMarkReviewed(question.id)}
                          className="rounded-lg bg-indigo-600 px-2 py-1 text-xs text-white hover:bg-indigo-700"
                        >
                          Mark reviewed
                        </button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {questions.length === 0 && !loading ? (
            <p className="p-6 text-sm text-zinc-500">No questions logged yet.</p>
          ) : null}
        </div>
      </main>
    </div>
  );
}
