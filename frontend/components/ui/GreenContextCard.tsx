/**
 * 메인 헤더 아래의 "현재 분석 중" 그린 박스 카드.
 * 좌측: 라벨 + 큰 제목 + 보조설명
 * 우측: 큰 강조 숫자 (예: 도달률)
 */
import clsx from "clsx";

interface GreenContextCardProps {
  contextLabel?: string;          // "// 현재 분석 중"
  title: string;                  // 굵은 큰 제목
  sub?: string;                   // 보조 설명
  metricLabel?: string;           // 우측 숫자 위 라벨
  metricValue: string;            // 우측 큰 숫자
  className?: string;
}

export function GreenContextCard({
  contextLabel = "현재 분석 중",
  title,
  sub,
  metricLabel,
  metricValue,
  className,
}: GreenContextCardProps) {
  return (
    <div
      className={clsx(
        "rounded-2xl text-white p-5 sm:p-6",
        "flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4",
        className,
      )}
      style={{
        background: "var(--kkj-emerald)",
        boxShadow: "0 6px 24px rgba(16, 185, 129, 0.20)",
      }}
    >
      <div className="min-w-0">
        <div className="text-xs sm:text-sm opacity-80 font-mono-jb">{`// ${contextLabel}`}</div>
        <div className="mt-1 font-gmarket-bold text-xl sm:text-2xl leading-snug">
          {title}
        </div>
        {sub && <div className="mt-2 text-sm opacity-85">{sub}</div>}
      </div>
      <div className="flex flex-col items-start sm:items-end shrink-0">
        {metricLabel && (
          <div className="text-xs opacity-80 font-mono-jb">{`// ${metricLabel}`}</div>
        )}
        <div
          className="font-gmarket-bold text-4xl sm:text-5xl leading-none mt-1"
          style={{ textShadow: "0 0 18px rgba(255,255,255,0.25)" }}
        >
          {metricValue}
        </div>
      </div>
    </div>
  );
}
