"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import clsx from "clsx";

import { Shell } from "@/components/layout/Shell";
import { PageHeader } from "@/components/layout/PageHeader";
import { Pill, SectionLabel } from "@/components/ui";
import { LiveQuote } from "@/components/ui/LiveQuote";
import { useQuotes, quotesByTicker } from "@/lib/hooks/useQuotes";
import {
  useCondSearchList,
  useCondSearchTickers,
} from "@/lib/hooks/useCondSearch";

/** 시총(억원 단위) → "1,578조" 또는 "8,432억" 같은 표기. */
function fmtMarketCap(mac: number | null | undefined): string {
  if (!mac || mac <= 0) return "-";
  if (mac >= 10000) return `${(mac / 10000).toFixed(1)}조`;
  return `${Math.round(mac).toLocaleString()}억`;
}

/** 거래대금(원 단위) → "1.2조" / "5,432억" / "82억" / "3,500만" 같은 표기. */
function fmtAmount(won: number | null | undefined): string {
  if (!won || won <= 0) return "-";
  if (won >= 1e12) return `${(won / 1e12).toFixed(1)}조`;
  if (won >= 1e8) return `${Math.round(won / 1e8).toLocaleString()}억`;
  if (won >= 1e4) return `${Math.round(won / 1e4).toLocaleString()}만`;
  return `${won.toLocaleString()}원`;
}

const LS_KEY = "live:cond-idx";

