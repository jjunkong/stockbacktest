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


# ===== 보조 지표 추가 =====
def add_indicators(df: pd.DataFrame, shares_outstanding: int) -> pd.DataFrame:
    """
    조건식 평가에 필요한 보조 컬럼들을 추가.

    shares_outstanding: 현재 상장주식수 (시점별 시총 근사용)
    """
    out = df.copy()

    # 시가총액 = 종가 × 현재 상장주식수 (근사)
    out["MarketCap"] = out["Close"] * shares_outstanding

    # 전일 종가 / 전일 거래량
    out["PrevClose"] = out["Close"].shift(1)
    out["PrevVolume"] = out["Volume"].shift(1)

    # 등락률 (전일 종가 대비) — 비율 (0.10 = 10%)
    out["ChangeRate"] = (out["Close"] - out["PrevClose"]) / out["PrevClose"]

    # 거래량 비율 (전일 대비)
    out["VolumeRatio"] = out["Volume"] / out["PrevVolume"]

    # 갭 비율 (전일 종가 대비 당일 시가)
    out["GapRate"] = (out["Open"] - out["PrevClose"]) / out["PrevClose"]

    # 240일 이동평균 (종가)
    out["MA240"] = out["Close"].rolling(window=240, min_periods=240).mean()

    return out


# ===== 조건식 1: 급등주 추격형 =====
def cond1_breakout_chase(df: pd.DataFrame) -> pd.Series:
    """
    이미 +10~25% 오른 저가주를 추격하는 콘셉트.

    - 5,000원 <= Close <= 20,000원
    - 10% <= ChangeRate <= 25%
    - VolumeRatio >= 500%
    - 3,000,000 <= Volume <= 999,999,999
    - Close >= MA240 (정배열 시작)
    - MarketCap >= 1,000억
    """
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


# ===== 조건식 2: 갭상승 정배열형 =====
def cond2_gap_aligned(df: pd.DataFrame) -> pd.Series:
    """
    장기 추세 위에서 갭상승하며 모멘텀 잡는 콘셉트.

    - (VolumeRatio >= 800%) OR (3,000,000 <= Volume <= 999,999,999)
    - GapRate >= 1%
    - 5% <= ChangeRate <= 20%
    - Open > MA240
    - MarketCap >= 1,000억
    """
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


# ===== 조건식 등록 =====
# 키: 조건식 ID, 값: (한글 이름, 함수)
CONDITIONS = {
    "cond1": ("급등주 추격형", cond1_breakout_chase),
    "cond2": ("갭상승 정배열형", cond2_gap_aligned),
}


def list_conditions() -> None:
    """등록된 조건식 목록 출력 (디버깅용)."""
    print("=== 등록된 조건식 ===")
    for cid, (name, _) in CONDITIONS.items():
        print(f"  {cid}: {name}")


if __name__ == "__main__":
    list_conditions()
