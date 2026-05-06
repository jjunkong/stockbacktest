/**
 * 목표별 달성/초과/미달 스택 막대 — div+flex로 SVG 없이 구현.
 */
import clsx from "clsx";
import type { MatrixRow } from "@/lib/api-types";

interface HitRateBarProps {
  rows: MatrixRow[];
  trackDays: number;
  className?: string;
}

export function HitRateBar({ rows, trackDays, className }: HitRateBarProps) {
  if (!rows.length) return null;

  return (
    <div className={clsx("kkj-card p-5", className)}>
      <h3 className="font-gmarket-medium text-sm text-kkj-text mb-1">
        목표별 도달 분포
      </h3>
      <p className="kkj-comment mb-5">// 추적 {trackDays}일 / 11~30일 / 미도달</p>

      <div className="space-y-4">
        {rows.map((r) => {
          const inP = r.in_track_rate * 100;
          const overP = r.over_track_rate * 100;
          const missP = r.miss_rate * 100;
          return (
            <div key={r.target}>
              <div className="flex items-baseline justify-between mb-1.5">
                <span className="font-mono-jb text-sm text-kkj-text">{r.target}</span>
                <span className="text-xs text-kkj-text-muted">
                  <span className="font-gmarket-bold text-kkj-emerald-strong">
                    {inP.toFixed(0)}%
                  </span>{" "}
                  · 초과 {overP.toFixed(0)}% · 미달 {missP.toFixed(0)}%
                </span>
              </div>
              <div className="flex h-6 rounded-md overflow-hidden bg-kkj-border-soft">
                <div
                  className="flex items-center justify-center text-[11px] font-bold text-white"
                  style={{ width: `${inP}%`, background: "var(--kkj-emerald)" }}
                  title={`${trackDays}일 내 ${inP.toFixed(1)}%`}
                >
                  {inP >= 8 && `${inP.toFixed(0)}%`}
                </div>
                <div
                  className="flex items-center justify-center text-[11px] font-bold text-white"
                  style={{ width: `${overP}%`, background: "var(--kkj-amber)" }}
                  title={`초과 ${overP.toFixed(1)}%`}
                >
                  {overP >= 10 && `${overP.toFixed(0)}%`}
                </div>
                <div
                  className="flex items-center justify-center text-[11px] font-bold text-white"
                  style={{ width: `${missP}%`, background: "var(--kkj-red)" }}
                  title={`미달 ${missP.toFixed(1)}%`}
                >
                  {missP >= 10 && `${missP.toFixed(0)}%`}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 범례 */}
      <div className="mt-5 flex items-center gap-4 text-xs text-kkj-text-muted">
        <span className="flex items-center gap-1.5">
          <span className="block w-3 h-3 rounded-sm" style={{ background: "var(--kkj-emerald)" }} />
          {trackDays}일 내
        </span>
        <span className="flex items-center gap-1.5">
          <span className="block w-3 h-3 rounded-sm" style={{ background: "var(--kkj-amber)" }} />
          초과 (~30일)
        </span>
        <span className="flex items-center gap-1.5">
          <span className="block w-3 h-3 rounded-sm" style={{ background: "var(--kkj-red)" }} />
          미달
        </span>
      </div>
    </div>
  );
}
