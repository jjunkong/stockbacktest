/**
 * Hero 스탯 카드 — 큰 숫자를 강조하는 그린 그라데이션 카드.
 * 학원앱의 검정+그린 글로우 D-day 카드와는 다른 톤 (밝고 깔끔).
 */
import clsx from "clsx";

interface HeroStatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  className?: string;
}

export function HeroStatCard({ label, value, sub, className }: HeroStatCardProps) {
  return (
    <div
      className={clsx(
        "relative overflow-hidden rounded-2xl p-6 sm:p-7 text-white",
        className,
      )}
      style={{
        background: "linear-gradient(135deg, #10B981 0%, #059669 100%)",
        boxShadow: "0 6px 24px rgba(16, 185, 129, 0.18)",
      }}
    >
      {/* 우상단 부드러운 화이트 글로우 */}
      <div
        className="absolute -top-16 -right-16 w-48 h-48 rounded-full pointer-events-none"
        style={{
          background:
            "radial-gradient(circle, rgba(255,255,255,0.28) 0%, rgba(255,255,255,0) 70%)",
        }}
        aria-hidden
      />

      <div className="relative">
        <div className="text-[11px] uppercase tracking-[0.1em] opacity-90 font-bold">
          {label}
        </div>
        <div className="font-gmarket-bold leading-none mt-3 text-4xl sm:text-5xl">
          {value}
        </div>
        {sub && <div className="mt-3 text-sm opacity-90">{sub}</div>}
      </div>
    </div>
  );
}
