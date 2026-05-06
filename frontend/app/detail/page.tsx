"use client";

import { useEffect, useMemo, useState } from "react";
import clsx from "clsx";

import { Shell } from "@/components/layout/Shell";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  Pill,
  SectionLabel,
} from "@/components/ui";
import { CandleChart } from "@/components/charts/CandleChart";
import { useBacktestConfig } from "@/lib/hooks/useBacktestConfig";
import {
  useTickerOhlcv,
  useTickerSignals,
  useTickerSummary,
} from "@/lib/hooks/useBacktest";

const COND_LABEL: Record<string, string> = {
  cond1: "급등주 추격형",
  cond2: "갭상승 정배열형",
};
const MARKET_LABEL: Record<string, string> = {
  all: "전체",
  KOSPI: "KOSPI",
  KOSDAQ: "KOSDAQ",
};

export default function DetailPage() {
  const { config } = useBacktestConfig();

  const targetPct = config.targets.includes(0.1)
    ? 10
    : Math.round(config.targets[0] * 100);

  const summaryQ = useTickerSummary(config, targetPct);

  const [search, setSearch] = useState("");
  const [pickedTicker, setPickedTicker] = useState<string | null>(null);

  const filtered = useMemo(() => {
    const rows = summaryQ.data?.rows ?? [];
    if (!search) return rows;
    const q = search.toLowerCase();
    return rows.filter(
      (r) => r.name.toLowerCase().includes(q) || r.ticker.includes(q),
    );
  }, [summaryQ.data, search]);

  useEffect(() => {
    if (!pickedTicker && filtered.length > 0) {
      setPickedTicker(filtered[0].ticker);
    }
  }, [filtered, pickedTicker]);

  const selected = filtered.find((r) => r.ticker === pickedTicker) ?? null;

  // MA240까지 보이게 충분히 긴 구간
  const ohlcvRange = useMemo(() => {
    if (!selected) return undefined;
    const last = new Date(selected.last_signal);
    const start = new Date(last);
    start.setDate(last.getDate() - 600);
    const end = new Date(last);
    end.setDate(last.getDate() + 60);
    return {
      start: start.toISOString().slice(0, 10),
      end: end.toISOString().slice(0, 10),
    };
  }, [selected]);

  const ohlcvQ = useTickerOhlcv(pickedTicker, ohlcvRange);
  const signalsQ = useTickerSignals(pickedTicker, config);

  const markers = useMemo(
    () =>
      (signalsQ.data ?? []).map((s) => ({
        date: s.signal_date,
        label: "신호",
      })),
    [signalsQ.data],
  );

  const recent = signalsQ.data?.[0];

  return (
    <Shell>
      <div className="space-y-6">
        <PageHeader
          eyebrow="Backtest"
          title="종목별 상세"
          description="신호가 자주 잡힌 종목의 캔들 + 신호 이력"
          trailing={
            <div className="flex flex-wrap items-center gap-2">
              <Pill variant="emerald">{COND_LABEL[config.cond] ?? config.cond}</Pill>
              <Pill variant="emerald">{MARKET_LABEL[config.market]}</Pill>
              <Pill variant="neutral">+{targetPct}% 기준</Pill>
            </div>
          }
        />

        {/* 검색 */}
        <section className="kkj-card p-5">
          <SectionLabel className="mb-2 block">검색</SectionLabel>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="종목명 또는 티커 (예: 삼성전자, 005930)"
            className="w-full rounded-lg border border-kkj-border bg-kkj-card px-3 py-2.5 text-sm font-mono-jb kkj-focus hover:border-kkj-emerald transition-colors"
          />
          <p className="mt-2 text-xs text-kkj-text-muted">
            전체 {(summaryQ.data?.rows ?? []).length.toLocaleString()}개 중{" "}
            {filtered.length.toLocaleString()}개 매칭
          </p>
        </section>

        {summaryQ.isLoading && (
          <div className="kkj-card p-8 text-center text-kkj-text-muted">
            종목 요약 계산 중…
          </div>
        )}
        {summaryQ.isError && (
          <div className="kkj-card p-5 border-l-4 border-kkj-red">
            <div className="text-sm text-kkj-red font-bold mb-1">백엔드 응답 실패</div>
            <p className="text-xs text-kkj-text-muted">{(summaryQ.error as Error).message}</p>
          </div>
        )}
        {summaryQ.data && filtered.length === 0 && (
          <div className="kkj-card p-5 text-sm text-kkj-text-muted">
            검색 결과 없음.
          </div>
        )}

        {/* 종목 리스트 */}
        {summaryQ.data && filtered.length > 0 && (
          <section>
            <h2 className="font-gmarket-medium text-base text-kkj-text mb-3">
              종목 리스트{" "}
              <span className="text-sm text-kkj-text-soft">
                상위 30 · 신호 빈도순
              </span>
            </h2>

            {/* PC 테이블 */}
            <div className="hidden sm:block kkj-card overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-kkj-card-soft border-b border-kkj-border-soft">
                    <th className="text-left px-4 py-2.5 text-[11px] font-bold uppercase tracking-wider text-kkj-text-muted">
                      티커
                    </th>
                    <th className="text-left px-4 py-2.5 text-[11px] font-bold uppercase tracking-wider text-kkj-text-muted">
                      종목명
                    </th>
                    <th className="text-left px-4 py-2.5 text-[11px] font-bold uppercase tracking-wider text-kkj-text-muted">
                      시장
                    </th>
                    <th className="text-right px-4 py-2.5 text-[11px] font-bold uppercase tracking-wider text-kkj-text-muted">
                      신호
                    </th>
                    <th className="text-right px-4 py-2.5 text-[11px] font-bold uppercase tracking-wider text-kkj-text-muted">
                      도달률
                    </th>
                    <th className="text-right px-4 py-2.5 text-[11px] font-bold uppercase tracking-wider text-kkj-text-muted">
                      최근
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.slice(0, 30).map((r) => {
                    const active = pickedTicker === r.ticker;
                    return (
                      <tr
                        key={r.ticker}
                        onClick={() => setPickedTicker(r.ticker)}
                        className={clsx(
                          "border-b border-kkj-border-soft last:border-0 cursor-pointer transition-colors",
                          active ? "bg-kkj-emerald-glow" : "hover:bg-kkj-card-soft",
                        )}
                      >
                        <td className="px-4 py-2.5 font-mono-jb text-xs text-kkj-text-muted">
                          {r.ticker}
                        </td>
                        <td className="px-4 py-2.5 text-kkj-text">{r.name}</td>
                        <td className="px-4 py-2.5">
                          <Pill variant="neutral">{r.market}</Pill>
                        </td>
                        <td className="px-4 py-2.5 text-right font-mono-jb text-kkj-text">
                          {r.n_signals}회
                        </td>
                        <td className="px-4 py-2.5 text-right font-gmarket-bold text-kkj-emerald-strong">
                          {Math.round(r.hit_rate * 100)}%
                        </td>
                        <td className="px-4 py-2.5 text-right font-mono-jb text-xs text-kkj-text-muted">
                          {r.last_signal}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* 모바일 카드 */}
            <div className="grid grid-cols-1 gap-2.5 sm:hidden">
              {filtered.slice(0, 30).map((r) => {
                const active = pickedTicker === r.ticker;
                return (
                  <button
                    key={r.ticker}
                    onClick={() => setPickedTicker(r.ticker)}
                    className={clsx(
                      "text-left p-4 rounded-xl border transition-all kkj-focus",
                      active
                        ? "border-kkj-emerald bg-kkj-emerald-glow"
                        : "border-kkj-border bg-kkj-card hover:border-kkj-emerald",
                    )}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono-jb text-xs text-kkj-text-muted">
                        {r.ticker}
                      </span>
                      <Pill variant="neutral">{r.market}</Pill>
                    </div>
                    <div className="font-gmarket-medium text-sm text-kkj-text mb-2 truncate">
                      {r.name}
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-kkj-text-muted">
                        신호{" "}
                        <span className="font-mono-jb text-kkj-text">
                          {r.n_signals}회
                        </span>{" "}
                        · 최근{" "}
                        <span className="font-mono-jb">{r.last_signal}</span>
                      </span>
                      <span className="font-gmarket-bold text-kkj-emerald-strong">
                        {Math.round(r.hit_rate * 100)}%
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </section>
        )}

        {/* 캔들차트 */}
        {selected && ohlcvQ.data && (
          <section>
            <h2 className="font-gmarket-medium text-base text-kkj-text mb-3">
              {selected.name}{" "}
              <span className="font-mono-jb text-sm text-kkj-text-muted">
                {selected.ticker}
              </span>{" "}
              <span className="text-sm text-kkj-text-soft">
                · {selected.market}
              </span>
            </h2>
            <CandleChart
              rows={ohlcvQ.data.rows}
              signals={markers}
              entryPrice={recent?.entry_price ?? null}
              targets={config.targets}
              entryLabel={
                recent?.entry_price
                  ? `최근 진입가 ${recent.entry_price.toLocaleString()}`
                  : undefined
              }
            />
          </section>
        )}

        {/* 신호 이력 */}
        {selected && signalsQ.data && signalsQ.data.length > 0 && (
          <section>
            <h2 className="font-gmarket-medium text-base text-kkj-text mb-3">
              신호 이력 ({signalsQ.data.length})
            </h2>
            <div className="kkj-card overflow-x-auto">
              <table className="w-full text-sm min-w-[560px]">
                <thead>
                  <tr className="bg-kkj-card-soft border-b border-kkj-border-soft">
                    <th className="text-left px-3 py-2.5 text-[11px] font-bold uppercase tracking-wider text-kkj-text-muted">
                      신호일
                    </th>
                    <th className="text-left px-3 py-2.5 text-[11px] font-bold uppercase tracking-wider text-kkj-text-muted">
                      진입가
                    </th>
                    {config.targets.map((t) => (
                      <th
                        key={t}
                        className="text-center px-3 py-2.5 text-[11px] font-bold uppercase tracking-wider text-kkj-text-muted"
                      >
                        +{Math.round(t * 100)}%
                      </th>
                    ))}
                    <th className="text-right px-3 py-2.5 text-[11px] font-bold uppercase tracking-wider text-kkj-text-muted">
                      MDD
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {signalsQ.data.map((s) => (
                    <tr
                      key={s.signal_date}
                      className="border-b border-kkj-border-soft last:border-0"
                    >
                      <td className="px-3 py-2.5 font-mono-jb text-kkj-text">
                        {s.signal_date}
                      </td>
                      <td className="px-3 py-2.5 font-mono-jb text-kkj-text">
                        {s.entry_price !== null ? s.entry_price.toLocaleString() : "-"}
                      </td>
                      {config.targets.map((t) => {
                        const v = s.days_to_target[String(Math.round(t * 100))];
                        return (
                          <td key={t} className="px-3 py-2.5 text-center">
                            {v === null ? (
                              <span className="text-kkj-text-soft">❌</span>
                            ) : v <= config.trackDays ? (
                              <Pill variant="emerald">{v}일</Pill>
                            ) : (
                              <Pill variant="amber">{v}일</Pill>
                            )}
                          </td>
                        );
                      })}
                      <td className="px-3 py-2.5 text-right font-mono-jb text-kkj-blue">
                        {s.mdd !== null ? `${(s.mdd * 100).toFixed(1)}%` : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>
    </Shell>
  );
}
