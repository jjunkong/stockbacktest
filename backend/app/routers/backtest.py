"""백테스트 메인 라우터 — /backtest 일가."""

from __future__ import annotations

from datetime import date as Date

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.core.backtest import ENTRY_LABELS
from app.core.conditions import CONDITIONS
from app.core.market_regime import load_kospi_regime
from app.core.backtest import aggregate
from app.schemas.backtest import (
    BacktestRequest,
    BacktestResponse,
    MatrixRow,
    SignalResult,
    DateBundleResponse,
    DateBundleStat,
    RegimeComparisonResponse,
    RegimeMatrix,
    TickerSummaryResponse,
    TickerSummaryRow,
)
from app.services.backtest_service import run_backtest, get_aggregate_for

router = APIRouter(prefix="/backtest", tags=["backtest"])


def _matrix_rows(agg: pd.DataFrame, track_days: int) -> list[MatrixRow]:
    if agg.empty:
        return []
    in_col = f"{track_days}일내"
    out: list[MatrixRow] = []
    for _, r in agg.iterrows():
        out.append(MatrixRow(
            target=r["목표"],
            n_signals=int(r["신호수"]),
            in_track_rate=float(r[in_col]),
            over_track_rate=float(r["초과도달"]),
            miss_rate=float(r["미도달"]),
            avg_days_to_hit=r["평균도달일"] if pd.notna(r["평균도달일"]) else None,
            avg_mdd_on_miss=r["실패시MDD"] if pd.notna(r["실패시MDD"]) else None,
            avg_pnl_on_miss=r["실패시평균손익"] if pd.notna(r["실패시평균손익"]) else None,
            miss_rate_no_day1=(
                r["1일차미도달시미달성률"]
                if pd.notna(r["1일차미도달시미달성률"]) else None
            ),
        ))
    return out


def _signal_results(results: pd.DataFrame, targets: list[float]) -> list[SignalResult]:
    from app.services.theme_store import theme_store

    out: list[SignalResult] = []
    for _, r in results.iterrows():
        days_map: dict[str, int | None] = {}
        for t in targets:
            col = f"d_{int(t*100)}"
            v = r.get(col)
            days_map[str(int(t * 100))] = int(v) if pd.notna(v) else None

        ticker = str(r["티커"])
        themes = theme_store.themes_for_ticker(ticker)

        out.append(SignalResult(
            ticker=ticker,
            name=str(r.get("종목명", "")),
            market=r.get("시장"),
            condition=str(r["조건식"]),
            signal_date=pd.to_datetime(r["신호일"]).date(),
            entry_date=pd.to_datetime(r["진입일"]).date() if pd.notna(r.get("진입일")) else None,
            entry_price=float(r["진입가"]) if pd.notna(r.get("진입가")) else None,
            days_to_target=days_map,
            mdd=float(r["MDD"]) if pd.notna(r.get("MDD")) else None,
            final_pnl=float(r["최종손익"]) if pd.notna(r.get("최종손익")) else None,
            skipped=r.get("skipped") if pd.notna(r.get("skipped")) else None,
            signal_close=float(r["신호종가"]) if pd.notna(r.get("신호종가")) else None,
            signal_change_rate=float(r["신호등락률"]) if pd.notna(r.get("신호등락률")) else None,
            signal_volume=int(r["신호거래량"]) if pd.notna(r.get("신호거래량")) else None,
            signal_amount=float(r["신호거래대금"]) if pd.notna(r.get("신호거래대금")) else None,
            signal_market_cap=float(r["신호시총"]) if pd.notna(r.get("신호시총")) else None,
            themes=themes,
        ))
    return out


