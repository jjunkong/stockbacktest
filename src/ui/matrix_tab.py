"""탭 1: 전체 매트릭스 + KPI + 차트."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_loader import get_aggregate
from backtest import ENTRY_LABELS
from ui import theme

CONDITION_LABELS = {
    "cond1": "급등주 추격형",
    "cond2": "갭상승 정배열형",
}


def _kpi_cards(results: pd.DataFrame, agg: pd.DataFrame, track_days: int) -> None:
    """상단 KPI 카드 4개."""
    valid = results[results["skipped"].isna()]
    n_total = len(valid)

    # 평균 도달률 (전체 목표의 평균 10일내 도달률)
    in_col = f"{track_days}일내"
    avg_hit_rate = agg[in_col].mean() if not agg.empty else 0

    # 전체 신호의 평균 도달일 (목표 +10% 기준 — 가장 대표적)
    if not agg.empty:
        d10 = agg[agg["목표"] == "+10%"]
        target_10_hit = (
            d10[in_col].iloc[0] if not d10.empty
            else agg[in_col].iloc[len(agg)//2]
        )
    else:
        target_10_hit = None

    avg_days = agg["평균도달일"].mean() if not agg.empty else None
    avg_mdd = agg["실패시MDD"].mean() if not agg.empty else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("신호 총 발생", f"{n_total:,}건")
    c2.metric(
        f"평균 도달률 ({track_days}일 내)",
        f"{avg_hit_rate*100:.1f}%",
        help="입력한 모든 목표 수익률의 평균",
    )
    c3.metric(
        "평균 도달일 (성공 케이스)",
        f"{avg_days:.1f}일" if avg_days else "-",
    )
    c4.metric(
        "평균 실패시 MDD",
        f"{avg_mdd*100:+.1f}%" if avg_mdd else "-",
        help="목표 미도달 케이스의 추적 기간 중 최대 낙폭",
    )


def _matrix_table(agg: pd.DataFrame, track_days: int) -> None:
    in_col = f"{track_days}일내"
    show = agg[[
        "목표", in_col, "초과도달", "미도달",
        "평균도달일", "실패시MDD", "실패시평균손익",
    ]].copy()

    show[in_col] = (show[in_col] * 100).round(1).astype(str) + "%"
    show["초과도달"] = (show["초과도달"] * 100).round(1).astype(str) + "%"
    show["미도달"] = (show["미도달"] * 100).round(1).astype(str) + "%"
    show["평균도달일"] = show["평균도달일"].apply(
        lambda x: f"{x:.1f}일" if pd.notna(x) else "-"
    )
    show["실패시MDD"] = show["실패시MDD"].apply(
        lambda x: f"{x*100:+.1f}%" if pd.notna(x) else "-"
    )
    show["실패시평균손익"] = show["실패시평균손익"].apply(
        lambda x: f"{x*100:+.1f}%" if pd.notna(x) else "-"
    )

    st.dataframe(show, use_container_width=True, hide_index=True)


def _hit_rate_bar(agg: pd.DataFrame, track_days: int) -> None:
    """목표별 도달률 막대 그래프 (10일내 / 초과 / 미도달 스택)."""
    if agg.empty:
        return

    fig = go.Figure()
    in_col = f"{track_days}일내"
    fig.add_trace(go.Bar(
        x=agg["목표"], y=agg[in_col] * 100,
        name=f"{track_days}일 내 도달", marker_color=theme.SUCCESS,
        text=[f"{v*100:.0f}%" for v in agg[in_col]],
        textposition="inside",
        textfont=dict(color="#ffffff"),
    ))
    fig.add_trace(go.Bar(
        x=agg["목표"], y=agg["초과도달"] * 100,
        name="초과 도달 (~30일)", marker_color=theme.PARTIAL,
        text=[f"{v*100:.0f}%" for v in agg["초과도달"]],
        textposition="inside",
        textfont=dict(color="#ffffff"),
    ))
    fig.add_trace(go.Bar(
        x=agg["목표"], y=agg["미도달"] * 100,
        name="미도달", marker_color=theme.FAIL,
        text=[f"{v*100:.0f}%" for v in agg["미도달"]],
        textposition="inside",
        textfont=dict(color="#ffffff"),
    ))
    theme.apply_layout(
        fig,
        barmode="stack",
        title="목표별 도달 분포",
        xaxis_title="목표 수익률",
        yaxis_title="비율 (%)",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig, use_container_width=True)


def _days_distribution(results: pd.DataFrame, targets: tuple[float, ...]) -> None:
    """목표별 도달일 분포 히스토그램."""
    valid = results[results["skipped"].isna()]
    if valid.empty:
        return

    palette = [theme.SUCCESS, theme.PARTIAL, theme.NEUTRAL, theme.FAIL]
    fig = go.Figure()
    for i, tgt in enumerate(targets):
        col = f"d_{int(tgt*100)}"
        if col not in valid.columns:
            continue
        d = valid[col].dropna()
        if d.empty:
            continue
        fig.add_trace(go.Histogram(
            x=d,
            name=f"+{int(tgt*100)}%",
            opacity=0.55,
            marker_color=palette[i % len(palette)],
            xbins=dict(start=1, end=31, size=1),
        ))
    theme.apply_layout(
        fig,
        title="목표 도달까지 걸린 일수 분포",
        xaxis_title="도달일 (거래일 기준)",
        yaxis_title="신호 수",
        barmode="overlay",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig, use_container_width=True)


def render(results: pd.DataFrame, cfg: dict) -> None:
    cond_label = CONDITION_LABELS.get(cfg["cond"], cfg["cond"])
    st.subheader(f"{cond_label} · 진입가: {ENTRY_LABELS[cfg['entry']]}")

    agg = get_aggregate(results, cfg["targets"], cfg["track_days"])

    _kpi_cards(results, agg, cfg["track_days"])
    st.markdown("##### 목표별 도달률 매트릭스")
    _matrix_table(agg, cfg["track_days"])

    col_a, col_b = st.columns(2)
    with col_a:
        _hit_rate_bar(agg, cfg["track_days"])
    with col_b:
        _days_distribution(results, cfg["targets"])

    # CSV 다운로드
    st.download_button(
        "📥 매트릭스 CSV 다운로드",
        data=agg.to_csv(index=False, encoding="utf-8-sig"),
        file_name=f"{cfg['cond']}_{cfg['entry']}_track{cfg['track_days']}_matrix.csv",
        mime="text/csv",
    )
    st.download_button(
        "📥 raw 결과 CSV 다운로드",
        data=results.to_csv(index=False, encoding="utf-8-sig"),
        file_name=f"{cfg['cond']}_{cfg['entry']}_track{cfg['track_days']}_raw.csv",
        mime="text/csv",
    )
