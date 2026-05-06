"""
백테스팅 엔진.

핵심 흐름:
  1) 신호 발생일 + 종목 일봉 → 진입가 결정
  2) 추적 기간 동안 일별 High로 목표 도달 여부 판정
  3) 미도달 시 MDD/평균손실 계산
  4) 결과 dict 반환

진입가 옵션:
  close_today : 신호 당일 종가 매수, 추적은 다음 거래일부터
  open_next   : 다음 거래일 시가 매수, 추적은 그 날부터 (기본값)
  close_next  : 다음 거래일 종가 매수, 추적은 그 다음 거래일부터
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import pandas as pd
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OHLCV_DIR = DATA_DIR / "ohlcv"
SIGNALS_CSV = DATA_DIR / "signals" / "all_signals.csv"
RESULTS_DIR = DATA_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# ===== 진입가 옵션 =====
ENTRY_OPTIONS = ("close_today", "open_next", "close_next")
ENTRY_LABELS = {
    "close_today": "신호 당일 종가",
    "open_next":   "다음날 시가",
    "close_next":  "다음날 종가",
}


@dataclass
class BacktestResult:
    """단일 신호의 백테스트 결과."""
    ticker: str
    name: str
    condition: str
    signal_date: pd.Timestamp
    entry_date: pd.Timestamp | None
    entry_price: float | None
    # 목표별 도달일수 (None이면 미도달, 1=다음날 도달)
    days_to_target: dict[float, int | None] = field(default_factory=dict)
    # 추적 기간 중 통계
    mdd_in_track: float | None = None       # 진입가 대비 최저점 하락률 (음수)
    final_pnl: float | None = None          # 추적 마지막 날 종가 손익률
    skipped: str | None = None              # 스킵 사유


# ===== 단일 신호 백테스트 =====
def backtest_single(
    ohlcv: pd.DataFrame,
    signal_date: pd.Timestamp,
    targets: list[float],
    entry: str = "open_next",
    track_days: int = 10,
    extra_days: int = 20,
) -> tuple[float | None, pd.Timestamp | None, dict[float, int | None], float | None, float | None, str | None]:
    """
    한 신호에 대해 백테스트 수행.
    반환: (entry_price, entry_date, days_to_target, mdd_in_track, final_pnl, skip_reason)
    """
    if signal_date not in ohlcv.index:
        return None, None, {}, None, None, "신호일이 OHLCV에 없음"

    sig_pos = ohlcv.index.get_loc(signal_date)
    total_track = track_days + extra_days

    # 진입 시점 결정
    if entry == "close_today":
        entry_pos = sig_pos
        entry_price = float(ohlcv.iloc[entry_pos]["Close"])
        track_start_pos = entry_pos + 1
    elif entry == "open_next":
        entry_pos = sig_pos + 1
        if entry_pos >= len(ohlcv):
            return None, None, {}, None, None, "다음 거래일 없음"
        entry_price = float(ohlcv.iloc[entry_pos]["Open"])
        track_start_pos = entry_pos
    elif entry == "close_next":
        entry_pos = sig_pos + 1
        if entry_pos >= len(ohlcv):
            return None, None, {}, None, None, "다음 거래일 없음"
        entry_price = float(ohlcv.iloc[entry_pos]["Close"])
        track_start_pos = entry_pos + 1
    else:
        raise ValueError(f"알 수 없는 entry: {entry}")

    if entry_price <= 0:
        return None, None, {}, None, None, "진입가 0 이하"

    entry_date = ohlcv.index[entry_pos]

    # 추적 구간 슬라이스
    track_end_pos = min(track_start_pos + total_track, len(ohlcv))
    track = ohlcv.iloc[track_start_pos:track_end_pos]
    if track.empty:
        return entry_price, entry_date, {t: None for t in targets}, None, None, "추적 데이터 없음"

    highs = track["High"].values
    lows = track["Low"].values
    closes = track["Close"].values

    # 목표별 도달일수: 1-based (1=추적 첫 날에 도달)
    days_to_target: dict[float, int | None] = {}
    for tgt in targets:
        target_price = entry_price * (1 + tgt)
        hit_idx = next((i for i, h in enumerate(highs) if h >= target_price), None)
        days_to_target[tgt] = (hit_idx + 1) if hit_idx is not None else None

    # 미도달 통계 (추적 전체 구간 기준)
    min_low = float(min(lows))
    mdd_in_track = (min_low - entry_price) / entry_price  # 음수
    final_close = float(closes[-1])
    final_pnl = (final_close - entry_price) / entry_price

    return entry_price, entry_date, days_to_target, mdd_in_track, final_pnl, None


# ===== 일괄 백테스트 =====
def load_ohlcv_cache(tickers: Iterable[str]) -> dict[str, pd.DataFrame]:
    """필요 종목들의 OHLCV를 한 번씩만 읽어 dict로 캐싱."""
    cache: dict[str, pd.DataFrame] = {}
    unique = sorted(set(tickers))
    for t in tqdm(unique, desc="OHLCV 캐싱"):
        path = OHLCV_DIR / f"{t}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path, parse_dates=["날짜"], index_col="날짜")
        df = df.sort_index()
        cache[t] = df
    return cache


def backtest_with_cache(
    signals: pd.DataFrame,
    ohlcv_cache: dict[str, pd.DataFrame],
    targets: list[float],
    entry: str = "open_next",
    track_days: int = 10,
    extra_days: int = 20,
    show_progress: bool = True,
) -> pd.DataFrame:
    """
    OHLCV cache를 외부에서 주입받는 백테스트.
    Streamlit 등에서 cache 재사용으로 속도 향상에 사용.
    """
    rows = []
    iterator = signals.iterrows()
    if show_progress:
        iterator = tqdm(iterator, total=len(signals), desc="백테스트")

    for _, r in iterator:
        ticker = str(r["티커"]).zfill(6)
        sig_date = pd.to_datetime(r["날짜"])
        df = ohlcv_cache.get(ticker)
        if df is None:
            continue

        entry_price, entry_date, dtt, mdd, fpnl, skip = backtest_single(
            df, sig_date, targets, entry=entry,
            track_days=track_days, extra_days=extra_days,
        )

        row = {
            "티커": ticker,
            "종목명": r.get("종목명", ""),
            "조건식": r["조건식"],
            "신호일": sig_date,
            "진입일": entry_date,
            "진입가": entry_price,
            "MDD": mdd,
            "최종손익": fpnl,
            "skipped": skip,
        }
        for tgt in targets:
            row[f"d_{int(tgt*100)}"] = dtt.get(tgt) if dtt else None
        rows.append(row)

    return pd.DataFrame(rows)


def backtest_all(
    signals: pd.DataFrame,
    targets: list[float],
    entry: str = "open_next",
    track_days: int = 10,
    extra_days: int = 20,
) -> pd.DataFrame:
    """
    모든 신호에 백테스트 적용. CSV에서 OHLCV를 로드하고 backtest_with_cache 호출.
    """
    print(f"[백테스트] 신호 {len(signals):,}건 / 진입: {ENTRY_LABELS[entry]} / "
          f"추적 {track_days}+{extra_days}일")

    cache = load_ohlcv_cache(signals["티커"].astype(str))
    results = backtest_with_cache(
        signals, cache, targets,
        entry=entry, track_days=track_days, extra_days=extra_days,
    )
    skipped = results["skipped"].notna().sum()
    print(f"  완료. 스킵 {skipped}건")
    return results


# ===== 결과 집계 =====
def aggregate(
    results: pd.DataFrame,
    targets: list[float],
    track_days: int = 10,
) -> pd.DataFrame:
    """
    백테스트 결과 → 목표별 도달률 매트릭스.

    columns: 목표, 신호수, 10일내, 초과도달, 미도달,
             평균도달일, 실패시MDD, 실패시평균손익
    """
    valid = results[results["skipped"].isna()].copy()
    n_total = len(valid)
    if n_total == 0:
        return pd.DataFrame()

    rows = []
    for tgt in targets:
        col = f"d_{int(tgt*100)}"
        d = valid[col]
        in_track = ((d >= 1) & (d <= track_days)).sum()
        over_track = (d > track_days).sum()
        no_hit = d.isna().sum()

        avg_days = d[d.notna()].mean() if d.notna().any() else None

        # 미도달 = d.isna() 인 케이스의 MDD/최종손익
        miss = valid[d.isna()]
        avg_mdd = miss["MDD"].mean() if len(miss) else None
        avg_loss = miss["최종손익"].mean() if len(miss) else None

        rows.append({
            "목표": f"+{int(tgt*100)}%",
            "신호수": n_total,
            f"{track_days}일내": in_track / n_total,
            "초과도달": over_track / n_total,
            "미도달": no_hit / n_total,
            "평균도달일": avg_days,
            "실패시MDD": avg_mdd,
            "실패시평균손익": avg_loss,
        })
    return pd.DataFrame(rows)


# ===== 출력 =====
def print_matrix(agg: pd.DataFrame, title: str, track_days: int = 10) -> None:
    print()
    print("=" * 78)
    print(f"  {title}")
    print("=" * 78)
    if agg.empty:
        print("  (데이터 없음)")
        return

    n = int(agg["신호수"].iloc[0])
    print(f"  신호 총 발생: {n:,}회")
    print()

    in_col = f"{track_days}일내"
    print(f"  {'목표':>6}  {in_col:>8}  {'초과도달':>10}  {'미도달':>8}  "
          f"{'평균도달일':>10}  {'실패시MDD':>10}  {'실패시평균':>10}")
    print(f"  {'-'*6}  {'-'*8}  {'-'*10}  {'-'*8}  {'-'*10}  {'-'*10}  {'-'*10}")
    for _, r in agg.iterrows():
        avg_days = f"{r['평균도달일']:>9.1f}일" if pd.notna(r['평균도달일']) else "    -"
        mdd = f"{r['실패시MDD']*100:>+9.1f}%" if pd.notna(r['실패시MDD']) else "    -"
        loss = f"{r['실패시평균손익']*100:>+9.1f}%" if pd.notna(r['실패시평균손익']) else "    -"
        print(f"  {r['목표']:>6}  "
              f"{r[in_col]*100:>7.1f}%  "
              f"{r['초과도달']*100:>9.1f}%  "
              f"{r['미도달']*100:>7.1f}%  "
              f"{avg_days:>10}  "
              f"{mdd:>10}  "
              f"{loss:>10}")


def parse_targets(s: str) -> list[float]:
    """'5,10,15,20' → [0.05, 0.10, 0.15, 0.20]"""
    return sorted(float(x) / 100 for x in s.split(",") if x.strip())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", default="all",
                        help="cond1, cond2, all (기본 all)")
    parser.add_argument("--entry", default="open_next", choices=ENTRY_OPTIONS,
                        help="진입가 옵션 (기본 open_next)")
    parser.add_argument("--targets", default="5,10,15,20",
                        help="목표 수익률 % (콤마 구분)")
    parser.add_argument("--track-days", type=int, default=10)
    parser.add_argument("--extra-days", type=int, default=20)
    parser.add_argument("--save", action="store_true",
                        help="결과 CSV로 저장")
    args = parser.parse_args()

    targets = parse_targets(args.targets)
    if not SIGNALS_CSV.exists():
        raise FileNotFoundError(f"{SIGNALS_CSV} 없음. test_signals.py 먼저 실행.")
    signals = pd.read_csv(SIGNALS_CSV, dtype={"티커": str}, parse_dates=["날짜"])
    signals["티커"] = signals["티커"].str.zfill(6)

    if args.condition != "all":
        signals = signals[signals["조건식"] == args.condition]

    conds = signals["조건식"].unique()
    for cid in conds:
        sub = signals[signals["조건식"] == cid]
        results = backtest_all(
            sub, targets,
            entry=args.entry,
            track_days=args.track_days,
            extra_days=args.extra_days,
        )
        agg = aggregate(results, targets, track_days=args.track_days)

        cname_map = {"cond1": "급등주 추격형", "cond2": "갭상승 정배열형"}
        title = (f"{cid} {cname_map.get(cid, '')} / "
                 f"진입: {ENTRY_LABELS[args.entry]} / "
                 f"추적 {args.track_days}+{args.extra_days}일")
        print_matrix(agg, title, track_days=args.track_days)

        if args.save:
            stem = f"{cid}_entry_{args.entry}_track{args.track_days}"
            results.to_csv(RESULTS_DIR / f"{stem}_raw.csv",
                           index=False, encoding="utf-8-sig")
            agg.to_csv(RESULTS_DIR / f"{stem}_matrix.csv",
                       index=False, encoding="utf-8-sig")
            print(f"\n  저장: data/results/{stem}_*.csv")


if __name__ == "__main__":
    main()
