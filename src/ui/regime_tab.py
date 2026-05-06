"""탭 2: 장세별 비교 (코스피 60일 이평 기준 상승장/하락장)."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_loader import attach_regime, get_aggregate, load_signals_all
from market_regime import load_kospi_regime
from backtest import ENTRY_LABELS
from ui import theme

CONDITION_LABELS = {
    "cond1": "급등주 추격형",
    "cond2": "갭상승 정배열형",
}
REGIME_LABEL = {"bull": "상승장", "bear": "하락장", "unknown": "분류불가"}
REGIME_COLOR = {"bull": theme.BULL, "bear": theme.BEAR}


def _regime_distribution(merged: pd.DataFrame) -> None:
    counts = merged["Regime"].value_counts()
    cols = st.columns(len(counts))
    for col, (label, n) in zip(cols, counts.items()):
        col.metric(
            f"{REGIME_LABEL.get(label, label)}",
            f"{n:,}건",
            delta=f"{n/len(merged)*100:.1f}%",
            delta_color="off",
        )


def _comparison_table(merged: pd.DataFrame, cfg: dict) -> None:
    """상승장/하락장 매트릭스를 나란히."""
    in_col = f"{cfg['track_days']}일내"
    rows = []
    for label in ("bull", "bear"):
        sub = merged[merged["Regime"] == label]
        if sub.empty:
            continue
        agg = get_aggregate(sub, cfg["targets"], cfg["track_days"])
        for _, r in agg.iterrows():
            rows.append({
                "장세": REGIME_LABEL[label],
                "목표": r["목표"],
                in_col: f"{r[in_col]*100:.1f}%",
                "초과도달": f"{r['초과도달']*100:.1f}%",
                "미도달": f"{r['미도달']*100:.1f}%",
                "평균도달일": f"{r['평균도달일']:.1f}일" if pd.notna(r["평균도달일"]) else "-",
                "실패시MDD": f"{r['실패시MDD']*100:+.1f}%" if pd.notna(r["실패시MDD"]) else "-",
                "실패시평균손익": f"{r['실패시평균손익']*100:+.1f}%" if pd.notna(r["실패시평균손익"]) else "-",
            })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _comparison_bar(merged: pd.DataFrame, cfg: dict) -> None:
    """상승장 vs 하락장 도달률 비교 막대."""
    in_col = f"{cfg['track_days']}일내"
    fig = go.Figure()
    for label in ("bull", "bear"):
        sub = merged[merged["Regime"] == label]
        if sub.empty:
            continue
        agg = get_aggregate(sub, cfg["targets"], cfg["track_days"])
        if agg.empty:
            continue
        fig.add_trace(go.Bar(
            x=agg["목표"], y=agg[in_col] * 100,
            name=REGIME_LABEL[label],
            marker_color=REGIME_COLOR[label],
            text=[f"{v*100:.1f}%" for v in agg[in_col]],
            textposition="outside",
        ))
    theme.apply_layout(
        fig,
        title=f"장세별 {cfg['track_days']}일 내 도달률 비교",
        xaxis_title="목표 수익률",
        yaxis_title="도달률 (%)",
        barmode="group",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig, use_container_width=True)


def _kospi_with_signals(merged: pd.DataFrame) -> None:
    """코스피 지수 + 신호 발생 시점 점 찍기."""
    if merged.empty:
        return
    start = merged["신호일"].min().strftime("%Y-%m-%d")
    end = merged["신호일"].max().strftime("%Y-%m-%d")
    kospi = load_kospi_regime(start, end, ma_window=60).reset_index()

    fig = go.Figure()
    # 코스피 지수 라인
    fig.add_trace(go.Scatter(
        x=kospi["Date"], y=kospi["Close"],
        mode="lines", name="코스피 지수",
        line=dict(color=theme.KOSPI_LINE, width=1.5),
    ))
    # 60일 이평
    fig.add_trace(go.Scatter(
        x=kospi["Date"], y=kospi["MA"],
        mode="lines", name="60일 이평",
        line=dict(color=theme.MA_LINE, width=1, dash="dash"),
    ))
    # 신호 발생 빈도 (월별)
    monthly = (
        merged.assign(month=merged["신호일"].dt.to_period("M"))
        .groupby("month").size()
    )
    if not monthly.empty:
        monthly.index = monthly.index.to_timestamp()
        fig.add_trace(go.Bar(
            x=monthly.index, y=monthly.values,
            name="월별 신호 수",
            marker_color="rgba(154, 148, 138, 0.35)",
            yaxis="y2",
        ))

    theme.apply_layout(
        fig,
        title="코스피 지수와 신호 발생 분포",
        xaxis_title="날짜",
        yaxis=dict(title="코스피 지수", gridcolor=theme.BORDER),
        yaxis2=dict(title="월별 신호 수", overlaying="y", side="right",
                    gridcolor=theme.BORDER),
        height=450,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig, use_container_width=True)


def render(results: pd.DataFrame, cfg: dict) -> None:
    cond_label = CONDITION_LABELS.get(cfg["cond"], cfg["cond"])
    st.subheader(f"{cond_label} · 진입가: {ENTRY_LABELS[cfg['entry']]} · 장세별 비교")

    merged = attach_regime(results)
    valid = merged[merged["skipped"].isna()]

    if valid.empty:
        st.info("백테스트 결과가 없어 장세별 분석을 표시할 수 없습니다.")
        return

    st.markdown("##### 장세 분포 (코스피 60일 이평 기준)")
    _regime_distribution(valid)

    st.markdown("##### 장세별 매트릭스")
    _comparison_table(valid, cfg)

    col_a, col_b = st.columns([1, 2])
    with col_a:
        _comparison_bar(valid, cfg)
    with col_b:
        _kospi_with_signals(valid)
