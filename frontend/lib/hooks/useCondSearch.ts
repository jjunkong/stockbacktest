"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export function useCondSearchList() {
  return useQuery({
    queryKey: ["cond-search-list"],
    queryFn: () => api.condSearchList(),
    staleTime: 60 * 1000, // 1분 - 영웅문 조건식 목록은 자주 안 바뀜
  });
}

/** 만족 종목 — 5초마다 자동 갱신 (백엔드도 5초 TTL). */
export function useCondSearchTickers(idx: string | null) {
  return useQuery({
    queryKey: ["cond-search-tickers", idx],
    queryFn: () => (idx ? api.condSearchTickers(idx) : Promise.reject()),
    enabled: !!idx,
    refetchInterval: 5000,
    refetchIntervalInBackground: false,
    staleTime: 0,
  });
}
