"use client";

import { useEffect, useMemo, useState } from "react";
import clsx from "clsx";

import { Shell } from "@/components/layout/Shell";
import { PageHeader } from "@/components/layout/PageHeader";
import { Pill, SectionLabel } from "@/components/ui";
import { CandleChart } from "@/components/charts/CandleChart";
import {
  useThemeDetail,
  useThemes,
  useTickerOhlcv,
} from "@/lib/hooks/useBacktest";
import type { ThemeStock } from "@/lib/api-types";

function fmtAmount(v: number | null): string {
  if (v === null) return "-";
  if (v >= 1e12) return `${(v / 1e12).toFixed(1)}조`;
  if (v >= 1e8) return `${(v / 1e8).toFixed(0)}억`;
  return v.toLocaleString();
}

function fmtChange(v: number | null): { text: string; tone: "up" | "down" | "flat" } {
  if (v === null) return { text: "-", tone: "flat" };
  const pct = v * 100;
  const tone = pct > 0 ? "up" : pct < 0 ? "down" : "flat";
  return { text: `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`, tone };
}

interface StockCardProps {
  stock: ThemeStock;
  active: boolean;
  onClick: () => void;
}

function StockCard({ stock, active, onClick }: StockCardProps) {
  const change = fmtChange(stock.last_change_rate);
  const changeColor =
    change.tone === "up"
      ? "text-kkj-red"
      : change.tone === "down"
        ? "text-kkj-blue"
        : "text-kkj-text-muted";

  return (
    <button
      onClick={onClick}
      className={clsx(
        "text-left p-3 rounded-lg border transition-all kkj-focus",
        active
          ? "border-kkj-emerald bg-kkj-emerald-glow shadow-md"
          : "border-kkj-border bg-kkj-card hover:border-kkj-emerald hover:bg-kkj-emerald-glow/30",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono-jb text-[11px] text-kkj-text-muted">
              {stock.ticker}
            </span>
            {stock.market && <Pill variant="neutral">{stock.market}</Pill>}
            {stock.is_leader && <Pill variant="emerald">주도주</Pill>}
          </div>
          <div className="font-gmarket-medium text-sm text-kkj-text truncate">
            {stock.name}
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className={clsx("font-gmarket-bold text-sm", changeColor)}>
            {change.text}
          </div>
          <div className="font-mono-jb text-[11px] text-kkj-text-muted mt-0.5">
            {fmtAmount(stock.last_amount)}
          </div>
        </div>
      </div>
    </button>
  );
}

export default function ThemesPage() {
  const themesQ = useThemes();
  const [pickedId, setPickedId] = useState<string | null>(null);
  const [pickedTicker, setPickedTicker] = useState<string | null>(null);

  useEffect(() => {
    if (!pickedId && themesQ.data && themesQ.data.length > 0) {
      setPickedId(themesQ.data[0].id);
    }
  }, [themesQ.data, pickedId]);

  const detailQ = useThemeDetail(pickedId);

  // 테마 변경 시 첫 주도주 자동 선택
  useEffect(() => {
    if (detailQ.data) {
      const all = [...detailQ.data.leaders, ...detailQ.data.related];
      if (all.length > 0) {
        setPickedTicker(all[0].ticker);
      } else {
        setPickedTicker(null);
      }
    }
  }, [detailQ.data]);

  const selectedStock = useMemo(() => {
    if (!detailQ.data || !pickedTicker) return null;
    const all = [...detailQ.data.leaders, ...detailQ.data.related];
    return all.find((s) => s.ticker === pickedTicker) ?? null;
  }, [detailQ.data, pickedTicker]);

  // 캔들차트용 OHLCV — 최근 1.5년치 정도 (MA240 표시 위해)
  const ohlcvRange = useMemo(() => {
    if (!selectedStock) return undefined;
    const end = new Date();
    const start = new Date(end);
    start.setDate(end.getDate() - 540);
    return {
      start: start.toISOString().slice(0, 10),
      end: end.toISOString().slice(0, 10),
    };
  }, [selectedStock]);

  const ohlcvQ = useTickerOhlcv(pickedTicker, ohlcvRange);

  return (
    <Shell>
      <div className="space-y-6">
        <PageHeader
          eyebrow="Themes"
          title="테마/산업"
          description="테마를 선택하고 종목 카드를 클릭하면 캔들차트가 아래에 펼쳐집니다"
          trailing={<Pill variant="neutral">{(themesQ.data ?? []).length}개 테마</Pill>}
        />

        {/* 테마 칩 */}
        <section>
          <SectionLabel className="mb-3 block">테마 선택</SectionLabel>
          {themesQ.isLoading ? (
            <div className="kkj-card p-5 text-sm text-kkj-text-muted">
              테마 목록 가져오는 중…
            </div>
          ) : themesQ.isError ? (
            <div className="kkj-card p-5 border-l-4 border-kkj-red">
              <div className="text-sm text-kkj-red font-bold mb-1">
                백엔드 응답 실패
              </div>
              <p className="text-xs text-kkj-text-muted">
                {(themesQ.error as Error).message}
              </p>
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {(themesQ.data ?? []).map((t) => {
                const active = pickedId === t.id;
                return (
                  <button
                    key={t.id}
                    onClick={() => setPickedId(t.id)}
                    title={t.description}
                    className={clsx(
                      "px-3 py-2 rounded-lg text-sm font-gmarket-medium border transition-all kkj-focus",
                      active
                        ? "bg-kkj-emerald text-white border-kkj-emerald shadow-md"
                        : "bg-kkj-card text-kkj-text border-kkj-border hover:border-kkj-emerald hover:bg-kkj-emerald-glow",
                    )}
                  >
                    {t.name}
                    <span
                      className={clsx(
                        "ml-1.5 text-[11px] font-mono-jb",
                        active ? "text-white/80" : "text-kkj-text-soft",
                      )}
                    >
                      {t.n_leaders + t.n_related}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </section>

        {/* 테마 상세 */}
        {detailQ.isLoading && (
          <div className="kkj-card p-8 text-center text-kkj-text-muted">
            테마 상세 가져오는 중…
          </div>
        )}

        {detailQ.data && (
          <>
            {/* 헤더 */}
            <section className="kkj-card-emerald p-5 flex items-center justify-between flex-wrap gap-3">
              <div>
                <h2 className="font-gmarket-bold text-2xl text-kkj-text">
                  {detailQ.data.name}
                </h2>
                {detailQ.data.description && (
                  <p className="text-sm text-kkj-text-muted mt-1">
                    {detailQ.data.description}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2 text-xs text-kkj-text-soft">
                {(detailQ.data.leaders[0]?.last_date ||
                  detailQ.data.related[0]?.last_date) && (
                  <span className="font-mono-jb">
                    기준일{" "}
                    {detailQ.data.leaders[0]?.last_date ||
                      detailQ.data.related[0]?.last_date}
                  </span>
                )}
                <Pill variant="emerald">
                  주도 {detailQ.data.leaders.length}
                </Pill>
                <Pill variant="neutral">관련 {detailQ.data.related.length}</Pill>
              </div>
            </section>

            {/* 주도주 */}
            <section>
              <h3 className="font-gmarket-medium text-base text-kkj-text mb-3">
                주도주 (대장주)
              </h3>
              {detailQ.data.leaders.length === 0 ? (
                <p className="kkj-card p-5 text-sm text-kkj-text-muted">
                  등록된 주도주 없음
                </p>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {detailQ.data.leaders.map((s) => (
                    <StockCard
                      key={s.ticker}
                      stock={s}
                      active={pickedTicker === s.ticker}
                      onClick={() => setPickedTicker(s.ticker)}
                    />
                  ))}
                </div>
              )}
            </section>

            {/* 관련주 */}
            <section>
              <h3 className="font-gmarket-medium text-base text-kkj-text mb-3">
                관련주
              </h3>
              {detailQ.data.related.length === 0 ? (
                <p className="kkj-card p-5 text-sm text-kkj-text-muted">
                  등록된 관련주 없음
                </p>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                  {detailQ.data.related.map((s) => (
                    <StockCard
                      key={s.ticker}
                      stock={s}
                      active={pickedTicker === s.ticker}
                      onClick={() => setPickedTicker(s.ticker)}
                    />
                  ))}
                </div>
              )}
            </section>

            {/* 인라인 캔들차트 */}
            {selectedStock && (
              <section>
                <h3 className="font-gmarket-medium text-base text-kkj-text mb-3">
                  {selectedStock.name}{" "}
                  <span className="font-mono-jb text-sm text-kkj-text-muted">
                    {selectedStock.ticker}
                  </span>{" "}
                  <span className="text-sm text-kkj-text-soft">
                    · {selectedStock.market}
                  </span>
                </h3>
                {ohlcvQ.isLoading && (
                  <div className="kkj-card p-8 text-center text-kkj-text-muted">
                    차트 불러오는 중…
                  </div>
                )}
                {ohlcvQ.data && (
                  <CandleChart
                    rows={ohlcvQ.data.rows}
                    height={500}
                  />
                )}
              </section>
            )}

            <p className="text-xs text-kkj-text-soft pt-4 border-t border-kkj-border-soft">
              ※ 테마 매핑은 수동 큐레이션 (data/themes.json). 종목별 등락률/거래대금은 데이터 cache의 최근 거래일 기준 — 매일 데이터 갱신 시 자동 반영.
            </p>
          </>
        )}
      </div>
    </Shell>
  );
}
