/**
 * 백엔드 API 응답 타입 (backend/app/schemas와 동기화).
 */

/** 동적 조건식 ID — cond1, cond2, kiwoom_131 등 백엔드가 노출하는 모든 ID. */
export type ConditionId = string;
export type MarketId = "all" | "KOSPI" | "KOSDAQ";
export type EntryOption = "close_today" | "open_next" | "close_next";

export interface ConditionInfo {
  id: string;
  label: string;
}

export interface MarketInfo {
  id: string;
  label: string;
}

export interface EntryInfo {
  id: string;
  label: string;
}

export interface HealthResponse {
  status: string;
  cache_ready: boolean;
  n_tickers: number;
  n_signals: number;
}

export interface BacktestRequest {
  condition: ConditionId;
  market: MarketId;
  entry: EntryOption;
  track_days: number;
  extra_days: number;
  targets: number[];
}

export interface MatrixRow {
  target: string;
  n_signals: number;
  in_track_rate: number;
  over_track_rate: number;
  miss_rate: number;
  avg_days_to_hit: number | null;
  avg_mdd_on_miss: number | null;
  avg_pnl_on_miss: number | null;
  /** P(끝까지 미달성 | 1일차에 미도달) */
  miss_rate_no_day1: number | null;
}

export interface SignalResult {
  ticker: string;
  name: string;
  market: string | null;
  condition: string;
  signal_date: string;
  entry_date: string | null;
  entry_price: number | null;
  days_to_target: Record<string, number | null>;
  mdd: number | null;
  final_pnl: number | null;
  skipped: string | null;
  // 신호 발생일 보조 정보
  signal_close: number | null;
  signal_change_rate: number | null;
  signal_volume: number | null;
  signal_amount: number | null;
  signal_market_cap: number | null;
  themes: string[];
}

export interface ThemeSummary {
  id: string;
  name: string;
  description: string;
  n_leaders: number;
  n_related: number;
}

export interface ThemeStock {
  ticker: string;
  name: string;
  market: string | null;
  is_leader: boolean;
  market_cap: number | null;
  last_close: number | null;
  last_date: string | null;
  last_change_rate: number | null;
  last_amount: number | null;
}

export interface ThemeDetailResponse {
  id: string;
  name: string;
  description: string;
  leaders: ThemeStock[];
  related: ThemeStock[];
}

export interface BacktestResponse {
  condition: string;
  condition_label: string;
  market: string;
  entry: string;
  entry_label: string;
  track_days: number;
  extra_days: number;
  targets: number[];
  n_signals: number;
  avg_hit_rate: number;
  matrix: MatrixRow[];
}

export interface DateBundleStat {
  target: string;
  hit_count: number;
  over_count: number;
  miss_count: number;
  total: number;
  hit_rate: number;
  avg_days_to_hit: number | null;
}

export interface DateBundleResponse {
  date: string;
  n_signals: number;
  bundle_stats: DateBundleStat[];
  individuals: SignalResult[];
}

export interface RegimeMatrix {
  regime: string;
  regime_label: string;
  n_signals: number;
  rows: MatrixRow[];
}

export interface RegimeComparisonResponse {
  condition: string;
  market: string;
  entry: string;
  track_days: number;
  distribution: Record<string, number>;
  regimes: RegimeMatrix[];
}

export interface TickerSummaryRow {
  ticker: string;
  name: string;
  market: string | null;
  n_signals: number;
  n_hit: number;
  hit_rate: number;
  last_signal: string;
}

export interface TickerSummaryResponse {
  target_pct: number;
  track_days: number;
  rows: TickerSummaryRow[];
}

export interface OHLCVRow {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  change_rate: number | null;
}

export interface TickerOHLCVResponse {
  ticker: string;
  name: string;
  market: string | null;
  rows: OHLCVRow[];
}

export interface KospiRow {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  change_rate: number | null;
  ma: number | null;
  regime: string;
}

export interface KospiResponse {
  ma_window: number;
  rows: KospiRow[];
}

export interface Quote {
  ticker: string;
  name?: string | null;
  current_price?: number | null;
  change?: number | null;
  change_rate?: number | null;
  open?: number | null;
  high?: number | null;
  low?: number | null;
  base_price?: number | null;
  /** 당일 누적 거래량 (주) */
  volume?: number | null;
  /** 당일 누적 거래대금 (원, 거래량×현재가 근사) */
  amount?: number | null;
  /** 시가총액 (단위: 억원) */
  market_cap?: number | null;
  /** 거래량 전일비 (%) */
  volume_pre_rate?: number | null;
  error?: string;
}

export interface CondSearchEntry {
  idx: string;
  name: string;
}

export interface CondSearchTickers {
  idx: string;
  tickers: { ticker: string; name: string; themes?: string[] }[];
  fetched_at: number;
}
