/**
 * 섹션 라벨 — 작은 회색 대문자, 글자 간격 트래킹.
 * 학원앱의 "// 코드 주석" 톤 대신 일반 데이터 대시보드 라벨.
 */
import clsx from "clsx";
import type { ReactNode } from "react";

interface SectionLabelProps {
  children: ReactNode;
  className?: string;
}

export function SectionLabel({ children, className }: SectionLabelProps) {
  return (
    <span
      className={clsx(
        "inline-block text-[11px] font-bold uppercase tracking-[0.08em]",
        "text-kkj-text-muted",
        className,
      )}
    >
      {children}
    </span>
  );
}
