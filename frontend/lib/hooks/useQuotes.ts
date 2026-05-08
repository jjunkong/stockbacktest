"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Quote } from "@/lib/api-types";

const POLL_MS = 2000; // 2초 폴링 — 키움 분당 한도 고려

/**
 * 다수 종목 실시간 시세. 2초마다 자동 갱신.
 * tickers 가 비어있으면 호출 안 함.
 */
export function useQuotes(tickers: string[]) {
  const sorted = [...new Set(tickers)].sort();
  return useQuery<Quote[]>({
    queryKey: ["quotes", sorted.join(",")],
    queryFn: () => api.quotes(sorted),
    enabled: sorted.length > 0,
    refetchInterval: POLL_MS,
    refetchIntervalInBackground: false,
    staleTime: 0,
  });
}

/** 시세 배열 → 티커별 빠른 lookup map. */
export function quotesByTicker(quotes: Quote[] | undefined): Record<string, Quote> {
  const out: Record<string, Quote> = {};
  for (const q of quotes ?? []) out[q.ticker] = q;
  return out;
}
