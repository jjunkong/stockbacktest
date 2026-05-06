"""
Streamlit 대시보드용 데이터 로더 + 캐싱.

캐싱 전략:
  - @st.cache_resource: 무거운 객체 (OHLCV cache 1500+ DataFrame). 앱 시작 시 한 번만 로드
  - @st.cache_data: 함수 결과 (백테스트 등). 인자 같으면 재실행 안 함
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from backtest import (
    backtest_with_cache,
    aggregate,
    load_ohlcv_cache,
    OHLCV_DIR,
)
from market_regime import load_kospi_regime

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SIGNALS_CSV = DATA_DIR / "signals" / "all_signals.csv"
TICKERS_CSV = DATA_DIR / "tickers_filtered.csv"


@st.cache_resource(show_spinner="신호 데이터 로딩...")
def load_signals_all() -> pd.DataFrame:
    df = pd.read_csv(SIGNALS_CSV, parse_dates=["날짜"], dtype={"티커": str})
    df["티커"] = df["티커"].str.zfill(6)
    return df


@st.cache_resource(show_spinner="종목 메타 로딩...")
def load_tickers_meta() -> pd.DataFrame:
    df = pd.read_csv(TICKERS_CSV, dtype={"티커": str})
    df["티커"] = df["티커"].str.zfill(6)
    return df


@st.cache_resource(show_spinner="일봉 데이터 1,543개 로딩 중 (최초 1회만, 약 5초)...")
def load_all_ohlcv() -> dict[str, pd.DataFrame]:
    meta = load_tickers_meta()
    return load_ohlcv_cache(meta["티커"].tolist())


@st.cache_data(show_spinner="백테스트 실행 중...")
def run_backtest(
    condition: str,
    entry: str,
    targets_tuple: tuple[float, ...],
    track_days: int,
    extra_days: int,
) -> pd.DataFrame:
    """인자별로 캐싱된 백테스트. 결과에 시장(KOSPI/KOSDAQ) 컬럼 부착."""
    signals = load_signals_all()
    if condition != "all":
        signals = signals[signals["조건식"] == condition]
    cache = load_all_ohlcv()
    results = backtest_with_cache(
        signals, cache, list(targets_tuple),
        entry=entry, track_days=track_days, extra_days=extra_days,
        show_progress=False,
    )
    # 시장 정보 부착
    meta = load_tickers_meta()[["티커", "시장"]]
    results = results.merge(meta, on="티커", how="left")
    return results


def filter_by_market(results: pd.DataFrame, market: str) -> pd.DataFrame:
    """시장 필터: 'KOSPI' / 'KOSDAQ' / 'all'."""
    if market == "all" or "시장" not in results.columns:
        return results
    return results[results["시장"] == market].copy()


@st.cache_data(show_spinner="시장 라벨 부착 중...")
def attach_regime(results: pd.DataFrame, ma_window: int = 60) -> pd.DataFrame:
    """백테스트 결과에 코스피 60일 이평 기준 장세 라벨 추가."""
    if results.empty or "신호일" not in results.columns:
        return results
    start = results["신호일"].min().strftime("%Y-%m-%d")
    end = results["신호일"].max().strftime("%Y-%m-%d")
    regime = load_kospi_regime(start, end, ma_window)

    out = results.copy()
    out["_d"] = out["신호일"].dt.normalize()
    out = out.merge(regime[["Regime"]], left_on="_d", right_index=True, how="left")
    out["Regime"] = out["Regime"].fillna("unknown")
    out = out.drop(columns=["_d"])
    return out


@st.cache_data
def get_aggregate(results: pd.DataFrame, targets_tuple: tuple[float, ...],
                  track_days: int) -> pd.DataFrame:
    return aggregate(results, list(targets_tuple), track_days=track_days)
