"""코스피 60일 이평 기준 장세 라벨링."""

from __future__ import annotations

from pathlib import Path

import FinanceDataReader as fdr
import pandas as pd

# 데이터 캐시 경로 — 프로젝트 루트의 data/
ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
KOSPI_CACHE = DATA_DIR / "kospi_index.csv"


def load_kospi_regime(start: str, end: str, ma_window: int = 60) -> pd.DataFrame:
    """
    코스피 지수 + 시장 라벨.
    Regime: 'bull' (Close > MA) / 'bear' (Close <= MA)
    """
    if KOSPI_CACHE.exists():
        df = pd.read_csv(KOSPI_CACHE, parse_dates=["Date"], index_col="Date")
    else:
        df = fdr.DataReader("KS11", "2020-01-01", "2026-12-31")
        df.index.name = "Date"
        DATA_DIR.mkdir(exist_ok=True)
        df.to_csv(KOSPI_CACHE, encoding="utf-8-sig")

    # 전체 캐시 기준으로 MA + 등락률 먼저 계산 → 그 다음 [start:end] 자르기
    df = df.copy()
    df["MA"] = df["Close"].rolling(ma_window).mean()
    df["PrevClose"] = df["Close"].shift(1)
    df["ChangeRate"] = (df["Close"] - df["PrevClose"]) / df["PrevClose"]

    df = df.loc[start:end].copy()
    df["Regime"] = "unknown"
    df.loc[df["Close"] > df["MA"], "Regime"] = "bull"
    df.loc[df["Close"] <= df["MA"], "Regime"] = "bear"
    return df[["Open", "High", "Low", "Close", "Volume", "ChangeRate", "MA", "Regime"]]
