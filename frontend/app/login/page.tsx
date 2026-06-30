"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { createClient } from "@/lib/supabase/client";

const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

const DEMO_ACCOUNTS = [
  { label: "Student demo", email: "demo@aditi.dev", password: "Demo123456!" },
  { label: "Admin demo", email: "admin@aditi.dev", password: "Admin123456!" },
] as const;

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSignUp, setIsSignUp] = useState(false);
  const [loading, setLoading] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [messageType, setMessageType] = useState<"error" | "success">("error");

  async function handleForgotPassword() {
    if (!email.trim()) {
      setMessageType("error");
      setMessage("Enter your email above, then click Forgot password.");
      return;
    }

    setResetting(true);
    setMessage(null);

    const supabase = createClient();
    const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
      redirectTo: `${window.location.origin}/login`,
    });

    setResetting(false);

    if (error) {
      setMessageType("error");
      setMessage(error.message);
      return;
    }

    setMessageType("success");
    setMessage("Password reset email sent. Check your inbox and spam folder.");
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage(null);

    const supabase = createClient();

    if (isSignUp) {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/dashboard`,
        },
      });
      setLoading(false);

      if (error) {
        setMessageType("error");
        setMessage(error.message);
        return;
      }

      if (!data.session) {
        setMessageType("success");
        setMessage(
          "Account created! Check your email for a confirmation link, then sign in here."
        );
        setIsSignUp(false);
        return;
      }

      router.push("/dashboard");
      router.refresh();
      return;
    }

    try {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });

      if (error) {
        setMessageType("error");
        setMessage(error.message);
        return;
      }

      if (!data.session) {
        setMessageType("error");
        setMessage("Sign in failed. Confirm your email first, then try again.");
        return;
      }

      window.location.assign("/dashboard");
    } catch (err) {
      setMessageType("error");
      setMessage(err instanceof Error ? err.message : "Sign in failed. Check your connection.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-violet-50 px-4">
      <div className="w-full max-w-md rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm">
        <div className="mb-6 text-center">
          <h1 className="text-3xl font-semibold text-indigo-700">ADITI</h1>
          <p className="mt-2 text-sm text-zinc-500">Sign in to ask JEE doubts safely</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="mb-1 block text-sm font-medium text-zinc-700">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="w-full rounded-xl border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-500 outline-none ring-indigo-500 focus:ring-2"
            />
          </div>
          <div>
            <div className="mb-1 flex items-center justify-between">
              <label htmlFor="password" className="block text-sm font-medium text-zinc-700">
                Password
              </label>
              {!isSignUp ? (
                <button
                  type="button"
                  onClick={handleForgotPassword}
                  disabled={resetting}
                  className="text-xs font-medium text-indigo-700 hover:underline disabled:opacity-50"
                >
                  {resetting ? "Sending..." : "Forgot password?"}
                </button>
              ) : null}
            </div>
            <input
              id="password"
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="w-full rounded-xl border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-500 outline-none ring-indigo-500 focus:ring-2"
            />
          </div>

          {message ? (
            <p
              className={`text-sm ${
                messageType === "success" ? "text-emerald-700" : "text-rose-600"
              }`}
            >
              {message}
            </p>
          ) : null}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? "Please wait..." : isSignUp ? "Create account" : "Sign in"}
          </button>
        </form>

        <button
          type="button"
          onClick={() => setIsSignUp((value) => !value)}
          className="mt-4 w-full text-sm text-indigo-700 hover:underline"
        >
          {isSignUp ? "Already have an account? Sign in" : "Need an account? Sign up"}
        </button>

        {DEMO_MODE ? (
          <div className="mt-6 rounded-xl border border-indigo-100 bg-indigo-50 p-4">
            <p className="text-sm font-medium text-indigo-900">Demo accounts</p>
            <p className="mt-1 text-xs text-indigo-700">
              Click to fill credentials, then sign in.
            </p>
            <div className="mt-3 space-y-2">
              {DEMO_ACCOUNTS.map((account) => (
                <button
                  key={account.email}
                  type="button"
                  onClick={() => {
                    setIsSignUp(false);
                    setEmail(account.email);
                    setPassword(account.password);
                    setMessage(null);
                  }}
                  className="w-full rounded-lg border border-indigo-200 bg-white px-3 py-2 text-left text-xs text-indigo-900 hover:bg-indigo-100"
                >
                  <span className="font-medium">{account.label}</span>
                  <span className="mt-0.5 block text-indigo-700">
                    {account.email} / {account.password}
                  </span>
                </button>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
