/**
 * 좌측에 그린 액센트 라인이 있는 KPI 카드.
 */
import clsx from "clsx";
import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: string | number | ReactNode;
  sub?: string;
  delta?: string;
  deltaTone?: "up" | "down" | "neutral";
  className?: string;
}

export function StatCard({
  label,
  value,
  sub,
  delta,
  deltaTone = "neutral",
  className,
}: StatCardProps) {
  const deltaColor =
    deltaTone === "up"
      ? "text-kkj-emerald-strong"
      : deltaTone === "down"
        ? "text-kkj-red"
        : "text-kkj-text-muted";

  return (
    <div
      className={clsx(
        "kkj-card relative pl-5 pr-5 py-4 transition-colors",
        "hover:border-kkj-emerald",
        className,
      )}
    >
      <span
        className="absolute left-0 top-3 bottom-3 w-1 rounded-full"
        style={{ background: "var(--kkj-emerald)" }}
      />
      <div className="text-xs text-kkj-text-muted font-bold tracking-wider uppercase">
        {label}
      </div>
      <div className="mt-1 text-2xl font-gmarket-bold text-kkj-text leading-tight">
        {value}
      </div>
      {(sub || delta) && (
        <div className="mt-1.5 flex items-baseline gap-2 text-xs">
          {sub && <span className="text-kkj-text-soft">{sub}</span>}
          {delta && <span className={clsx("font-mono-jb", deltaColor)}>{delta}</span>}
        </div>
      )}
    </div>
  );
}
