"""종목 OHLCV / 신호 이력 응답 모델."""

from __future__ import annotations

from datetime import date as Date
from typing import Optional

from pydantic import BaseModel


class OHLCVRow(BaseModel):
    date: Date
    open: float
    high: float
    low: float
    close: float
    volume: int
    change_rate: Optional[float] = None  # 전일 대비 (-1.0 ~ +inf)


class TickerOHLCVResponse(BaseModel):
    ticker: str
    name: str
    market: Optional[str] = None
    rows: list[OHLCVRow]


class KospiRow(BaseModel):
    date: Date
    open: float
    high: float
    low: float
    close: float
    volume: int = 0
    change_rate: Optional[float] = None
    ma: Optional[float] = None
    regime: str  # bull/bear/unknown


class KospiResponse(BaseModel):
    ma_window: int
    rows: list[KospiRow]