# ===== POST /backtest — 메인 =====
@router.post("", response_model=BacktestResponse)
def post_backtest(req: BacktestRequest) -> BacktestResponse:
    targets = tuple(sorted(set(req.targets)))
    results = run_backtest(
        condition=req.condition, market=req.market, entry=req.entry,
        track_days=req.track_days, extra_days=req.extra_days, targets=targets,
    )
    if results.empty:
        raise HTTPException(404, "해당 조건/시장에 신호가 없음")

    valid = results[results["skipped"].isna()]
    agg = aggregate(valid, list(targets), track_days=req.track_days)
    matrix = _matrix_rows(agg, req.track_days)

    in_col = f"{req.track_days}일내"
    avg_hit = float(agg[in_col].mean()) if not agg.empty else 0.0

    cond_label = CONDITIONS.get(req.condition, (req.condition, None))[0]

    return BacktestResponse(
        condition=req.condition,
        condition_label=cond_label,
        market=req.market,
        entry=req.entry,
        entry_label=ENTRY_LABELS[req.entry],
        track_days=req.track_days,
        extra_days=req.extra_days,
        targets=list(targets),
        n_signals=int(len(valid)),
        avg_hit_rate=avg_hit,
        matrix=matrix,
    )


# ===== GET /backtest/signal-dates =====
@router.get("/signal-dates", response_model=list[Date])
def get_signal_dates(
    condition: str = Query(...),
    market: str = "all",
    entry: str = "open_next",
    track_days: int = 10,
    extra_days: int = 20,
    targets: str = Query("5,10,15,20"),
) -> list[Date]:
    """해당 조건/시장 기준 신호 발생일 목록 (최신순)."""
    tgt_list = tuple(sorted({float(x.strip())/100 for x in targets.split(",") if x.strip()}))
    results = run_backtest(condition, market, entry, track_days, extra_days, tgt_list)
    if results.empty:
        return []
    valid = results[results["skipped"].isna()]
    if valid.empty:
        return []
    dates = pd.to_datetime(valid["신호일"]).dt.normalize().unique()
    return sorted([d.date() for d in pd.DatetimeIndex(dates)], reverse=True)


# ===== GET /backtest/date-bundle =====
@router.get("/date-bundle", response_model=DateBundleResponse)
def get_date_bundle(
    date: Date = Query(...),
    condition: str = Query(...),
    market: str = "all",
    entry: str = "open_next",
    track_days: int = 10,
    extra_days: int = 20,
    targets: str = Query("5,10,15,20"),
) -> DateBundleResponse:
    """특정 날짜의 신호 묶음 통계 + 개별 종목 결과."""
    tgt_list = tuple(sorted({float(x.strip())/100 for x in targets.split(",") if x.strip()}))
    results = run_backtest(condition, market, entry, track_days, extra_days, tgt_list)
    if results.empty:
        raise HTTPException(404, "해당 조건/시장에 신호 없음")
    valid = results[results["skipped"].isna()].copy()
    valid["_d"] = pd.to_datetime(valid["신호일"]).dt.normalize()
    pick = pd.Timestamp(date)
    group = valid[valid["_d"] == pick].drop(columns=["_d"])

    if group.empty:
        return DateBundleResponse(date=date, n_signals=0, bundle_stats=[], individuals=[])

    n = len(group)
    stats: list[DateBundleStat] = []
    for tgt in tgt_list:
        col = f"d_{int(tgt*100)}"
        d = group[col]
        in_track = int(((d >= 1) & (d <= track_days)).sum())
        over = int((d > track_days).sum())
        miss = int(d.isna().sum())
        avg_d = float(d[d.notna()].mean()) if d.notna().any() else None
        stats.append(DateBundleStat(
            target=f"+{int(tgt*100)}%",
            hit_count=in_track, over_count=over, miss_count=miss,
            total=n, hit_rate=in_track / n,
            avg_days_to_hit=avg_d,
        ))

    individuals = _signal_results(group, list(tgt_list))
    return DateBundleResponse(
        date=date, n_signals=n,
        bundle_stats=stats, individuals=individuals,
    )


