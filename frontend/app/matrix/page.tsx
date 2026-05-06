"use client";

import { useMemo } from "react";

import { Shell } from "@/components/layout/Shell";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  GreenContextCard,
  Pill,
  StatCard,
} from "@/components/ui";
import { MatrixTable } from "@/components/charts/MatrixTable";
import { HitRateBar } from "@/components/charts/HitRateBar";
import { DaysHistogram } from "@/components/charts/DaysHistogram";
import { useBacktestConfig } from "@/lib/hooks/useBacktestConfig";
import { useBacktest } from "@/lib/hooks/useBacktest";

const COND_LABEL: Record<string, string> = {
  cond1: "급등주 추격형",
  cond2: "갭상승 정배열형",
};
const ENTRY_LABEL: Record<string, string> = {
  close_today: "당일 종가",
  open_next: "다음날 시가",
  close_next: "다음날 종가",
};
const MARKET_LABEL: Record<string, string> = {
  all: "전체",
  KOSPI: "KOSPI",
  KOSDAQ: "KOSDAQ",
};

export default function MatrixPage() {
  const { config } = useBacktestConfig();
  const { data, isLoading, isError, error } = useBacktest(config);

  const kpi = useMemo(() => {
    if (!data) return null;
    const target10 = data.matrix.find((r) => r.target === "+10%") ?? data.matrix[0];
    const validDays = data.matrix.filter((r) => r.avg_days_to_hit !== null);
    const validMdd = data.matrix.filter((r) => r.avg_mdd_on_miss !== null);
    return {
      n: data.n_signals,
      target10Rate: target10?.in_track_rate ?? 0,
      avgDays:
        validDays.reduce((a, r) => a + (r.avg_days_to_hit ?? 0), 0) /
        Math.max(1, validDays.length),
      avgMdd:
        validMdd.reduce((a, r) => a + (r.avg_mdd_on_miss ?? 0), 0) /
        Math.max(1, validMdd.length),
    };
  }, [data]);

  return (
    <Shell>
      <div className="space-y-6">
        <PageHeader
          eyebrow="Backtest"
          title="전체 매트릭스"
          description="조건식이 잡은 모든 신호의 목표별 도달률"
          trailing={
            <div className="flex flex-wrap items-center gap-2">
              <Pill variant="emerald">{COND_LABEL[config.cond] ?? config.cond}</Pill>
              <Pill variant="emerald">{MARKET_LABEL[config.market]}</Pill>
              <Pill variant="neutral">{ENTRY_LABEL[config.entry]}</Pill>
            </div>
          }
        />

        {data && (
          <GreenContextCard
            contextLabel="현재 분석"
            title={`${COND_LABEL[data.condition] ?? data.condition} · ${data.entry_label} · 추적 ${data.track_days}일`}
            sub={`${MARKET_LABEL[data.market]} · 신호 ${data.n_signals.toLocaleString()}건`}
            metricLabel="평균 도달률"
            metricValue={`${(data.avg_hit_rate * 100).toFixed(0)}%`}
          />
        )}

        {isLoading && (
          <div className="kkj-card p-8 text-center text-kkj-text-muted">
            백테스트 실행 중…
          </div>
        )}
        {isError && (
          <div className="kkj-card p-5 border-l-4 border-kkj-red">
            <div className="text-sm text-kkj-red font-bold mb-1">백엔드 응답 실패</div>
            <p className="text-xs text-kkj-text-muted">{(error as Error).message}</p>
          </div>
        )}

        {data && kpi && (
          <>
            <section className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <StatCard
                label="신호 총 발생"
                value={kpi.n.toLocaleString()}
                sub={`${data.condition} · 시총 1,000억↑`}
              />
              <StatCard
                label={`+10% ${data.track_days}일 내`}
                value={`${(kpi.target10Rate * 100).toFixed(1)}%`}
                sub="대표 손익비 지표"
              />
              <StatCard
                label="평균 도달일"
                value={`${kpi.avgDays.toFixed(1)}일`}
                sub="성공 케이스만"
              />
              <StatCard
                label="실패시 평균 MDD"
                value={`${(kpi.avgMdd * 100).toFixed(1)}%`}
                sub="추적 기간 최저점"
                deltaTone="down"
              />
            </section>

            <section>
              <h2 className="font-gmarket-medium text-base text-kkj-text mb-3">
                목표별 매트릭스
              </h2>
              <MatrixTable rows={data.matrix} trackDays={data.track_days} />
            </section>

            <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <HitRateBar rows={data.matrix} trackDays={data.track_days} />
              <DaysHistogram rows={data.matrix} trackDays={data.track_days} />
            </section>
          </>
        )}
      </div>
    </Shell>
  );
}
