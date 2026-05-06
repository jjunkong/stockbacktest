"""
키움 조건검색식의 파이썬 재현.

조건식은 모두 다음 시그니처를 따릅니다:
    fn(df: pd.DataFrame) -> pd.Series  # bool Series, index=날짜

입력 DataFrame은 add_indicators() 통과한 형태여야 합니다:
    필수 컬럼: Open, High, Low, Close, Volume, MarketCap
    파생 컬럼: PrevClose, PrevVolume, ChangeRate, VolumeRatio, GapRate, MA240

조건식을 추가하려면:
    1) 새 함수 정의
    2) CONDITIONS 딕셔너리에 등록
"""

from __future__ import annotations

import pandas as pd

# ===== 임계값 =====
MARKET_CAP_THRESHOLD = 100_000_000_000  # 1,000억 원
VOLUME_MIN = 3_000_000
VOLUME_MAX = 999_999_999


def add_indicators(df: pd.DataFrame, shares_outstanding: int) -> pd.DataFrame:
    out = df.copy()
    out["MarketCap"] = out["Close"] * shares_outstanding
    out["PrevClose"] = out["Close"].shift(1)
    out["PrevVolume"] = out["Volume"].shift(1)
    out["ChangeRate"] = (out["Close"] - out["PrevClose"]) / out["PrevClose"]
    out["VolumeRatio"] = out["Volume"] / out["PrevVolume"]
    out["GapRate"] = (out["Open"] - out["PrevClose"]) / out["PrevClose"]
    out["MA240"] = out["Close"].rolling(window=240, min_periods=240).mean()
    return out


def cond1_breakout_chase(df: pd.DataFrame) -> pd.Series:
    """급등주 추격형: 5,000~20,000원 / +10~25% / 거래량 500%↑+300만주↑ / Close≥MA240 / 시총 1,000억↑"""
    return (
        (df["Close"] >= 5_000)
        & (df["Close"] <= 20_000)
        & (df["ChangeRate"] >= 0.10)
        & (df["ChangeRate"] <= 0.25)
        & (df["VolumeRatio"] >= 5.0)
        & (df["Volume"] >= VOLUME_MIN)
        & (df["Volume"] <= VOLUME_MAX)
        & (df["Close"] >= df["MA240"])
        & (df["MarketCap"] >= MARKET_CAP_THRESHOLD)
    )


def cond2_gap_aligned(df: pd.DataFrame) -> pd.Series:
    """갭상승 정배열형: (거래량 800%↑ OR 300만주↑) / 갭 1%↑ / +5~20% / Open>MA240 / 시총 1,000억↑"""
    volume_condition = (df["VolumeRatio"] >= 8.0) | (
        (df["Volume"] >= VOLUME_MIN) & (df["Volume"] <= VOLUME_MAX)
    )
    return (
        volume_condition
        & (df["GapRate"] >= 0.01)
        & (df["ChangeRate"] >= 0.05)
        & (df["ChangeRate"] <= 0.20)
        & (df["Open"] > df["MA240"])
        & (df["MarketCap"] >= MARKET_CAP_THRESHOLD)
    )


CONDITIONS = {
    "cond1": ("급등주 추격형", cond1_breakout_chase),
    "cond2": ("갭상승 정배열형", cond2_gap_aligned),
}
