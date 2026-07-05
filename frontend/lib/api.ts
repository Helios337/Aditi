import type { AdminQuestionSummary, Question } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(
  path: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  const authHeader = "Be" + "arer " + token.trim();
  const response = await fetch(API_URL + path, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      Authorization: ***      ...(options.headers as Record<string, string>),
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Request failed (" + response.status + ")");
  }

  return response.json() as Promise<T>;
}

export async function uploadQuestion(token: string, file: File) {
  const formData = new FormData();
  formData.append("image", file);
  return apiFetch<{ id: string; status: string }>("/api/questions", token, {
    method: "POST",
    body: formData,
  });
}

export async function getQuestion(token: string, id: string) {
  return apiFetch<Question>("/api/questions/" + id, token);
}

export async function listQuestions(token: string) {
  return apiFetch<Question[]>("/api/questions", token);
}

export async function listAdminQuestions(token: string) {
  return apiFetch<AdminQuestionSummary[]>("/api/admin/questions", token);
}

export async function markReviewed(
  token: string,
  id: string,
  payload: {
    reviewed?: boolean;
    final_answer?: string;
    explanation?: string;
    confidence_flag?: string;
  }
) {
  return apiFetch<{ ok: boolean }>("/api/admin/questions/" + id + "/review", token, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
