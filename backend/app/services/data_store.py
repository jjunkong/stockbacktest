"""
앱 전역에서 공유하는 인메모리 데이터 스토어.

서버 시작 시 lifespan에서 prime() 호출 → OHLCV + 신호 + 메타 모두 메모리에 적재.
이후 모든 요청은 디스크 IO 없이 메모리에서 즉시 조회.

데이터 소스 우선순위:
  1. stocks.db (SQLite, 단일 파일) — Phase 5에서 클라우드 배포용
  2. data/ohlcv/*.csv (1,543개 파일) — 로컬 개발용 fallback
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

import pandas as pd

# 프로젝트 루트의 data/
ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
OHLCV_DIR = DATA_DIR / "ohlcv"
SIGNALS_CSV = DATA_DIR / "signals" / "all_signals.csv"
TICKERS_CSV = DATA_DIR / "tickers_filtered.csv"
STOCKS_DB = DATA_DIR / "stocks.db"


class DataStore:
    """앱 전역 캐시. main.py의 lifespan에서 prime() 호출."""

    def __init__(self) -> None:
        self.ohlcv: dict[str, pd.DataFrame] = {}
        self.signals: pd.DataFrame | None = None
        self.tickers: pd.DataFrame | None = None

    def prime(self) -> None:
        """모든 OHLCV + signals + tickers 메모리에 로드."""
        self.tickers = self._load_tickers()
        self.signals = self._load_signals()
        self.ohlcv = self._load_all_ohlcv(self.tickers["티커"].tolist())

    def is_ready(self) -> bool:
        return self.signals is not None and self.tickers is not None and len(self.ohlcv) > 0

    @staticmethod
    def _load_tickers() -> pd.DataFrame:
        df = pd.read_csv(TICKERS_CSV, dtype={"티커": str})
        df["티커"] = df["티커"].str.zfill(6)
        return df

    @staticmethod
    def _load_signals() -> pd.DataFrame:
        df = pd.read_csv(SIGNALS_CSV, parse_dates=["날짜"], dtype={"티커": str})
        df["티커"] = df["티커"].str.zfill(6)
        return df

    @staticmethod
    def _load_all_ohlcv(tickers: Iterable[str]) -> dict[str, pd.DataFrame]:
        # SQLite 단일 파일이 있으면 우선 (배포 환경)
        if STOCKS_DB.exists():
            return DataStore._load_ohlcv_from_sqlite(tickers)
        # 없으면 CSV fallback (로컬 개발)
        return DataStore._load_ohlcv_from_csv(tickers)

    @staticmethod
    def _load_ohlcv_from_sqlite(tickers: Iterable[str]) -> dict[str, pd.DataFrame]:
        """stocks.db (SQLite)에서 한 번에 읽어 dict로 그룹핑."""
        wanted = set(t.zfill(6) for t in tickers)
        with sqlite3.connect(str(STOCKS_DB)) as conn:
            df = pd.read_sql(
                "SELECT 티커, 날짜, Open, High, Low, Close, Volume FROM ohlcv ORDER BY 티커, 날짜",
                conn,
                parse_dates=["날짜"],
            )
        df["티커"] = df["티커"].astype(str).str.zfill(6)
        df = df[df["티커"].isin(wanted)]
        # 미마감 행 제거
        df = df[df["Open"] > 0]

        cache: dict[str, pd.DataFrame] = {}
        for ticker, group in df.groupby("티커"):
            g = group.drop(columns=["티커"]).set_index("날짜").sort_index()
            cache[ticker] = g
        return cache

    @staticmethod
    def _load_ohlcv_from_csv(tickers: Iterable[str]) -> dict[str, pd.DataFrame]:
        cache: dict[str, pd.DataFrame] = {}
        for t in sorted(set(tickers)):
            path = OHLCV_DIR / f"{t}.csv"
            if not path.exists():
                continue
            df = pd.read_csv(path, parse_dates=["날짜"], index_col="날짜").sort_index()
            # 미마감(미체결) 행 제거 — Open이 0이거나 None인 행
            df = df[df["Open"] > 0]
            cache[t] = df
        return cache

    def get_ohlcv(self, ticker: str) -> pd.DataFrame | None:
        return self.ohlcv.get(ticker.zfill(6))

    def get_market_for(self, ticker: str) -> str | None:
        if self.tickers is None:
            return None
        row = self.tickers[self.tickers["티커"] == ticker.zfill(6)]
        return row["시장"].iloc[0] if len(row) else None

    def get_signals_filtered(
        self,
        condition: str | None = None,
        market: str | None = None,
    ) -> pd.DataFrame:
        if self.signals is None or self.tickers is None:
            return pd.DataFrame()
        df = self.signals.copy()
        if condition and condition != "all":
            df = df[df["조건식"] == condition]
        if market and market != "all":
            keep = self.tickers[self.tickers["시장"] == market]["티커"].tolist()
            df = df[df["티커"].isin(keep)]
        return df


# 전역 싱글턴 — main.py가 lifespan에서 prime() 호출
store = DataStore()