export default function LivePage() {
  const listQ = useCondSearchList();

  // 마지막에 본 조건식 idx 복원
  const [pickedIdx, setPickedIdx] = useState<string | null>(null);
  useEffect(() => {
    if (typeof window === "undefined") return;
    const saved = window.localStorage.getItem(LS_KEY);
    if (saved) setPickedIdx(saved);
  }, []);
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (pickedIdx) window.localStorage.setItem(LS_KEY, pickedIdx);
  }, [pickedIdx]);

  // 조건식 목록 받으면 첫 번째 자동 선택 (저장된 게 있으면 유지)
  useEffect(() => {
    if (!pickedIdx && listQ.data && listQ.data.length > 0) {
      setPickedIdx(listQ.data[0].idx);
    }
  }, [listQ.data, pickedIdx]);

  const tickersQ = useCondSearchTickers(pickedIdx);

  // 신규 진입 / 이탈 추적 — prev 를 Map(ticker → name) 으로 보관해야 이탈 시 이름이 남음
  const prevMap = useRef<Map<string, string>>(new Map());
  const [recentlyAdded, setRecentlyAdded] = useState<Set<string>>(new Set());
  const [recentlyRemoved, setRecentlyRemoved] = useState<Map<string, string>>(
    new Map(),
  );

  useEffect(() => {
    if (!tickersQ.data) return;
    const curMap = new Map<string, string>(
      tickersQ.data.tickers.map((t) => [t.ticker, t.name]),
    );
    const added = new Set<string>();
    const removed = new Map<string, string>();
    for (const t of curMap.keys()) if (!prevMap.current.has(t)) added.add(t);
    for (const [t, name] of prevMap.current) {
      if (!curMap.has(t)) removed.set(t, name); // 이전에 알던 이름 유지
    }
    if (added.size) {
      setRecentlyAdded((prev) => new Set([...prev, ...added]));
      setTimeout(() => {
        setRecentlyAdded((prev) => {
          const n = new Set(prev);
          for (const t of added) n.delete(t);
          return n;
        });
      }, 8000);
    }
    if (removed.size) {
      setRecentlyRemoved((prev) => {
        const n = new Map(prev);
        for (const [k, v] of removed) n.set(k, v);
        return n;
      });
      setTimeout(() => {
        setRecentlyRemoved((prev) => {
          const n = new Map(prev);
          for (const k of removed.keys()) n.delete(k);
          return n;
        });
      }, 8000);
    }
    prevMap.current = curMap;
  }, [tickersQ.data]);

  const tickers = tickersQ.data?.tickers ?? [];
  const liveTickerCodes = useMemo(() => tickers.map((t) => t.ticker), [tickers]);
  const quotesQ = useQuotes(liveTickerCodes);
  const quoteMap = useMemo(() => quotesByTicker(quotesQ.data), [quotesQ.data]);

  const fetchedSec = tickersQ.data
    ? new Date(tickersQ.data.fetched_at * 1000).toLocaleTimeString("ko-KR")
    : null;

  return (
    <Shell>
      <div className="space-y-6">
        <PageHeader
          eyebrow="Live"
          title="장중 실시간 조건검색"
          description="키움 영웅문에 등록된 조건식을 5초마다 폴링 — 떴다 사라졌다 보임"
          trailing={
            <div className="flex flex-wrap items-center gap-2">
              {fetchedSec && (
                <Pill variant="emerald">갱신 {fetchedSec}</Pill>
              )}
              <Pill variant="neutral">
                현재 {tickers.length}종목
              </Pill>
            </div>
          }
        />

        {/* 조건식 선택 */}
        <section className="kkj-card p-5">
          <SectionLabel className="mb-2 block">조건식</SectionLabel>
          {listQ.isLoading && (
            <p className="text-sm text-kkj-text-muted">목록 가져오는 중…</p>
          )}
          {listQ.isError && (
            <p className="text-sm text-kkj-red">
              조건검색 목록 실패: {(listQ.error as Error).message}
            </p>
          )}
          {listQ.data && (
            <select
              value={pickedIdx ?? ""}
              onChange={(e) => setPickedIdx(e.target.value || null)}
              className="w-full rounded-lg border border-kkj-border bg-kkj-card px-3 py-2 text-sm kkj-focus hover:border-kkj-emerald transition-colors"
            >
              {listQ.data.map((c) => (
                <option key={c.idx} value={c.idx}>
                  [{c.idx}] {c.name}
                </option>
              ))}
            </select>
          )}
        </section>

        {/* 카드 */}
        {tickersQ.isLoading && (
          <div className="kkj-card p-8 text-center text-kkj-text-muted">
            조건 만족 종목 가져오는 중…
          </div>
        )}
        {tickersQ.isError && (
          <div className="kkj-card p-5 border-l-4 border-kkj-red">
            <div className="text-sm text-kkj-red font-bold mb-1">조회 실패</div>
            <p className="text-xs text-kkj-text-muted">
              {(tickersQ.error as Error).message}
            </p>
          </div>
        )}
        {tickersQ.data && tickers.length === 0 && (
          <div className="kkj-card p-8 text-center text-sm text-kkj-text-muted">
            지금 이 조건을 만족하는 종목이 없어요. 5초마다 자동으로 다시 확인해요.
          </div>
        )}

        {tickers.length > 0 && (
          <section>
            <h2 className="font-gmarket-medium text-base text-kkj-text mb-3">
              만족 종목 ({tickers.length})
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {tickers.map((t) => {
                const isNew = recentlyAdded.has(t.ticker);
                const q = quoteMap[t.ticker];
                return (
                  <div
                    key={t.ticker}
                    className={clsx(
                      "p-4 rounded-xl border bg-kkj-card transition-all",
                      isNew
                        ? "border-kkj-emerald shadow-md ring-2 ring-kkj-emerald/30"
                        : "border-kkj-border",
                    )}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-mono-jb text-xs text-kkj-text-muted">
                        {t.ticker}
                      </span>
                      {isNew && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-kkj-emerald text-white font-bold">
                          NEW
                        </span>
                      )}
                    </div>
                    <div className="font-gmarket-medium text-sm text-kkj-text mb-2 truncate">
                      {t.name || "—"}
                    </div>

                    {/* 테마 */}
                    {t.themes && t.themes.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-2">
                        {t.themes.slice(0, 4).map((th) => (
                          <span
                            key={th}
                            className="text-[10px] px-1.5 py-0.5 rounded bg-kkj-card-soft text-kkj-text-muted border border-kkj-border-soft"
                          >
                            {th}
                          </span>
                        ))}
                      </div>
                    )}

                    <LiveQuote quote={q} />
                    {/* 거래대금 / 시총 */}
                    <div className="grid grid-cols-2 gap-x-2 gap-y-0.5 mt-2 text-[11px] font-mono-jb">
                      <span className="text-kkj-text-soft">거래대금</span>
                      <span className="text-right text-kkj-text">
                        {fmtAmount(q?.amount)}
                      </span>
                      <span className="text-kkj-text-soft">시총</span>
                      <span className="text-right text-kkj-text">
                        {fmtMarketCap(q?.market_cap)}
                      </span>
                      {q?.volume_pre_rate !== undefined &&
                        q?.volume_pre_rate !== null && (
                          <>
                            <span className="text-kkj-text-soft">거래량 전일비</span>
                            <span
                              className={clsx(
                                "text-right",
                                q.volume_pre_rate > 0
                                  ? "text-kkj-red"
                                  : q.volume_pre_rate < 0
                                    ? "text-kkj-blue"
                                    : "text-kkj-text",
                              )}
                            >
                              {q.volume_pre_rate > 0 ? "+" : ""}
                              {q.volume_pre_rate.toFixed(0)}%
                            </span>
                          </>
                        )}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* 이탈 종목 (잠깐 보여줬다 사라짐) */}
        {recentlyRemoved.size > 0 && (
          <section>
            <h2 className="font-gmarket-medium text-base text-kkj-text-muted mb-2">
              방금 이탈 ({recentlyRemoved.size})
            </h2>
            <div className="flex flex-wrap gap-2">
              {Array.from(recentlyRemoved.entries()).map(([code, name]) => (
                <span
                  key={code}
                  className="text-xs px-2.5 py-1 rounded-full bg-kkj-card-soft text-kkj-text-soft border border-kkj-border-soft line-through"
                >
                  {name || code}
                </span>
              ))}
            </div>
          </section>
        )}
      </div>
    </Shell>
  );
}
