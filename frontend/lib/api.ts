/**
 * 백엔드 API 클라이언트. fetch 기반 + 타입 안전.
 */
import type {
  BacktestRequest,
  BacktestResponse,
  ConditionInfo,
  DateBundleResponse,
  EntryInfo,
  HealthResponse,
  KospiResponse,
  MarketInfo,
  RegimeComparisonResponse,
  SignalResult,
  ThemeDetailResponse,
  ThemeSummary,
  TickerOHLCVResponse,
  TickerSummaryResponse,
} from "./api-types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

async function request<T>(
  path: string,
  init?: RequestInit & { searchParams?: Record<string, string | number | undefined> },
): Promise<T> {
  const { searchParams, ...rest } = init ?? {};
  let url = `${BASE_URL}${path}`;
  if (searchParams) {
    const qs = new URLSearchParams();
    Object.entries(searchParams).forEach(([k, v]) => {
      if (v !== undefined && v !== null) qs.append(k, String(v));
    });
    const s = qs.toString();
    if (s) url += `?${s}`;
  }

  const res = await fetch(url, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(rest.headers ?? {}),
    },
  });
  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      // ignore
    }
    throw new ApiError(`API ${res.status} ${path}`, res.status, body);
  }
  return res.json() as Promise<T>;
}

// ===== 메타 =====
export const api = {
  health: () => request<HealthResponse>("/health"),
  conditions: () => request<ConditionInfo[]>("/conditions"),
  markets: () => request<MarketInfo[]>("/markets"),
  entryOptions: () => request<EntryInfo[]>("/entry-options"),

  // ===== 백테스트 =====
  backtest: (req: BacktestRequest) =>
    request<BacktestResponse>("/backtest", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  signalDates: (params: {
    condition: string;
    market?: string;
    entry?: string;
    track_days?: number;
    extra_days?: number;
    targets?: string;
  }) => request<string[]>("/backtest/signal-dates", { searchParams: params }),

  dateBundle: (params: {
    date: string;
    condition: string;
    market?: string;
    entry?: string;
    track_days?: number;
    extra_days?: number;
    targets?: string;
  }) => request<DateBundleResponse>("/backtest/date-bundle", { searchParams: params }),

  regimeComparison: (params: {
    condition: string;
    market?: string;
    entry?: string;
    track_days?: number;
    extra_days?: number;
    targets?: string;
    ma_window?: number;
  }) => request<RegimeComparisonResponse>("/backtest/regime-comparison", {
    searchParams: params,
  }),

  tickerSummary: (params: {
    condition: string;
    market?: string;
    entry?: string;
    track_days?: number;
    extra_days?: number;
    target_pct?: number;
  }) => request<TickerSummaryResponse>("/backtest/ticker-summary", { searchParams: params }),

  // ===== 종목 =====
  tickerOhlcv: (
    ticker: string,
    params?: { start?: string; end?: string },
  ) => request<TickerOHLCVResponse>(`/tickers/${ticker}/ohlcv`, {
    searchParams: params,
  }),

  tickerSignals: (
    ticker: string,
    params: {
      condition: string;
      market?: string;
      entry?: string;
      track_days?: number;
      extra_days?: number;
      targets?: string;
    },
  ) => request<SignalResult[]>(`/tickers/${ticker}/signals`, { searchParams: params }),

  // ===== 코스피 =====
  kospi: (params: { start: string; end: string; ma_window?: number }) =>
    request<KospiResponse>("/kospi", { searchParams: params }),

  // ===== 테마 =====
  themes: () => request<ThemeSummary[]>("/themes"),
  themeDetail: (id: string) => request<ThemeDetailResponse>(`/themes/${id}`),
};

export { ApiError };
