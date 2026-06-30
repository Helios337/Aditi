"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { Header } from "@/components/Header";
import { QuestionCard } from "@/components/QuestionCard";
import { QuestionUpload } from "@/components/QuestionUpload";
import { listQuestions } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import type { Question } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshQuestions = useCallback(async (accessToken: string) => {
    const data = await listQuestions(accessToken);
    setQuestions(data);
    setError(null);
  }, []);

  useEffect(() => {
    async function init() {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        router.push("/login");
        return;
      }

      setToken(session.access_token);
      setEmail(session.user.email ?? null);

      try {
        await refreshQuestions(session.access_token);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load questions");
      } finally {
        setLoading(false);
      }
    }

    init();
  }, [router, refreshQuestions]);

  if (loading || !token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50">
        <p className="text-sm text-zinc-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50">
      <Header email={email} />
      <main className="mx-auto grid max-w-5xl gap-6 px-4 py-8 lg:grid-cols-[1.1fr_0.9fr]">
        {error ? (
          <div className="lg:col-span-2 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
            {error}
          </div>
        ) : null}
        <QuestionUpload
          token={token}
          onUploaded={(id) => {
            refreshQuestions(token);
            router.push(`/question/${id}`);
          }}
        />
        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-zinc-900">Recent questions</h2>
          {questions.length === 0 ? (
            <p className="rounded-xl border border-dashed border-zinc-200 bg-white p-6 text-sm text-zinc-500">
              No questions yet. Upload your first doubt to get started.
            </p>
          ) : (
            questions.map((question) => <QuestionCard key={question.id} question={question} />)
          )}
        </section>
      </main>
    </div>
  );
}
