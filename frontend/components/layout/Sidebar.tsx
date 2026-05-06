"use client";

import clsx from "clsx";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { BrandMark, SectionLabel } from "@/components/ui";
import { ControlPanel } from "./ControlPanel";

interface NavItem {
  href: string;
  label: string;
  description: string;
}

const NAV: NavItem[] = [
  { href: "/", label: "날짜별 분석", description: "그 날 신호 묶음의 도달률" },
  { href: "/matrix", label: "전체 매트릭스", description: "조건식 전체 손익비" },
  { href: "/regime", label: "장세별 비교", description: "상승장 vs 하락장" },
  { href: "/detail", label: "종목별 상세", description: "종목 캔들 + 신호 이력" },
  { href: "/themes", label: "테마/산업", description: "주도주 + 관련주" },
];

interface SidebarProps {
  open?: boolean;
  onClose?: () => void;
}

export function Sidebar({ open = false, onClose }: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {/* 모바일 백드롭 */}
      {open && (
        <div
          className="fixed inset-0 bg-black/30 z-30 sm:hidden"
          onClick={onClose}
          aria-hidden
        />
      )}

      <aside
        className={clsx(
          "fixed sm:sticky top-0 left-0 h-screen w-72 z-40",
          "bg-kkj-card border-r border-kkj-border",
          "flex flex-col",
          "transition-transform duration-200",
          open ? "translate-x-0" : "-translate-x-full sm:translate-x-0",
        )}
      >
        {/* 헤더 — 워드마크 */}
        <div className="px-5 py-4 border-b border-kkj-border-soft">
          <BrandMark size="md" />
          <p className="mt-1 text-xs text-kkj-text-soft">
            키움 조건검색식 백테스팅
          </p>
        </div>

        {/* 스크롤 본문 */}
        <div className="flex-1 overflow-y-auto">
          {/* 네비 */}
          <nav className="px-4 py-4 space-y-1 border-b border-kkj-border-soft">
            <SectionLabel className="px-2 mb-2 block">분석</SectionLabel>
            {NAV.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onClose}
                  className={clsx(
                    "block px-3 py-2.5 rounded-lg transition-colors",
                    active
                      ? "bg-kkj-emerald-glow border border-kkj-emerald"
                      : "hover:bg-kkj-card-soft border border-transparent",
                  )}
                >
                  <div
                    className={clsx(
                      "font-gmarket-medium text-sm",
                      active ? "text-kkj-emerald-strong" : "text-kkj-text",
                    )}
                  >
                    {item.label}
                  </div>
                  <div className="text-[11px] text-kkj-text-soft mt-0.5">
                    {item.description}
                  </div>
                </Link>
              );
            })}
          </nav>

          {/* 컨트롤 */}
          <div className="px-5 py-4">
            <ControlPanel />
          </div>
        </div>

        {/* 푸터 */}
        <div className="px-5 py-3 border-t border-kkj-border-soft">
          <span className="text-[11px] text-kkj-text-soft font-mono-jb">
            v0.1.0
          </span>
        </div>
      </aside>
    </>
  );
}
