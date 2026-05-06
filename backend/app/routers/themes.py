"""테마/주도주 라우터."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException

from app.schemas.theme import ThemeDetailResponse, ThemeStock, ThemeSummary
from app.services.data_store import store
from app.services.theme_store import theme_store

router = APIRouter(prefix="/themes", tags=["themes"])


def _build_stock(ticker: str, is_leader: bool) -> ThemeStock | None:
    """티커를 ThemeStock으로 — 최근 거래일의 등락률/거래대금까지 채움."""
    t = ticker.zfill(6)
    if store.tickers is None:
        return None
    row = store.tickers[store.tickers["티커"] == t]
    if row.empty:
        return ThemeStock(ticker=t, name="(데이터 없음)", is_leader=is_leader)
    r = row.iloc[0]

    # 최근 거래일 OHLCV 정보 (data cache 기준 최신)
    last_date = None
    last_change_rate = None
    last_amount = None
    last_close = float(r["종가"]) if pd.notna(r["종가"]) else None

    df = store.get_ohlcv(t)
    if df is not None and not df.empty:
        last_idx = df.index[-1]
        last_row = df.iloc[-1]
        last_date = pd.Timestamp(last_idx).strftime("%Y-%m-%d")
        last_close_ohlcv = float(last_row["Close"])
        # OHLCV에 더 최신 종가가 있으면 그쪽 우선
        if last_close_ohlcv and last_close_ohlcv > 0:
            last_close = last_close_ohlcv
        if pd.notna(last_row["Volume"]):
            last_amount = last_close * float(last_row["Volume"])
        # 등락률 = (오늘 종가 - 전일 종가) / 전일 종가
        if len(df) >= 2:
            prev_close = float(df.iloc[-2]["Close"])
            if prev_close > 0:
                last_change_rate = (last_close - prev_close) / prev_close

    return ThemeStock(
        ticker=t,
        name=str(r["종목명"]),
        market=str(r["시장"]),
        is_leader=is_leader,
        market_cap=float(r["시가총액"]) if pd.notna(r["시가총액"]) else None,
        last_close=last_close,
        last_date=last_date,
        last_change_rate=last_change_rate,
        last_amount=last_amount,
    )


@router.get("", response_model=list[ThemeSummary])
def list_themes() -> list[ThemeSummary]:
    return [ThemeSummary(**t) for t in theme_store.list_themes()]


@router.get("/{theme_id}", response_model=ThemeDetailResponse)
def get_theme(theme_id: str) -> ThemeDetailResponse:
    th = theme_store.get_theme(theme_id)
    if th is None:
        raise HTTPException(404, f"테마 '{theme_id}' 없음")

    leaders: list[ThemeStock] = []
    for t in th.get("leaders", []):
        s = _build_stock(t, is_leader=True)
        if s is not None:
            leaders.append(s)

    related: list[ThemeStock] = []
    for t in th.get("related", []):
        s = _build_stock(t, is_leader=False)
        if s is not None:
            related.append(s)

    # 시총 큰 순 정렬
    leaders.sort(key=lambda x: x.market_cap or 0, reverse=True)
    related.sort(key=lambda x: x.market_cap or 0, reverse=True)

    return ThemeDetailResponse(
        id=th["id"],
        name=th["name"],
        description=th.get("description", ""),
        leaders=leaders,
        related=related,
    )
