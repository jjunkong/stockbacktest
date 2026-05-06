"""코스피 지수 + 60일 이평."""

from __future__ import annotations

from datetime import date as Date

import pandas as pd
from fastapi import APIRouter, Query

from app.core.market_regime import load_kospi_regime
from app.schemas.ticker import KospiResponse, KospiRow

router = APIRouter(prefix="/kospi", tags=["kospi"])


@router.get("", response_model=KospiResponse)
def get_kospi(
    start: Date = Query(...),
    end: Date = Query(...),
    ma_window: int = 60,
) -> KospiResponse:
    """장세 라벨 포함 코스피 지수."""
    df = load_kospi_regime(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), ma_window)
    rows: list[KospiRow] = []
    for d, r in df.iterrows():
        rows.append(KospiRow(
            date=d.date(),
            open=float(r["Open"]),
            high=float(r["High"]),
            low=float(r["Low"]),
            close=float(r["Close"]),
            volume=int(r["Volume"]) if pd.notna(r["Volume"]) else 0,
            change_rate=float(r["ChangeRate"]) if pd.notna(r["ChangeRate"]) else None,
            ma=float(r["MA"]) if pd.notna(r["MA"]) else None,
            regime=str(r["Regime"]),
        ))
    return KospiResponse(ma_window=ma_window, rows=rows)
