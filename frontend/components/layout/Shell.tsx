"use client";

import { Menu } from "lucide-react";
import { useState, type ReactNode } from "react";

import { BrandMark } from "@/components/ui";
import { Sidebar } from "./Sidebar";

/**
 * 전체 레이아웃 셸 — 사이드바 + 메인 컨텐츠.
 * 모바일에선 사이드바 숨김 + 햄버거 토글.
 */
export function Shell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex min-h-screen">
      <Sidebar open={open} onClose={() => setOpen(false)} />

      <div className="flex-1 min-w-0 flex flex-col">
        {/* 모바일 탑바 */}
        <header className="sm:hidden sticky top-0 z-20 bg-kkj-card border-b border-kkj-border">
          <div className="flex items-center justify-between px-4 py-3">
            <button
              type="button"
              onClick={() => setOpen(true)}
              className="kkj-focus p-2 -ml-2 rounded-md hover:bg-kkj-card-soft"
              aria-label="메뉴 열기"
            >
              <Menu className="w-5 h-5 text-kkj-text" />
            </button>
            <BrandMark size="sm" />
            <span className="w-8" />
          </div>
        </header>

        <main className="flex-1 px-4 sm:px-8 py-6 sm:py-8 max-w-[1400px] w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
