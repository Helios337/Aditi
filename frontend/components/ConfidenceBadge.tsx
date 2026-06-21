import type { ConfidenceFlag } from "@/lib/types";

const styles: Record<ConfidenceFlag, string> = {
  verified: "bg-emerald-100 text-emerald-800 border-emerald-200",
  unverified: "bg-amber-100 text-amber-800 border-amber-200",
  needs_review: "bg-rose-100 text-rose-800 border-rose-200",
};

const labels: Record<ConfidenceFlag, string> = {
  verified: "Verified",
  unverified: "AI-generated, not verified",
  needs_review: "Needs review",
};

export function ConfidenceBadge({ flag }: { flag: ConfidenceFlag }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles[flag]}`}
    >
      {labels[flag]}
    </span>
  );
}
