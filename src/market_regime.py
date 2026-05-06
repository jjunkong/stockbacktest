"""
시장 상황별 백테스트 결과 분류.

코스피 지수(KS11)를 다운로드해 60일 이동평균 위/아래로 시장 라벨링 후,
백테스트 결과 CSV에 라벨을 붙여 장세별 도달률 매트릭스를 출력.

사용:
    python src/market_regime.py --results data/results/cond1_entry_open_next_track10_raw.csv
    python src/market_regime.py --results data/results/cond2_entry_open_next_track10_raw.csv --ma 60
"""

from __future__ import annotations

import argparse
from pathlib import Path

import FinanceDataReader as fdr
import pandas as pd

from backtest import aggregate, print_matrix, parse_targets

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
KOSPI_CACHE = DATA_DIR / "kospi_index.csv"


def load_kospi_regime(start: str, end: str, ma_window: int = 60) -> pd.DataFrame:
    """
    코스피 지수 다운로드 + 시장 라벨.
    Regime: 'bull' (Close > MA) / 'bear' (Close <= MA)
    """
    if KOSPI_CACHE.exists():
        df = pd.read_csv(KOSPI_CACHE, parse_dates=["Date"], index_col="Date")
    else:
        print("코스피 지수 다운로드 중...")
        df = fdr.DataReader("KS11", "2020-01-01", "2026-12-31")
        df.index.name = "Date"
        df.to_csv(KOSPI_CACHE, encoding="utf-8-sig")

    df = df.loc[start:end].copy()
    df["MA"] = df["Close"].rolling(ma_window).mean()
    df["Regime"] = "unknown"
    df.loc[df["Close"] > df["MA"], "Regime"] = "bull"
    df.loc[df["Close"] <= df["MA"], "Regime"] = "bear"
    return df[["Close", "MA", "Regime"]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True,
                        help="백테스트 결과 raw CSV 경로")
    parser.add_argument("--ma", type=int, default=60,
                        help="시장 판정 이동평균 기간 (기본 60일)")
    parser.add_argument("--targets", default="5,10,15,20")
    parser.add_argument("--track-days", type=int, default=10)
    args = parser.parse_args()

    targets = parse_targets(args.targets)
    results_path = Path(args.results)
    if not results_path.exists():
        raise FileNotFoundError(results_path)

    results = pd.read_csv(results_path, parse_dates=["신호일"], dtype={"티커": str})
    print(f"\n결과 파일: {results_path.name}")
    print(f"  총 신호: {len(results):,}건")

    # 시장 라벨 부착
    start = results["신호일"].min().strftime("%Y-%m-%d")
    end = results["신호일"].max().strftime("%Y-%m-%d")
    regime = load_kospi_regime(start, end, args.ma)

    # 신호일을 인덱스 매칭용 normalize
    results["_d"] = results["신호일"].dt.normalize()
    merged = results.merge(
        regime[["Regime"]],
        left_on="_d",
        right_index=True,
        how="left",
    )
    merged["Regime"] = merged["Regime"].fillna("unknown")
    merged = merged.drop(columns=["_d"])

    # 분포 요약
    print(f"\n시장 상황 분포 (코스피 {args.ma}일 이평 기준):")
    for label, n in merged["Regime"].value_counts().items():
        print(f"  {label}: {n:,}건 ({n/len(merged)*100:.1f}%)")

    # 라벨별 매트릭스
    cond_id = merged["조건식"].iloc[0] if "조건식" in merged.columns else "?"
    label_kor = {"bull": "상승장", "bear": "하락장", "unknown": "분류불가"}

    for label in ("bull", "bear"):
        sub = merged[merged["Regime"] == label]
        if sub.empty:
            print(f"\n[{label_kor[label]}] 데이터 없음")
            continue
        agg = aggregate(sub, targets, track_days=args.track_days)
        title = f"{cond_id} / {label_kor[label]} ({label})"
        print_matrix(agg, title, track_days=args.track_days)


if __name__ == "__main__":
    main()
