"use client";

import { useEffect, useMemo, useState } from "react";
import clsx from "clsx";

import { Shell } from "@/components/layout/Shell";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  HeroStatCard,
  Pill,
  SectionLabel,
} from "@/components/ui";
import { LiveQuote } from "@/components/ui/LiveQuote";
import { CandleChart } from "@/components/charts/CandleChart";
import { useBacktestConfig } from "@/lib/hooks/useBacktestConfig";
import {
  useDateBundle,
  useSignalDates,
  useTickerOhlcv,
} from "@/lib/hooks/useBacktest";
import { useQuotes, quotesByTicker } from "@/lib/hooks/useQuotes";

const MARKET_LABEL: Record<string, string> = {
  all: "전체",
  KOSPI: "KOSPI",
  KOSDAQ: "KOSDAQ",
};

const COND_LABEL: Record<string, string> = {
  cond1: "급등주 추격형",
  cond2: "갭상승 정배열형",
};

function fmtDate(s: string): { md: string; weekday: string } {
  const d = new Date(s);
  const md = `${d.getMonth() + 1}/${d.getDate()}`;
  const weekday = ["일", "월", "화", "수", "목", "금", "토"][d.getDay()];
  return { md, weekday };
}

export default function DatePage() {
  const { config } = useBacktestConfig();
  const datesQ = useSignalDates(config);
  const dates = datesQ.data ?? [];

  const [pickedDate, setPickedDate] = useState<string | null>(null);
  useEffect(() => {
    if (!pickedDate && dates.length > 0) setPickedDate(dates[0]);
    else if (pickedDate && dates.length > 0 && !dates.includes(pickedDate)) {
      setPickedDate(dates[0]);
    }
  }, [dates, pickedDate]);

  const bundleQ = useDateBundle(config, pickedDate);

  const [pickedTicker, setPickedTicker] = useState<string | null>(null);
  useEffect(() => {
    if (bundleQ.data && bundleQ.data.individuals.length > 0) {
      setPickedTicker(bundleQ.data.individuals[0].ticker);
    } else {
      setPickedTicker(null);
    }
  }, [bundleQ.data]);

  const selected = useMemo(
    () =>
      bundleQ.data?.individuals.find((s) => s.ticker === pickedTicker) ?? null,
    [bundleQ.data, pickedTicker],
  );

  const ohlcvRange = useMemo(() => {
    if (!selected || !pickedDate) return null;
    const d = new Date(pickedDate);
    // MA240을 표시하려면 최소 240거래일+α 분량이 필요. 신호일 기준 약 1.5년 전부터 가져옴.
    const start = new Date(d);
    start.setDate(d.getDate() - 480);
    const end = new Date(d);
    end.setDate(d.getDate() + 60);
    return {
      start: start.toISOString().slice(0, 10),
      end: end.toISOString().slice(0, 10),
    };
  }, [selected, pickedDate]);

  const ohlcvQ = useTickerOhlcv(selected?.ticker ?? null, ohlcvRange ?? undefined);

  // 카드별 실시간 시세 (2초 폴링)
  const cardTickers = useMemo(
    () => bundleQ.data?.individuals.map((s) => s.ticker) ?? [],
    [bundleQ.data],
  );
  const quotesQ = useQuotes(cardTickers);
  const quoteMap = useMemo(() => quotesByTicker(quotesQ.data), [quotesQ.data]);

  const heroMetric = useMemo(() => {
    if (!bundleQ.data) return null;
    const stats = bundleQ.data.bundle_stats;
    const tgt10 = stats.find((s) => s.target === "+10%") ?? stats[0];
    return {
      n: bundleQ.data.n_signals,
      hitRate: tgt10 ? Math.round(tgt10.hit_rate * 100) : 0,
      tgtLabel: tgt10?.target ?? "-",
    };
  }, [bundleQ.data]);

  return (
    <Shell>
      <div className="space-y-6">
        <PageHeader
          eyebrow="Backtest"
          title="날짜별 분석"
          description="특정 날짜에 잡힌 신호 묶음의 도달률을 한눈에"
          trailing={
            <div className="flex flex-wrap items-center gap-2">
              <Pill variant="emerald">{COND_LABEL[config.cond] ?? config.cond}</Pill>
              <Pill variant="emerald">{MARKET_LABEL[config.market]}</Pill>
              <Pill variant="neutral">신호일 {datesQ.data?.length ?? 0}개</Pill>
            </div>
          }
        />

        {/* Hero + 캘린더 */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-1">
            {pickedDate && heroMetric ? (
              <HeroStatCard
                label={`${pickedDate} · ${heroMetric.tgtLabel} 도달`}
                value={`${heroMetric.hitRate}%`}
                sub={`${heroMetric.n}종목 · 추적 ${config.trackDays}일`}
              />
            ) : (
              <div className="kkj-card p-6 text-sm text-kkj-text-muted">
                날짜를 선택하면 묶음 도달률이 여기에 표시됩니다.
              </div>
            )}
          </div>

          <div className="lg:col-span-2 kkj-card p-5">
            <SectionLabel className="mb-2 block">날짜 선택</SectionLabel>

            <input
              type="date"
              value={pickedDate ?? ""}
              onChange={(e) => setPickedDate(e.target.value || null)}
              min={dates[dates.length - 1]}
              max={dates[0]}
              className="w-full rounded-lg border border-kkj-border bg-kkj-card px-3 py-2 text-sm font-mono-jb kkj-focus hover:border-kkj-emerald transition-colors"
            />

            {dates.length > 0 && (
              <div className="mt-3">
                <SectionLabel className="mb-2 block">최근 신호일</SectionLabel>
                <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5">
                  {dates.slice(0, 6).map((d) => {
                    const f = fmtDate(d);
                    const active = pickedDate === d;
                    return (
                      <button
                        key={d}
                        onClick={() => setPickedDate(d)}
                        className={clsx(
                          "rounded-md text-xs font-mono-jb py-1.5 transition-colors kkj-focus",
                          active
                            ? "bg-kkj-emerald text-white"
                            : "bg-kkj-card-soft text-kkj-text-muted hover:bg-kkj-emerald-glow hover:text-kkj-emerald-strong",
                        )}
                      >
                        {f.md} {f.weekday}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </section>

        {/* 신호일 로딩/에러 */}
        {datesQ.isLoading && (
          <div className="kkj-card p-8 text-center text-kkj-text-muted">
            신호 발생일 가져오는 중…
          </div>
        )}
        {datesQ.isError && (
          <div className="kkj-card p-5 border-l-4 border-kkj-red">
            <div className="text-sm text-kkj-red font-bold mb-1">
              백엔드 응답 실패
            </div>
            <p className="text-xs text-kkj-text-muted">{(datesQ.error as Error).message}</p>
            <p className="mt-2 text-xs text-kkj-text-muted">
              backend/ 에서 uvicorn 서버가 떠있는지 확인하세요. (http://localhost:8000)
            </p>
          </div>
        )}
        {!datesQ.isLoading &&
          !datesQ.isError &&
          datesQ.data &&
          datesQ.data.length === 0 && (
            <div className="kkj-card p-5 text-sm text-kkj-text-muted">
              이 조건/시장 조합에 신호가 없습니다. 사이드바에서 다른 설정을 선택해보세요.
            </div>
          )}

        {pickedDate && bundleQ.isLoading && (
          <div className="kkj-card p-8 text-center text-kkj-text-muted">
            묶음 통계 계산 중…
          </div>
        )}

        {bundleQ.data && bundleQ.data.n_signals === 0 && (
          <div className="kkj-card p-5 text-sm text-kkj-text-muted">
            이 날짜에는 신호가 없습니다. 다른 날짜를 선택하세요.
          </div>
        )}

        {bundleQ.data && bundleQ.data.n_signals > 0 && (
          <>
            {/* 묶음 통계 */}
            <section>
              <h2 className="font-gmarket-medium text-base text-kkj-text mb-3">
                묶음 통계{" "}
                <span className="text-sm text-kkj-text-soft">
                  추적 {config.trackDays}일 기준
                </span>
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {bundleQ.data.bundle_stats.map((s) => (
                  <div key={s.target} className="kkj-card p-4">
                    <div className="flex items-center justify-between mb-2">
                      <Pill variant="emerald">{s.target}</Pill>
                      <span className="font-gmarket-bold text-2xl text-kkj-emerald-strong">
                        {Math.round(s.hit_rate * 100)}%
                      </span>
                    </div>
                    <div className="text-xs text-kkj-text-muted space-y-0.5">
                      <div>
                        달성{" "}
                        <span className="font-mono-jb text-kkj-text">
                          {s.hit_count}/{s.total}
                        </span>
                      </div>
                      <div>
                        초과{" "}
                        <span className="font-mono-jb text-kkj-text">
                          {s.over_count}/{s.total}
                        </span>{" "}
                        · 미달{" "}
                        <span className="font-mono-jb text-kkj-text">
                          {s.miss_count}/{s.total}
                        </span>
                      </div>
                      <div>
                        평균 도달{" "}
                        <span className="font-mono-jb text-kkj-text">
                          {s.avg_days_to_hit !== null
                            ? `${s.avg_days_to_hit.toFixed(1)}일`
                            : "-"}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* 개별 종목 */}
            <section>
              <h2 className="font-gmarket-medium text-base text-kkj-text mb-3">
                개별 종목 ({bundleQ.data.n_signals})
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {bundleQ.data.individuals.map((s) => {
                  const active = pickedTicker === s.ticker;
                  return (
                    <button
                      key={s.ticker + s.signal_date}
                      onClick={() => setPickedTicker(s.ticker)}
                      className={clsx(
                        "text-left p-4 rounded-xl border transition-all kkj-focus",
                        active
                          ? "border-kkj-emerald bg-kkj-emerald-glow shadow-md"
                          : "border-kkj-border bg-kkj-card hover:border-kkj-emerald hover:bg-kkj-emerald-glow/30",
                      )}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-mono-jb text-xs text-kkj-text-muted">
                          {s.ticker}
                        </span>
                        {s.market && <Pill variant="neutral">{s.market}</Pill>}
                      </div>
                      <div className="font-gmarket-medium text-sm text-kkj-text mb-1 truncate">
                        {s.name}
                      </div>

                      {/* 실시간 시세 */}
                      <div className="mb-2">
                        <LiveQuote quote={quoteMap[s.ticker]} />
                      </div>

                      {/* 신호 당일 정보 */}
                      <div className="grid grid-cols-2 gap-x-2 gap-y-0.5 mb-2 text-[11px] font-mono-jb">
                        {s.signal_change_rate !== null && (
                          <>
                            <span className="text-kkj-text-soft">등락률</span>
                            <span
                              className={clsx(
                                "text-right",
                                s.signal_change_rate >= 0
                                  ? "text-kkj-red"
                                  : "text-kkj-blue",
                              )}
                            >
                              {s.signal_change_rate >= 0 ? "+" : ""}
                              {(s.signal_change_rate * 100).toFixed(1)}%
                            </span>
                          </>
                        )}
                        {s.signal_amount !== null && (
                          <>
                            <span className="text-kkj-text-soft">거래대금</span>
                            <span className="text-right text-kkj-text">
                              {(s.signal_amount / 1e8).toFixed(0)}억
                            </span>
                          </>
                        )}
                        {s.signal_market_cap !== null && (
                          <>
                            <span className="text-kkj-text-soft">시총</span>
                            <span className="text-right text-kkj-text">
                              {(s.signal_market_cap / 1e8).toFixed(0)}억
                            </span>
                          </>
                        )}
                        {s.entry_price !== null && (
                          <>
                            <span className="text-kkj-text-soft">진입가</span>
                            <span className="text-right text-kkj-text">
                              {s.entry_price.toLocaleString()}
                            </span>
                          </>
                        )}
                      </div>

                      {/* 테마 */}
                      {s.themes.length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-2">
                          {s.themes.slice(0, 4).map((t) => (
                            <span
                              key={t}
                              className="text-[10px] px-1.5 py-0.5 rounded bg-kkj-card-soft text-kkj-text-muted border border-kkj-border-soft"
                            >
                              {t}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* 도달 결과 */}
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(s.days_to_target).map(([k, v]) => {
                          if (v === null) {
                            return (
                              <Pill key={k} variant="red">
                                +{k}% ❌
                              </Pill>
                            );
                          }
                          if (v <= config.trackDays) {
                            return (
                              <Pill key={k} variant="emerald">
                                +{k}% {v}일
                              </Pill>
                            );
                          }
                          return (
                            <Pill key={k} variant="amber">
                              +{k}% {v}일
                            </Pill>
                          );
                        })}
                      </div>
                    </button>
                  );
                })}
              </div>
            </section>

            {/* 캔들차트 */}
            {selected && ohlcvQ.data && (
              <section>
                <h2 className="font-gmarket-medium text-base text-kkj-text mb-3">
                  {selected.name}{" "}
                  <span className="font-mono-jb text-sm text-kkj-text-muted">
                    {selected.ticker}
                  </span>{" "}
                  <span className="text-sm text-kkj-text-soft">
                    · {selected.market ?? ""}
                  </span>
                </h2>
                <CandleChart
                  rows={ohlcvQ.data.rows}
                  signals={[{ date: selected.signal_date, label: "신호" }]}
                  entryPrice={selected.entry_price}
                  targets={config.targets}
                  entryLabel={
                    selected.entry_price
                      ? `진입가 ${selected.entry_price.toLocaleString()}`
                      : undefined
                  }
                />
              </section>
            )}
          </>
        )}
      </div>
    </Shell>
  );
}
