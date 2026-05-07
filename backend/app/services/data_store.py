"""
앱 전역에서 공유하는 인메모리 데이터 스토어.

서버 시작 시 lifespan에서 prime() 호출 → 가벼운 메타(signals + tickers)만 메모리.
OHLCV 는 요청 시 SQLite 에서 lazy 로드 (LRU 캐시) — 메모리 ~250MB 안에 머물기 위함.

데이터 소스 우선순위:
  1. stocks.db (SQLite, 단일 파일) — 클라우드 배포용
  2. data/ohlcv/*.csv (1,543개 파일) — 로컬 개발용 fallback
"""

from __future__ import annotations

import sqlite3
from collections import OrderedDict
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

# 단일 종목 조회용 LRU 캐시 크기 (한 종목 ~1MB → 50개면 약 50MB)
_OHLCV_CACHE_MAX = 50


class DataStore:
    """앱 전역 캐시. main.py의 lifespan에서 prime() 호출."""

    def __init__(self) -> None:
        self.signals: pd.DataFrame | None = None
        self.tickers: pd.DataFrame | None = None
        # 단일 조회용 LRU
        self._ohlcv_cache: OrderedDict[str, pd.DataFrame] = OrderedDict()

    def prime(self) -> None:
        """가벼운 메타(signals + tickers)만 메모리. OHLCV 는 lazy 로드."""
        self.tickers = self._load_tickers()
        self.signals = self._load_signals()

    def is_ready(self) -> bool:
        return self.signals is not None and self.tickers is not None

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

    # ===== 단일 종목 조회 (LRU 캐시 사용) =====

    def get_ohlcv(self, ticker: str) -> pd.DataFrame | None:
        t = ticker.zfill(6)
        if t in self._ohlcv_cache:
            self._ohlcv_cache.move_to_end(t)
            return self._ohlcv_cache[t]
        df = self._fetch_one(t)
        if df is not None:
            self._ohlcv_cache[t] = df
            if len(self._ohlcv_cache) > _OHLCV_CACHE_MAX:
                self._ohlcv_cache.popitem(last=False)
        return df

    @staticmethod
    def _fetch_one(ticker: str) -> pd.DataFrame | None:
        if STOCKS_DB.exists():
            return DataStore._fetch_one_sqlite(ticker)
        return DataStore._fetch_one_csv(ticker)

    @staticmethod
    def _fetch_one_sqlite(ticker: str) -> pd.DataFrame | None:
        with sqlite3.connect(str(STOCKS_DB)) as conn:
            df = pd.read_sql(
                "SELECT 날짜, Open, High, Low, Close, Volume FROM ohlcv WHERE 티커 = ? ORDER BY 날짜",
                conn,
                params=[ticker],
                parse_dates=["날짜"],
            )
        if df.empty:
            return None
        df = df[df["Open"] > 0]
        return df.set_index("날짜").sort_index()

    @staticmethod
    def _fetch_one_csv(ticker: str) -> pd.DataFrame | None:
        path = OHLCV_DIR / f"{ticker}.csv"
        if not path.exists():
            return None
        df = pd.read_csv(path, parse_dates=["날짜"], index_col="날짜").sort_index()
        return df[df["Open"] > 0]

    # ===== 배치 조회 (백테스트 용. LRU 우회) =====

    def get_ohlcv_batch(self, tickers: Iterable[str]) -> dict[str, pd.DataFrame]:
        """다수 종목 한 번에 메모리로. 백테스트가 호출 — 결과 dict 는 호출자만 사용."""
        unique = sorted(set(t.zfill(6) for t in tickers))
        if not unique:
            return {}
        if STOCKS_DB.exists():
            return DataStore._fetch_batch_sqlite(unique)
        return DataStore._fetch_batch_csv(unique)

    @staticmethod
    def _fetch_batch_sqlite(tickers: list[str]) -> dict[str, pd.DataFrame]:
        # IN 쿼리 chunk (SQLite 변수 한도 ~999 회피)
        out: dict[str, pd.DataFrame] = {}
        with sqlite3.connect(str(STOCKS_DB)) as conn:
            for i in range(0, len(tickers), 500):
                chunk = tickers[i : i + 500]
                placeholders = ",".join(["?"] * len(chunk))
                sql = (
                    f"SELECT 티커, 날짜, Open, High, Low, Close, Volume "
                    f"FROM ohlcv WHERE 티커 IN ({placeholders}) ORDER BY 티커, 날짜"
                )
                df = pd.read_sql(sql, conn, params=chunk, parse_dates=["날짜"])
                df["티커"] = df["티커"].astype(str).str.zfill(6)
                df = df[df["Open"] > 0]
                for ticker, group in df.groupby("티커"):
                    g = group.drop(columns=["티커"]).set_index("날짜").sort_index()
                    out[ticker] = g
        return out

    @staticmethod
    def _fetch_batch_csv(tickers: list[str]) -> dict[str, pd.DataFrame]:
        out: dict[str, pd.DataFrame] = {}
        for t in tickers:
            df = DataStore._fetch_one_csv(t)
            if df is not None:
                out[t] = df
        return out

    # ===== 기타 =====

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
