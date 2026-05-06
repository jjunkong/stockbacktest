"""탭 3: 종목별 상세. 신호 발생 종목을 검색/선택, 캔들차트 + 신호 마킹."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_loader import load_tickers_meta
from backtest import ENTRY_LABELS
from ui import theme

ROOT = Path(__file__).resolve().parent.parent.parent
OHLCV_DIR = ROOT / "data" / "ohlcv"


def _signal_summary(results: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """종목별 신호 횟수 + 평균 도달률 요약."""
    valid = results[results["skipped"].isna()].copy()
    if valid.empty:
        return pd.DataFrame()

    # +10% 기준 도달률 계산 (없으면 첫 목표)
    target_label = "+10%"
    target_value = 10
    if 0.10 not in cfg["targets"]:
        target_value = int(cfg["targets"][0] * 100)
        target_label = f"+{target_value}%"
    col = f"d_{target_value}"

    track_days = cfg["track_days"]

    def hit_in_track(s):
        return ((s >= 1) & (s <= track_days)).sum()

    group_cols = ["티커", "종목명"]
    if "시장" in valid.columns:
        group_cols.append("시장")
    summary = valid.groupby(group_cols).agg(
        신호수=("신호일", "count"),
        도달=(col, hit_in_track),
        최근신호=("신호일", "max"),
    ).reset_index()
    summary[f"{target_label} {track_days}일내 도달률"] = (
        summary["도달"] / summary["신호수"] * 100
    ).round(1)
    summary = summary.sort_values("신호수", ascending=False)
    summary["최근신호"] = summary["최근신호"].dt.strftime("%Y-%m-%d")
    return summary


def _candle_chart(ticker: str, name: str, signals: pd.DataFrame,
                  cfg: dict) -> None:
    """종목 캔들차트 + 신호 마킹 + 진입가/목표가."""
    path = OHLCV_DIR / f"{ticker}.csv"
    if not path.exists():
        st.warning(f"{ticker} OHLCV 파일 없음")
        return

    df = pd.read_csv(path, parse_dates=["날짜"], index_col="날짜").sort_index()

    # 차트 표시 범위: 가장 최근 신호 ± 60일 (또는 마지막 6개월)
    if not signals.empty:
        last_sig = signals["신호일"].max()
        window_start = last_sig - pd.Timedelta(days=180)
        window_end = last_sig + pd.Timedelta(days=60)
        view = df.loc[window_start:window_end].copy()
    else:
        view = df.tail(150).copy()

    if view.empty:
        st.info("표시할 OHLCV 구간이 없음")
        return

    # 호버박스용 customdata 준비
    weekday_kor = ["월", "화", "수", "목", "금", "토", "일"]
    view["요일"] = [weekday_kor[d.weekday()] for d in view.index]
    view["전일종가"] = view["Close"].shift(1)
    view["등락률"] = (view["Close"] - view["전일종가"]) / view["전일종가"] * 100
    customdata = view[["요일", "Volume", "등락률"]].values

    hovertemplate = (
        "<b>%{x|%Y-%m-%d} (%{customdata[0]})</b><br>"
        "시가: %{open:,.0f}<br>"
        "고가: %{high:,.0f}<br>"
        "저가: %{low:,.0f}<br>"
        "종가: %{close:,.0f}<br>"
        "거래량: %{customdata[1]:,.0f}<br>"
        "등락률: %{customdata[2]:+.2f}%<extra></extra>"
    )

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=view.index,
        open=view["Open"], high=view["High"],
        low=view["Low"], close=view["Close"],
        name=f"{name} ({ticker})",
        increasing_line_color=theme.CANDLE_UP,
        decreasing_line_color=theme.CANDLE_DOWN,
        customdata=customdata,
        hovertemplate=hovertemplate,
    ))

    # 신호 마킹
    sig_in_view = signals[
        (signals["신호일"] >= view.index.min()) &
        (signals["신호일"] <= view.index.max())
    ]
    if not sig_in_view.empty:
        fig.add_trace(go.Scatter(
            x=sig_in_view["신호일"],
            y=[df.loc[d, "High"] * 1.03 if d in df.index else None
               for d in sig_in_view["신호일"]],
            mode="markers+text",
            marker=dict(symbol="triangle-down", size=12,
                        color=theme.SIGNAL_MARK),
            text=["신호" for _ in range(len(sig_in_view))],
            textposition="top center",
            textfont=dict(color=theme.SIGNAL_MARK, size=10),
            name="신호 발생",
        ))

        # 가장 최근 신호의 진입가/목표가 가이드
        latest = sig_in_view.iloc[-1]
        if pd.notna(latest.get("진입가")):
            entry_price = latest["진입가"]
            fig.add_hline(
                y=entry_price, line_dash="dot", line_color=theme.TEXT,
                annotation_text=f"진입가 {entry_price:,.0f}",
                annotation_position="left",
                annotation_font_color=theme.TEXT,
            )
            for tgt in cfg["targets"]:
                target_price = entry_price * (1 + tgt)
                fig.add_hline(
                    y=target_price, line_dash="dash",
                    line_color=theme.SUCCESS, opacity=0.5,
                    annotation_text=f"+{int(tgt*100)}%: {target_price:,.0f}",
                    annotation_position="right",
                    annotation_font_color=theme.SUCCESS,
                )

    theme.apply_layout(
        fig,
        title=f"{name} ({ticker}) — 일봉 + 신호",
        xaxis_title="날짜",
        yaxis_title="가격 (원)",
        height=500,
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(fixedrange=False, gridcolor=theme.BORDER, linecolor=theme.BORDER),
        yaxis=dict(fixedrange=True, gridcolor=theme.BORDER, linecolor=theme.BORDER),
        hovermode="x unified",
        dragmode="pan",
    )
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "scrollZoom": True,
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        },
    )


def _signal_history(ticker: str, signals: pd.DataFrame, cfg: dict) -> None:
    """선택 종목의 신호 이력 테이블 (목표 도달 결과 포함)."""
    if signals.empty:
        st.info("이 종목의 신호 이력 없음")
        return

    track_days = cfg["track_days"]
    out = signals[["신호일", "진입일", "진입가"]].copy()

    for tgt in cfg["targets"]:
        col = f"d_{int(tgt*100)}"
        if col in signals.columns:
            def label(v):
                if pd.isna(v):
                    return "❌ 미도달"
                if v <= track_days:
                    return f"✅ {int(v)}일"
                return f"🟡 {int(v)}일 (초과)"
            out[f"+{int(tgt*100)}%"] = signals[col].apply(label)

    out["MDD"] = signals["MDD"].apply(
        lambda x: f"{x*100:+.1f}%" if pd.notna(x) else "-"
    )
    out["최종손익"] = signals["최종손익"].apply(
        lambda x: f"{x*100:+.1f}%" if pd.notna(x) else "-"
    )
    out["진입가"] = out["진입가"].apply(
        lambda x: f"{x:,.0f}" if pd.notna(x) else "-"
    )
    out["신호일"] = out["신호일"].dt.strftime("%Y-%m-%d")
    out["진입일"] = pd.to_datetime(out["진입일"]).dt.strftime("%Y-%m-%d")
    out = out.sort_values("신호일", ascending=False)

    st.dataframe(out, use_container_width=True, hide_index=True)


def render(results: pd.DataFrame, cfg: dict) -> None:
    st.subheader(f"종목별 상세 · 진입가: {ENTRY_LABELS[cfg['entry']]}")

    valid = results[results["skipped"].isna()]
    if valid.empty:
        st.info("결과가 비어있음")
        return

    summary = _signal_summary(valid, cfg)
    if summary.empty:
        st.info("종목 요약 데이터 없음")
        return

    # 종목 검색
    search = st.text_input(
        "🔎 종목 검색 (이름 또는 티커)",
        placeholder="예: 삼성전자, 005930",
    ).strip()

    if search:
        filtered = summary[
            summary["종목명"].str.contains(search, case=False, na=False)
            | summary["티커"].str.contains(search, na=False)
        ]
    else:
        filtered = summary

    st.markdown(f"##### 신호 발생 종목 — {len(filtered):,}개")
    st.caption("표 행을 클릭하면 아래 차트에 반영됩니다.")

    selected = st.dataframe(
        filtered.head(200),
        use_container_width=True, hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    sel_rows = selected.selection.rows
    if sel_rows:
        row = filtered.iloc[sel_rows[0]]
        ticker = row["티커"]
        name = row["종목명"]
    elif len(filtered) > 0:
        ticker = filtered.iloc[0]["티커"]
        name = filtered.iloc[0]["종목명"]
    else:
        st.info("검색 결과 없음")
        return

    st.markdown(f"### 📌 {name} ({ticker})")

    sig_for_ticker = valid[valid["티커"] == ticker].sort_values("신호일")
    _candle_chart(ticker, name, sig_for_ticker, cfg)

    st.markdown("##### 신호 이력")
    _signal_history(ticker, sig_for_ticker, cfg)
