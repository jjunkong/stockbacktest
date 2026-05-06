"use client";

import { useMemo } from "react";

import { Shell } from "@/components/layout/Shell";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  HeroStatCard,
  Pill,
} from "@/components/ui";
import { MatrixTable } from "@/components/charts/MatrixTable";
import { CandleChart } from "@/components/charts/CandleChart";
import { useBacktestConfig } from "@/lib/hooks/useBacktestConfig";
import {
  useKospi,
  useRegimeComparison,
  useSignalDates,
} from "@/lib/hooks/useBacktest";
import type { KospiRow, OHLCVRow } from "@/lib/api-types";

/** KospiRow → OHLCVRow 변환 (CandleChart 재사용) */
function toOHLCV(rows: KospiRow[]): OHLCVRow[] {
  return rows.map((r) => ({
    date: r.date,
    open: r.open,
    high: r.high,
    low: r.low,
    close: r.close,
    volume: r.volume,
    change_rate: r.change_rate,
  }));
}

const COND_LABEL: Record<string, string> = {
  cond1: "급등주 추격형",
  cond2: "갭상승 정배열형",
};
const MARKET_LABEL: Record<string, string> = {
  all: "전체",
  KOSPI: "KOSPI",
  KOSDAQ: "KOSDAQ",
};
const REGIME_LABEL_KOR: Record<string, string> = {
  bull: "상승장",
  bear: "하락장",
  unknown: "분류불가",
};

export default function RegimePage() {
  const { config } = useBacktestConfig();
  const regimeQ = useRegimeComparison(config);
  const datesQ = useSignalDates(config);

  const range = useMemo(() => {
    if (!datesQ.data || datesQ.data.length === 0) return null;
    const sorted = [...datesQ.data].sort();
    return { start: sorted[0], end: sorted[sorted.length - 1] };
  }, [datesQ.data]);

  const kospiQ = useKospi(range?.start ?? "", range?.end ?? "", 60);

  return (
    <Shell>
      <div className="space-y-6">
        <PageHeader
          eyebrow="Backtest"
          title="장세별 비교"
          description="코스피 60일 이평 위(상승장) / 아래(하락장)의 도달률 차이"
          trailing={
            <div className="flex flex-wrap items-center gap-2">
              <Pill variant="emerald">{COND_LABEL[config.cond] ?? config.cond}</Pill>
              <Pill variant="emerald">{MARKET_LABEL[config.market]}</Pill>
            </div>
          }
        />

        {regimeQ.isLoading && (
          <div className="kkj-card p-8 text-center text-kkj-text-muted">
            장세 분석 중…
          </div>
        )}
        {regimeQ.isError && (
          <div className="kkj-card p-5 border-l-4 border-kkj-red">
            <div className="text-sm text-kkj-red font-bold mb-1">실패</div>
            <p className="text-xs text-kkj-text-muted">{(regimeQ.error as Error).message}</p>
          </div>
        )}

        {regimeQ.data && (
          <>
            {/* 장세 분포 Hero 2개 */}
            <section className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {regimeQ.data.regimes.map((r) => (
                <HeroStatCard
                  key={r.regime}
                  label={REGIME_LABEL_KOR[r.regime] ?? r.regime}
                  value={r.n_signals.toLocaleString()}
                  sub={`코스피 60일 이평 ${r.regime === "bull" ? "위" : "아래"}`}
                />
              ))}
            </section>

            {/* 분포 요약 */}
            <section className="kkj-card p-5">
              <p className="text-xs text-kkj-text-muted font-bold uppercase tracking-wider mb-2">
                전체 분포
              </p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(regimeQ.data.distribution).map(([k, v]) => (
                  <Pill
                    key={k}
                    variant={k === "bull" ? "emerald" : k === "bear" ? "red" : "neutral"}
                  >
                    {REGIME_LABEL_KOR[k] ?? k} {v.toLocaleString()}건
                  </Pill>
                ))}
              </div>
            </section>

            {/* 매트릭스 */}
            {regimeQ.data.regimes.map((r) => (
              <section key={r.regime}>
                <h2 className="font-gmarket-medium text-base text-kkj-text mb-3">
                  {REGIME_LABEL_KOR[r.regime] ?? r.regime} 매트릭스{" "}
                  <span className="text-kkj-text-soft text-sm font-mono-jb">
                    ({r.n_signals.toLocaleString()}건)
                  </span>
                </h2>
                <MatrixTable rows={r.rows} trackDays={config.trackDays} />
              </section>
            ))}

            {/* 코스피 일봉 캔들 + MA20/120/240 */}
            {kospiQ.data && (
              <section>
                <h2 className="font-gmarket-medium text-base text-kkj-text mb-3">
                  코스피 일봉{" "}
                  <span className="text-sm text-kkj-text-soft">
                    · MA20 / MA120 / MA240
                  </span>
                </h2>
                <CandleChart rows={toOHLCV(kospiQ.data.rows)} height={500} />
              </section>
            )}
          </>
        )}
      </div>
    </Shell>
  );
}
