"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { BacktestConfig } from "./useBacktestConfig";

export function useBacktest(cfg: BacktestConfig) {
  return useQuery({
    queryKey: [
      "backtest",
      cfg.cond,
      cfg.market,
      cfg.entry,
      cfg.trackDays,
      cfg.extraDays,
      cfg.targetsCsv,
    ],
    queryFn: () =>
      api.backtest({
        condition: cfg.cond,
        market: cfg.market,
        entry: cfg.entry,
        track_days: cfg.trackDays,
        extra_days: cfg.extraDays,
        targets: cfg.targets,
      }),
  });
}

export function useSignalDates(cfg: BacktestConfig) {
  return useQuery({
    queryKey: [
      "signal-dates",
      cfg.cond,
      cfg.market,
      cfg.entry,
      cfg.trackDays,
      cfg.extraDays,
      cfg.targetsCsv,
    ],
    queryFn: () =>
      api.signalDates({
        condition: cfg.cond,
        market: cfg.market,
        entry: cfg.entry,
        track_days: cfg.trackDays,
        extra_days: cfg.extraDays,
        targets: cfg.targetsCsv,
      }),
  });
}

export function useDateBundle(cfg: BacktestConfig, date: string | null) {
  return useQuery({
    queryKey: [
      "date-bundle",
      cfg.cond,
      cfg.market,
      cfg.entry,
      cfg.trackDays,
      cfg.extraDays,
      cfg.targetsCsv,
      date,
    ],
    queryFn: () =>
      api.dateBundle({
        date: date!,
        condition: cfg.cond,
        market: cfg.market,
        entry: cfg.entry,
        track_days: cfg.trackDays,
        extra_days: cfg.extraDays,
        targets: cfg.targetsCsv,
      }),
    enabled: Boolean(date),
  });
}

export function useRegimeComparison(cfg: BacktestConfig) {
  return useQuery({
    queryKey: [
      "regime-comparison",
      cfg.cond,
      cfg.market,
      cfg.entry,
      cfg.trackDays,
      cfg.extraDays,
      cfg.targetsCsv,
    ],
    queryFn: () =>
      api.regimeComparison({
        condition: cfg.cond,
        market: cfg.market,
        entry: cfg.entry,
        track_days: cfg.trackDays,
        extra_days: cfg.extraDays,
        targets: cfg.targetsCsv,
      }),
  });
}

export function useTickerSummary(cfg: BacktestConfig, targetPct = 10) {
  return useQuery({
    queryKey: [
      "ticker-summary",
      cfg.cond,
      cfg.market,
      cfg.entry,
      cfg.trackDays,
      cfg.extraDays,
      targetPct,
    ],
    queryFn: () =>
      api.tickerSummary({
        condition: cfg.cond,
        market: cfg.market,
        entry: cfg.entry,
        track_days: cfg.trackDays,
        extra_days: cfg.extraDays,
        target_pct: targetPct,
      }),
  });
}

export function useTickerOhlcv(
  ticker: string | null,
  range?: { start?: string; end?: string },
) {
  return useQuery({
    queryKey: ["ticker-ohlcv", ticker, range?.start, range?.end],
    queryFn: () => api.tickerOhlcv(ticker!, range),
    enabled: Boolean(ticker),
  });
}

export function useTickerSignals(
  ticker: string | null,
  cfg: BacktestConfig,
) {
  return useQuery({
    queryKey: [
      "ticker-signals",
      ticker,
      cfg.cond,
      cfg.market,
      cfg.entry,
      cfg.trackDays,
      cfg.extraDays,
      cfg.targetsCsv,
    ],
    queryFn: () =>
      api.tickerSignals(ticker!, {
        condition: cfg.cond,
        market: cfg.market,
        entry: cfg.entry,
        track_days: cfg.trackDays,
        extra_days: cfg.extraDays,
        targets: cfg.targetsCsv,
      }),
    enabled: Boolean(ticker),
  });
}

export function useKospi(start: string, end: string, maWindow = 60) {
  return useQuery({
    queryKey: ["kospi", start, end, maWindow],
    queryFn: () => api.kospi({ start, end, ma_window: maWindow }),
    enabled: Boolean(start && end),
  });
}

export function useThemes() {
  return useQuery({
    queryKey: ["themes"],
    queryFn: () => api.themes(),
  });
}

export function useThemeDetail(id: string | null) {
  return useQuery({
    queryKey: ["theme", id],
    queryFn: () => api.themeDetail(id!),
    enabled: Boolean(id),
  });
}
