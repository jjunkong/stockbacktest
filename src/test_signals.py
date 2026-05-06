"""
과거 데이터에서 조건식 신호 발생 횟수/분포를 검증하는 스크립트.

Phase 1 마지막 단계: 데이터 + 조건식이 잘 결합되는지, 신호가
합리적인 빈도로 잡히는지 확인.

사용:
    python src/test_signals.py            # 모든 조건식 검증
    python src/test_signals.py --sample   # 샘플 50종목으로만 빠르게
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from conditions import CONDITIONS, add_indicators

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OHLCV_DIR = DATA_DIR / "ohlcv"
TICKERS_FILTERED_CSV = DATA_DIR / "tickers_filtered.csv"
SIGNALS_DIR = DATA_DIR / "signals"
SIGNALS_DIR.mkdir(exist_ok=True)


def load_ticker_meta() -> pd.DataFrame:
    df = pd.read_csv(TICKERS_FILTERED_CSV, dtype={"티커": str})
    df["티커"] = df["티커"].str.zfill(6)
    return df.set_index("티커")


def load_ohlcv(ticker: str) -> pd.DataFrame | None:
    path = OHLCV_DIR / f"{ticker}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["날짜"], index_col="날짜")
    if df.empty:
        return None
    return df


def detect_signals_for_ticker(
    ticker: str, name: str, shares: int, df: pd.DataFrame
) -> pd.DataFrame:
    """
    한 종목의 일봉에 모든 조건식을 적용, 신호 발생 row를 long-format으로 반환.
    컬럼: 티커, 종목명, 조건식, 날짜, Open, High, Low, Close, Volume, ChangeRate, ...
    """
    enriched = add_indicators(df, shares_outstanding=shares)
    rows = []
    for cid, (cname, fn) in CONDITIONS.items():
        sig = fn(enriched)
        if not sig.any():
            continue
        hit = enriched[sig].copy()
        hit["티커"] = ticker
        hit["종목명"] = name
        hit["조건식"] = cid
        hit["조건식이름"] = cname
        hit = hit.reset_index().rename(columns={"날짜": "날짜"})
        rows.append(hit)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def main(sample: int | None = None) -> None:
    meta = load_ticker_meta()
    tickers = list(meta.index)
    if sample:
        tickers = tickers[:sample]
        print(f"[샘플 모드] 상위 {sample}개 종목만 검증")

    all_signals: list[pd.DataFrame] = []
    no_data = 0

    for ticker in tqdm(tickers, desc="신호 검색"):
        df = load_ohlcv(ticker)
        if df is None:
            no_data += 1
            continue
        info = meta.loc[ticker]
        shares = int(info["상장주식수"]) if pd.notna(info["상장주식수"]) else 0
        if shares <= 0:
            continue
        sig_df = detect_signals_for_ticker(
            ticker, info["종목명"], shares, df
        )
        if not sig_df.empty:
            all_signals.append(sig_df)

    if not all_signals:
        print("\n[!] 신호가 한 건도 발견되지 않았습니다. 조건식이나 데이터 점검 필요.")
        return

    signals = pd.concat(all_signals, ignore_index=True)
    signals.to_csv(SIGNALS_DIR / "all_signals.csv", index=False, encoding="utf-8-sig")

    print()
    print("=" * 60)
    print(f"  검증 완료: {len(tickers)}종목 (데이터 없음: {no_data}개)")
    print(f"  총 신호: {len(signals):,}건")
    print("=" * 60)

    for cid, (cname, _) in CONDITIONS.items():
        sub = signals[signals["조건식"] == cid]
        if sub.empty:
            print(f"\n[{cid}] {cname}: 신호 0건")
            continue

        n_sig = len(sub)
        n_uniq_tickers = sub["티커"].nunique()
        date_min = sub["날짜"].min()
        date_max = sub["날짜"].max()

        print(f"\n[{cid}] {cname}")
        print(f"  · 신호 총 발생: {n_sig:,}건")
        print(f"  · 신호 발생 종목: {n_uniq_tickers}개")
        print(f"  · 기간: {date_min.date()} ~ {date_max.date()}")

        top = (
            sub.groupby(["티커", "종목명"])
            .size()
            .reset_index(name="횟수")
            .sort_values("횟수", ascending=False)
            .head(5)
        )
        print(f"  · Top 5 다발 종목:")
        for _, r in top.iterrows():
            print(f"      {r['티커']} {r['종목명']}: {r['횟수']}회")

        # 연도별 분포
        sub_year = sub.copy()
        sub_year["연도"] = pd.to_datetime(sub_year["날짜"]).dt.year
        year_dist = sub_year.groupby("연도").size()
        print(f"  · 연도별 분포:")
        for year, cnt in year_dist.items():
            print(f"      {year}: {cnt}건")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=None,
                        help="상위 N종목만 빠르게 검증")
    args = parser.parse_args()
    main(sample=args.sample)
