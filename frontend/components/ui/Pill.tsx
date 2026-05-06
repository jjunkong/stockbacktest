/**
 * 작은 상태 배지.
 *   <Pill variant="emerald">10일 내 도달</Pill>
 *   <Pill variant="amber">초과 도달</Pill>
 *   <Pill variant="red">미도달</Pill>
 */
import clsx from "clsx";
import type { ReactNode } from "react";

type PillVariant = "emerald" | "amber" | "red" | "neutral";

interface PillProps {
  variant?: PillVariant;
  children: ReactNode;
  className?: string;
}

const variantClass: Record<PillVariant, string> = {
  emerald: "kkj-pill-emerald",
  amber: "kkj-pill-amber",
  red: "kkj-pill-red",
  neutral:
    "inline-flex items-center bg-kkj-card-soft text-kkj-text-muted text-xs font-semibold rounded-md px-2 py-0.5 border border-kkj-border",
};

export function Pill({ variant = "emerald", children, className }: PillProps) {
  return (
    <span className={clsx(variantClass[variant], className)}>{children}</span>
  );
}
