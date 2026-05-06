"""백테스트 요청/응답 모델."""

from __future__ import annotations

from datetime import date as Date
from typing import Optional

from pydantic import BaseModel, Field

from .common import ConditionId, MarketId, EntryOption


# ===== 요청 =====

class BacktestRequest(BaseModel):
    condition: ConditionId
    market: MarketId = "all"
    entry: EntryOption = "open_next"
    track_days: int = Field(10, ge=1, le=60)
    extra_days: int = Field(20, ge=0, le=60)
    targets: list[float] = Field(default_factory=lambda: [0.05, 0.10, 0.15, 0.20])


# ===== 매트릭스 행 =====

class MatrixRow(BaseModel):
    target: str                       # "+10%"
    n_signals: int
    in_track_rate: float              # 0.0~1.0
    over_track_rate: float
    miss_rate: float
    avg_days_to_hit: Optional[float] = None
    avg_mdd_on_miss: Optional[float] = None
    avg_pnl_on_miss: Optional[float] = None
    miss_rate_no_day1: Optional[float] = None
    # ↑ 조건부 확률: P(끝까지 미달성 | 1일차에 미도달)
    # "신호 다음날 한 번에 못 닿으면 결국 못 갈 확률" — 손절 룰 판단용


# ===== 신호 단건 (raw 결과) =====

class SignalResult(BaseModel):
    ticker: str
    name: str
    market: Optional[str] = None
    condition: str
    signal_date: Date
    entry_date: Optional[Date] = None
    entry_price: Optional[float] = None
    days_to_target: dict[str, Optional[int]] = Field(
        default_factory=dict,
        description="키: '5','10','15','20', 값: 도달일(없으면 null)",
    )
    mdd: Optional[float] = None
    final_pnl: Optional[float] = None
    skipped: Optional[str] = None
    # ===== 신호 발생일 보조 정보 =====
    signal_close: Optional[float] = None        # 신호 당일 종가
    signal_change_rate: Optional[float] = None  # 신호 당일 등락률 (전일 대비)
    signal_volume: Optional[int] = None         # 신호 당일 거래량
    signal_amount: Optional[float] = None       # 신호 당일 거래대금 (close × volume)
    signal_market_cap: Optional[float] = None   # 신호 당일 시가총액 (근사)
    themes: list[str] = Field(default_factory=list)  # 종목이 속한 테마 목록


# ===== 종합 응답 =====

class BacktestResponse(BaseModel):
    condition: str
    condition_label: str
    market: str
    entry: str
    entry_label: str
    track_days: int
    extra_days: int
    targets: list[float]
    n_signals: int
    avg_hit_rate: float = Field(..., description="모든 목표의 track_days 내 도달률 평균")
    matrix: list[MatrixRow]


# ===== 날짜별 분석 =====

class DateBundleStat(BaseModel):
    target: str
    hit_count: int
    over_count: int
    miss_count: int
    total: int
    hit_rate: float
    avg_days_to_hit: Optional[float] = None


class DateBundleResponse(BaseModel):
    date: Date
    n_signals: int
    bundle_stats: list[DateBundleStat]
    individuals: list[SignalResult]


# ===== 장세별 비교 =====

class RegimeMatrix(BaseModel):
    regime: str           # "bull" / "bear"
    regime_label: str     # "상승장" / "하락장"
    n_signals: int
    rows: list[MatrixRow]


class RegimeComparisonResponse(BaseModel):
    condition: str
    market: str
    entry: str
    track_days: int
    distribution: dict[str, int]   # {"bull": 1074, "bear": 325, "unknown": 75}
    regimes: list[RegimeMatrix]


# ===== 종목 요약 =====

class TickerSummaryRow(BaseModel):
    ticker: str
    name: str
    market: Optional[str] = None
    n_signals: int
    n_hit: int
    hit_rate: float
    last_signal: Date


class TickerSummaryResponse(BaseModel):
    target_pct: int      # 10 (= +10% 기준)
    track_days: int
    rows: list[TickerSummaryRow]
