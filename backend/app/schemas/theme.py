"""테마 응답 모델."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ThemeSummary(BaseModel):
    id: str
    name: str
    description: str = ""
    n_leaders: int = 0
    n_related: int = 0


class ThemeStock(BaseModel):
    ticker: str
    name: str
    market: Optional[str] = None
    is_leader: bool = False
    market_cap: Optional[float] = None  # 시가총액 (현재 시점, 원)
    last_close: Optional[float] = None
    # ===== 가장 최근 거래일의 동적 정보 =====
    last_date: Optional[str] = None              # 최근 거래일 (YYYY-MM-DD)
    last_change_rate: Optional[float] = None     # 전일 대비 등락률
    last_amount: Optional[float] = None          # 거래대금 (close × volume, 원)


class ThemeDetailResponse(BaseModel):
    id: str
    name: str
    description: str = ""
    leaders: list[ThemeStock]
    related: list[ThemeStock]
