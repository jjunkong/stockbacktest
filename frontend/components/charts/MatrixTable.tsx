/**
 * 백테스트 결과 매트릭스 표 — 모바일 카드 / PC 테이블 하이브리드.
 */
import clsx from "clsx";

import type { MatrixRow } from "@/lib/api-types";
import { Pill } from "@/components/ui";

interface MatrixTableProps {
  rows: MatrixRow[];
  trackDays: number;
  className?: string;
}

function pct(v: number, decimals = 1): string {
  return `${(v * 100).toFixed(decimals)}%`;
}
function pctSigned(v: number | null, decimals = 1): string {
  if (v === null) return "-";
  return `${v >= 0 ? "+" : ""}${(v * 100).toFixed(decimals)}%`;
}

export function MatrixTable({ rows, trackDays, className }: MatrixTableProps) {
  if (!rows.length) {
    return (
      <div className={clsx("kkj-card p-5 text-sm text-kkj-text-muted", className)}>
        데이터 없음
      </div>
    );
  }

  return (
    <div className={className}>
      {/* PC: 테이블 */}
      <div className="hidden sm:block kkj-card-emerald overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-kkj-emerald-glow border-b border-kkj-emerald/30">
              <th className="text-left px-4 py-3 font-gmarket-medium text-kkj-text">목표</th>
              <th className="text-right px-4 py-3 font-gmarket-medium text-kkj-text">{trackDays}일 내</th>
              <th className="text-right px-4 py-3 font-gmarket-medium text-kkj-text">초과</th>
              <th className="text-right px-4 py-3 font-gmarket-medium text-kkj-text">미달</th>
              <th
                className="text-right px-4 py-3 font-gmarket-medium text-kkj-text"
                title="신호 다음날 1일차에 도달 못 했을 때, 결국 추적 끝까지 못 갈 확률"
              >
                1일차 미도달 → 미달%
              </th>
              <th className="text-right px-4 py-3 font-gmarket-medium text-kkj-text">평균 도달일</th>
              <th className="text-right px-4 py-3 font-gmarket-medium text-kkj-text">실패시 MDD</th>
              <th className="text-right px-4 py-3 font-gmarket-medium text-kkj-text">실패시 손익</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr
                key={r.target}
                className={clsx(
                  "border-b border-kkj-border-soft last:border-0",
                  i % 2 === 1 && "bg-kkj-card-soft/40",
                )}
              >
                <td className="px-4 py-3">
                  <Pill variant="emerald">{r.target}</Pill>
                </td>
                <td className="px-4 py-3 text-right font-gmarket-bold text-kkj-emerald-strong">
                  {pct(r.in_track_rate)}
                </td>
                <td className="px-4 py-3 text-right font-mono-jb text-kkj-text-muted">
                  {pct(r.over_track_rate)}
                </td>
                <td className="px-4 py-3 text-right font-mono-jb text-kkj-text-muted">
                  {pct(r.miss_rate)}
                </td>
                <td className="px-4 py-3 text-right font-gmarket-bold text-kkj-red">
                  {r.miss_rate_no_day1 !== null ? pct(r.miss_rate_no_day1) : "-"}
                </td>
                <td className="px-4 py-3 text-right font-mono-jb text-kkj-text">
                  {r.avg_days_to_hit !== null ? `${r.avg_days_to_hit.toFixed(1)}일` : "-"}
                </td>
                <td className="px-4 py-3 text-right font-mono-jb text-kkj-blue">
                  {pctSigned(r.avg_mdd_on_miss)}
                </td>
                <td className="px-4 py-3 text-right font-mono-jb text-kkj-red">
                  {pctSigned(r.avg_pnl_on_miss)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 모바일: 카드 */}
      <div className="grid grid-cols-1 gap-3 sm:hidden">
        {rows.map((r) => (
          <div key={r.target} className="kkj-card-emerald p-4">
            <div className="flex items-center justify-between mb-3">
              <Pill variant="emerald">{r.target}</Pill>
              <div className="font-gmarket-bold text-2xl text-kkj-emerald-strong">
                {pct(r.in_track_rate, 0)}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
              <div className="text-kkj-text-muted">{trackDays}일 내</div>
              <div className="text-right font-mono-jb text-kkj-text">{pct(r.in_track_rate)}</div>
              <div className="text-kkj-text-muted">초과</div>
              <div className="text-right font-mono-jb text-kkj-text">{pct(r.over_track_rate)}</div>
              <div className="text-kkj-text-muted">미달</div>
              <div className="text-right font-mono-jb text-kkj-text">{pct(r.miss_rate)}</div>
              <div className="text-kkj-text-muted">1일차 미도달 → 미달</div>
              <div className="text-right font-mono-jb text-kkj-red font-bold">
                {r.miss_rate_no_day1 !== null ? pct(r.miss_rate_no_day1) : "-"}
              </div>
              <div className="text-kkj-text-muted">평균 도달일</div>
              <div className="text-right font-mono-jb text-kkj-text">
                {r.avg_days_to_hit !== null ? `${r.avg_days_to_hit.toFixed(1)}일` : "-"}
              </div>
              <div className="text-kkj-text-muted">실패시 MDD</div>
              <div className="text-right font-mono-jb text-kkj-blue">
                {pctSigned(r.avg_mdd_on_miss)}
              </div>
              <div className="text-kkj-text-muted">실패시 손익</div>
              <div className="text-right font-mono-jb text-kkj-red">
                {pctSigned(r.avg_pnl_on_miss)}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
