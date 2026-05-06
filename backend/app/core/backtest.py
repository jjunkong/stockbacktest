"""
백테스팅 엔진 (FastAPI 백엔드용 — CLI 부분 제거).

진입가 옵션:
  close_today : 신호 당일 종가 매수, 추적은 다음 거래일부터
  open_next   : 다음 거래일 시가 매수, 추적은 그 날부터 (기본값)
  close_next  : 다음 거래일 종가 매수, 추적은 그 다음 거래일부터
"""

from __future__ import annotations

import pandas as pd

ENTRY_OPTIONS = ("close_today", "open_next", "close_next")
ENTRY_LABELS = {
    "close_today": "신호 당일 종가",
    "open_next":   "다음날 시가",
    "close_next":  "다음날 종가",
}


def backtest_single(
    ohlcv: pd.DataFrame,
    signal_date: pd.Timestamp,
    targets: list[float],
    entry: str = "open_next",
    track_days: int = 10,
    extra_days: int = 20,
) -> tuple:
    """반환: (entry_price, entry_date, days_to_target, mdd_in_track, final_pnl, skip_reason)"""
    if signal_date not in ohlcv.index:
        return None, None, {}, None, None, "신호일이 OHLCV에 없음"

    sig_pos = ohlcv.index.get_loc(signal_date)
    total_track = track_days + extra_days

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
    track_end_pos = min(track_start_pos + total_track, len(ohlcv))
    track = ohlcv.iloc[track_start_pos:track_end_pos]
    if track.empty:
        return entry_price, entry_date, {t: None for t in targets}, None, None, "추적 데이터 없음"

    highs = track["High"].values
    lows = track["Low"].values
    closes = track["Close"].values

    days_to_target: dict[float, int | None] = {}
    for tgt in targets:
        target_price = entry_price * (1 + tgt)
        hit_idx = next((i for i, h in enumerate(highs) if h >= target_price), None)
        days_to_target[tgt] = (hit_idx + 1) if hit_idx is not None else None

    min_low = float(min(lows))
    mdd_in_track = (min_low - entry_price) / entry_price
    final_close = float(closes[-1])
    final_pnl = (final_close - entry_price) / entry_price

    return entry_price, entry_date, days_to_target, mdd_in_track, final_pnl, None


def backtest_with_cache(
    signals: pd.DataFrame,
    ohlcv_cache: dict[str, pd.DataFrame],
    targets: list[float],
    entry: str = "open_next",
    track_days: int = 10,
    extra_days: int = 20,
    shares_map: dict[str, int] | None = None,
) -> pd.DataFrame:
    """
    OHLCV cache를 외부에서 주입받는 백테스트.

    shares_map: 티커 → 상장주식수 dict (시점별 시총 근사용).
                None이면 시총 컬럼은 채우지 않음.
    """
    rows = []
    for _, r in signals.iterrows():
        ticker = str(r["티커"]).zfill(6)
        sig_date = pd.to_datetime(r["날짜"])
        df = ohlcv_cache.get(ticker)
        if df is None:
            continue

        entry_price, entry_date, dtt, mdd, fpnl, skip = backtest_single(
            df, sig_date, targets, entry=entry,
            track_days=track_days, extra_days=extra_days,
        )

        # 신호 발생일 보조 정보
        sig_close = sig_volume = sig_amount = sig_change = sig_mcap = None
        if sig_date in df.index:
            row_sig = df.loc[sig_date]
            sig_close = float(row_sig["Close"])
            sig_volume = int(row_sig["Volume"])
            sig_amount = sig_close * sig_volume
            # 등락률 = 전일 종가 대비
            pos = df.index.get_loc(sig_date)
            if pos > 0:
                prev_close = float(df.iloc[pos - 1]["Close"])
                if prev_close > 0:
                    sig_change = (sig_close - prev_close) / prev_close
            # 시총 = 종가 × 상장주식수
            shares = (shares_map or {}).get(ticker)
            if shares and shares > 0:
                sig_mcap = sig_close * shares

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
            "신호종가": sig_close,
            "신호등락률": sig_change,
            "신호거래량": sig_volume,
            "신호거래대금": sig_amount,
            "신호시총": sig_mcap,
        }
        for tgt in targets:
            row[f"d_{int(tgt*100)}"] = dtt.get(tgt) if dtt else None
        rows.append(row)

    return pd.DataFrame(rows)


def aggregate(
    results: pd.DataFrame,
    targets: list[float],
    track_days: int = 10,
) -> pd.DataFrame:
    """결과 → 목표별 도달률 매트릭스."""
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
        miss = valid[d.isna()]
        avg_mdd = miss["MDD"].mean() if len(miss) else None
        avg_loss = miss["최종손익"].mean() if len(miss) else None

        # 1일차에 도달하지 못한 케이스 중, 결국 끝까지 미달성한 비율
        # = "신호 당일/다음날 한 번에 못 닿으면 결국 못 갈 확률"
        # 분모: 1일차 미도달 (d != 1, NaN 포함). 분자: 끝까지 미달성 (d.isna())
        not_day1 = ((d.isna()) | (d > 1)).sum()
        miss_rate_no_day1 = (no_hit / not_day1) if not_day1 > 0 else None

        rows.append({
            "목표": f"+{int(tgt*100)}%",
            "신호수": int(n_total),
            f"{track_days}일내": float(in_track / n_total),
            "초과도달": float(over_track / n_total),
            "미도달": float(no_hit / n_total),
            "평균도달일": float(avg_days) if avg_days is not None else None,
            "실패시MDD": float(avg_mdd) if avg_mdd is not None and not pd.isna(avg_mdd) else None,
            "실패시평균손익": float(avg_loss) if avg_loss is not None and not pd.isna(avg_loss) else None,
            "1일차미도달시미달성률": (
                float(miss_rate_no_day1) if miss_rate_no_day1 is not None else None
            ),
        })
    return pd.DataFrame(rows)
