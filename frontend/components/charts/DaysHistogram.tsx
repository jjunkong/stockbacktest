/**
 * 도달일 분포 히스토그램 — 백테스트 raw에서 days_to_target만 보내주면 그림.
 * (간단 SVG. Plotly/Recharts 없이.)
 *
 * 우리 백엔드에서 raw 결과는 매트릭스 응답이 아닌 별도 엔드포인트에 있음.
 * 매트릭스 응답에는 평균 도달일만 있으므로, 이 컴포넌트는
 * 매트릭스의 평균 도달일을 막대로 보여주는 단순 막대 그래프로 변형.
 */
import clsx from "clsx";
import type { MatrixRow } from "@/lib/api-types";

interface DaysBarProps {
  rows: MatrixRow[];
  trackDays: number;
  className?: string;
}

const COLORS = ["#10B981", "#34D399", "#F59E0B", "#EF4444"];

export function DaysHistogram({ rows, trackDays, className }: DaysBarProps) {
  if (!rows.length) return null;
  const max = Math.max(
    ...rows.map((r) => r.avg_days_to_hit ?? 0),
    trackDays + 5,
  );

  return (
    <div className={clsx("kkj-card p-5", className)}>
      <h3 className="font-gmarket-medium text-sm text-kkj-text mb-1">
        목표별 평균 도달일
      </h3>
      <p className="kkj-comment mb-5">// 도달한 케이스만 평균. 추적 {trackDays}일 기준선 표시</p>

      <div className="relative" style={{ height: 220 }}>
        {/* 추적 기간 가이드 라인 */}
        <div
          className="absolute left-0 right-0 border-t border-dashed border-kkj-border"
          style={{ bottom: `${(trackDays / max) * 100}%` }}
        >
          <span className="absolute -top-5 right-0 text-[10px] font-mono-jb text-kkj-text-soft">
            {trackDays}일
          </span>
        </div>

        <div className="flex items-end justify-around h-full gap-3 sm:gap-6 px-1">
          {rows.map((r, i) => {
            const days = r.avg_days_to_hit ?? 0;
            const h = (days / max) * 100;
            const color = COLORS[i % COLORS.length];
            return (
              <div key={r.target} className="flex-1 flex flex-col items-center gap-2 h-full justify-end">
                <span className="text-[11px] font-mono-jb text-kkj-text-muted">
                  {days > 0 ? `${days.toFixed(1)}일` : "-"}
                </span>
                <div
                  className="w-full rounded-t-md transition-all"
                  style={{
                    height: `${h}%`,
                    background: color,
                    minHeight: days > 0 ? 4 : 0,
                  }}
                />
                <span className="text-xs font-bold text-kkj-text">{r.target}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
