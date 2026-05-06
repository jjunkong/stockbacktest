/**
 * 페이지 상단 공통 헤더.
 * 작은 섹션 라벨 + 큰 타이틀 + 보조 설명 + 우측 trailing.
 */
import { SectionLabel } from "@/components/ui";
import type { ReactNode } from "react";

interface PageHeaderProps {
  eyebrow?: string;          // 상단 작은 라벨 (예: "Backtest")
  title: string;
  description?: string;
  trailing?: ReactNode;
}

export function PageHeader({ eyebrow, title, description, trailing }: PageHeaderProps) {
  return (
    <header className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 sm:gap-4">
      <div className="min-w-0">
        {eyebrow && <SectionLabel>{eyebrow}</SectionLabel>}
        <h1 className="mt-1 text-2xl sm:text-3xl font-gmarket-bold text-kkj-text leading-tight">
          {title}
        </h1>
        {description && (
          <p className="mt-1.5 text-sm text-kkj-text-muted">{description}</p>
        )}
      </div>
      {trailing && <div className="shrink-0">{trailing}</div>}
    </header>
  );
}
