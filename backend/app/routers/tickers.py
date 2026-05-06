"""종목별 OHLCV + 신호 이력."""

from __future__ import annotations

from datetime import date as Date

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.schemas.ticker import OHLCVRow, TickerOHLCVResponse
from app.schemas.backtest import SignalResult
from app.services.data_store import store
from app.services.backtest_service import run_backtest

router = APIRouter(prefix="/tickers", tags=["tickers"])


@router.get("/{ticker}/ohlcv", response_model=TickerOHLCVResponse)
def get_ohlcv(
    ticker: str,
    start: Date | None = Query(None),
    end: Date | None = Query(None),
) -> TickerOHLCVResponse:
    """캔들차트용 OHLCV. start/end로 구간 자르기."""
    df = store.get_ohlcv(ticker)
    if df is None or df.empty:
        raise HTTPException(404, f"{ticker} OHLCV 없음")

    view = df.copy()
    if start:
        view = view.loc[pd.Timestamp(start):]
    if end:
        view = view.loc[:pd.Timestamp(end)]

    view = view.sort_index()
    view["전일종가"] = view["Close"].shift(1)
    view["등락률"] = (view["Close"] - view["전일종가"]) / view["전일종가"]

    rows: list[OHLCVRow] = []
    for d, r in view.iterrows():
        rows.append(OHLCVRow(
            date=d.date(),
            open=float(r["Open"]),
            high=float(r["High"]),
            low=float(r["Low"]),
            close=float(r["Close"]),
            volume=int(r["Volume"]),
            change_rate=float(r["등락률"]) if pd.notna(r["등락률"]) else None,
        ))

    name = ""
    market = None
    if store.tickers is not None:
        meta = store.tickers[store.tickers["티커"] == ticker.zfill(6)]
        if len(meta):
            name = str(meta["종목명"].iloc[0])
            market = str(meta["시장"].iloc[0])

    return TickerOHLCVResponse(ticker=ticker.zfill(6), name=name, market=market, rows=rows)


@router.get("/{ticker}/signals", response_model=list[SignalResult])
def get_ticker_signals(
    ticker: str,
    condition: str = Query(...),
    market: str = "all",
    entry: str = "open_next",
    track_days: int = 10,
    extra_days: int = 20,
    targets: str = Query("5,10,15,20"),
) -> list[SignalResult]:
    """이 종목의 모든 신호 + 백테스트 결과."""
    tgt_list = tuple(sorted({float(x.strip())/100 for x in targets.split(",") if x.strip()}))
    results = run_backtest(condition, market, entry, track_days, extra_days, tgt_list)
    if results.empty:
        return []
    sub = results[results["티커"] == ticker.zfill(6)]
    if sub.empty:
        return []

    out: list[SignalResult] = []
    for _, r in sub.iterrows():
        days_map: dict[str, int | None] = {}
        for t in tgt_list:
            col = f"d_{int(t*100)}"
            v = r.get(col)
            days_map[str(int(t * 100))] = int(v) if pd.notna(v) else None

        out.append(SignalResult(
            ticker=str(r["티커"]),
            name=str(r.get("종목명", "")),
            market=r.get("시장"),
            condition=str(r["조건식"]),
            signal_date=pd.to_datetime(r["신호일"]).date(),
            entry_date=pd.to_datetime(r["진입일"]).date() if pd.notna(r.get("진입일")) else None,
            entry_price=float(r["진입가"]) if pd.notna(r.get("진입가")) else None,
            days_to_target=days_map,
            mdd=float(r["MDD"]) if pd.notna(r.get("MDD")) else None,
            final_pnl=float(r["최종손익"]) if pd.notna(r.get("최종손익")) else None,
            skipped=r.get("skipped") if pd.notna(r.get("skipped")) else None,
        ))
    return sorted(out, key=lambda x: x.signal_date, reverse=True)
