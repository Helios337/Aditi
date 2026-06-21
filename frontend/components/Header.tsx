"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { createClient } from "@/lib/supabase/client";

export function Header({ email }: { email?: string | null }) {
  const router = useRouter();

  async function signOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  }

  return (
    <header className="border-b border-zinc-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
        <div>
          <Link href="/dashboard" className="text-xl font-semibold tracking-tight text-indigo-700">
            ADITI
          </Link>
          <p className="text-sm text-zinc-500">JEE doubt-solving pilot</p>
        </div>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/dashboard" className="text-zinc-700 hover:text-indigo-700">
            Ask
          </Link>
          <Link href="/admin" className="text-zinc-700 hover:text-indigo-700">
            Review
          </Link>
          {email ? <span className="hidden text-zinc-500 sm:inline">{email}</span> : null}
          <button
            type="button"
            onClick={signOut}
            className="rounded-lg border border-zinc-200 px-3 py-1.5 text-zinc-700 hover:bg-zinc-50"
          >
            Sign out
          </button>
        </nav>
      </div>
    </header>
  );
}