# ===== GET /backtest/regime-comparison =====
@router.get("/regime-comparison", response_model=RegimeComparisonResponse)
def get_regime_comparison(
    condition: str = Query(...),
    market: str = "all",
    entry: str = "open_next",
    track_days: int = 10,
    extra_days: int = 20,
    targets: str = Query("5,10,15,20"),
    ma_window: int = 60,
) -> RegimeComparisonResponse:
    """장세별(상승장/하락장) 매트릭스 비교."""
    tgt_list = tuple(sorted({float(x.strip())/100 for x in targets.split(",") if x.strip()}))
    results = run_backtest(condition, market, entry, track_days, extra_days, tgt_list)
    if results.empty:
        raise HTTPException(404, "신호 없음")

    valid = results[results["skipped"].isna()].copy()
    if valid.empty:
        raise HTTPException(404, "유효 신호 없음")

    start = valid["신호일"].min().strftime("%Y-%m-%d")
    end = valid["신호일"].max().strftime("%Y-%m-%d")
    regime = load_kospi_regime(start, end, ma_window)

    valid["_d"] = pd.to_datetime(valid["신호일"]).dt.normalize()
    merged = valid.merge(regime[["Regime"]], left_on="_d", right_index=True, how="left")
    merged["Regime"] = merged["Regime"].fillna("unknown")

    distribution: dict[str, int] = (
        merged["Regime"].value_counts().to_dict()
    )
    distribution = {k: int(v) for k, v in distribution.items()}

    label_kor = {"bull": "상승장", "bear": "하락장"}
    out_regimes: list[RegimeMatrix] = []
    for label in ("bull", "bear"):
        sub = merged[merged["Regime"] == label]
        if sub.empty:
            continue
        agg = aggregate(sub, list(tgt_list), track_days=track_days)
        out_regimes.append(RegimeMatrix(
            regime=label,
            regime_label=label_kor[label],
            n_signals=len(sub),
            rows=_matrix_rows(agg, track_days),
        ))

    return RegimeComparisonResponse(
        condition=condition, market=market, entry=entry,
        track_days=track_days, distribution=distribution, regimes=out_regimes,
    )


# ===== GET /backtest/ticker-summary =====
@router.get("/ticker-summary", response_model=TickerSummaryResponse)
def get_ticker_summary(
    condition: str = Query(...),
    market: str = "all",
    entry: str = "open_next",
    track_days: int = 10,
    extra_days: int = 20,
    target_pct: int = Query(10, ge=1, le=100),
) -> TickerSummaryResponse:
    """종목별 신호 횟수 + 도달률 요약."""
    tgt = target_pct / 100.0
    results = run_backtest(condition, market, entry, track_days, extra_days, (tgt,))
    if results.empty:
        return TickerSummaryResponse(target_pct=target_pct, track_days=track_days, rows=[])

    valid = results[results["skipped"].isna()]
    col = f"d_{target_pct}"
    if col not in valid.columns:
        return TickerSummaryResponse(target_pct=target_pct, track_days=track_days, rows=[])

    def hit_in_track(s):
        return int(((s >= 1) & (s <= track_days)).sum())

    cols = ["티커", "종목명"]
    if "시장" in valid.columns:
        cols.append("시장")

    summary = valid.groupby(cols).agg(
        신호수=("신호일", "count"),
        도달=(col, hit_in_track),
        최근=("신호일", "max"),
    ).reset_index()
    summary = summary.sort_values("신호수", ascending=False)

    rows: list[TickerSummaryRow] = []
    for _, r in summary.iterrows():
        n = int(r["신호수"])
        hit = int(r["도달"])
        rows.append(TickerSummaryRow(
            ticker=str(r["티커"]),
            name=str(r["종목명"]),
            market=r.get("시장"),
            n_signals=n,
            n_hit=hit,
            hit_rate=hit / n if n else 0.0,
            last_signal=pd.to_datetime(r["최근"]).date(),
        ))
    return TickerSummaryResponse(target_pct=target_pct, track_days=track_days, rows=rows)
