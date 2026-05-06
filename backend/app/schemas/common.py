"""공통 응답 모델."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ConditionId = Literal["cond1", "cond2"]
MarketId = Literal["all", "KOSPI", "KOSDAQ"]
EntryOption = Literal["close_today", "open_next", "close_next"]


class ConditionInfo(BaseModel):
    id: str
    label: str


class MarketInfo(BaseModel):
    id: str
    label: str


class EntryInfo(BaseModel):
    id: str
    label: str


class HealthResponse(BaseModel):
    status: str = "ok"
    cache_ready: bool = Field(..., description="OHLCV/signals 메모리 준비 완료 여부")
    n_tickers: int = 0
    n_signals: int = 0
