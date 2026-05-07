"""
백테스트 서비스.

라우터(엔드포인트)가 호출하는 thin layer. core 로직 + DataStore + 결과 캐싱.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable

import pandas as pd

from app.core.backtest import backtest_with_cache, aggregate
from app.services.data_store import store


# 결과 캐시 키: (condition, market, entry, track_days, extra_days, targets_tuple)
_results_cache: dict[tuple, pd.DataFrame] = {}


def run_backtest(
    condition: str,
    market: str,
    entry: str,
    track_days: int,
    extra_days: int,
    targets: tuple[float, ...],
) -> pd.DataFrame:
    """인자별 캐싱된 백테스트. results DataFrame 반환 (skipped/시장 컬럼 포함)."""
    key = (condition, market, entry, track_days, extra_days, tuple(sorted(targets)))
    if key in _results_cache:
        return _results_cache[key]

    signals = store.get_signals_filtered(condition=condition, market=market)
    if signals.empty:
        empty = pd.DataFrame()
        _results_cache[key] = empty
        return empty

    # 시총 근사용 — 티커 → 상장주식수
    shares_map: dict[str, int] = {}
    if store.tickers is not None:
        for _, t in store.tickers.iterrows():
            try:
                shares_map[t["티커"]] = int(t["상장주식수"])
            except (ValueError, TypeError):
                pass

    # signals 에 등장하는 종목만 batch 로 SQLite 에서 가져오기 (메모리 절약)
    needed_tickers = signals["티커"].unique().tolist()
    ohlcv_dict = store.get_ohlcv_batch(needed_tickers)

    results = backtest_with_cache(
        signals,
        ohlcv_dict,
        list(targets),
        entry=entry,
        track_days=track_days,
        extra_days=extra_days,
        shares_map=shares_map,
    )
    # 시장 라벨 부착
    if store.tickers is not None and not results.empty:
        meta = store.tickers[["티커", "시장"]]
        results = results.merge(meta, on="티커", how="left")
    _results_cache[key] = results
    return results


def get_aggregate_for(
    condition: str,
    market: str,
    entry: str,
    track_days: int,
    extra_days: int,
    targets: tuple[float, ...],
) -> pd.DataFrame:
    results = run_backtest(condition, market, entry, track_days, extra_days, targets)
    return aggregate(results, list(targets), track_days=track_days)


def clear_cache() -> None:
    _results_cache.clear()
