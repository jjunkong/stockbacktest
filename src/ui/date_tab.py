"""
탭: 📅 날짜별 분석 (메인 화면)

특정 날짜를 선택하면, 그 날 발생한 신호 종목 묶음을 보여주고
며칠 안에 목표 수익률에 도달했는지 묶음 통계 + 개별 결과를 표시.

사용 시나리오:
  "2024-08-12에 cond1이 5종목 잡았는데, 그 중 +10% 도달은 며칠 후 몇 개?"
"""

from __future__ import annotations

from pathlib import Path
import datetime as dt

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backtest import ENTRY_LABELS
from ui import theme

ROOT = Path(__file__).resolve().parent.parent.parent
OHLCV_DIR = ROOT / "data" / "ohlcv"

CONDITION_LABELS = {
    "cond1": "급등주 추격형",
    "cond2": "갭상승 정배열형",
}


def _signal_dates(results: pd.DataFrame) -> list[dt.date]:
    """신호가 발생한 모든 날짜 (정렬, 중복 제거)."""
    valid = results[results["skipped"].isna()]
    if valid.empty:
        return []
    dates = pd.to_datetime(valid["신호일"]).dt.normalize().unique()
    return sorted([d.date() for d in dates], reverse=True)


def _bundle_stats(group: pd.DataFrame, targets: tuple[float, ...],
                  track_days: int) -> pd.DataFrame:
    """선택된 날짜의 신호 묶음 통계."""
    n = len(group)
    rows = []
    for tgt in targets:
        col = f"d_{int(tgt*100)}"
        if col not in group.columns:
            continue
        d = group[col]
        in_track = ((d >= 1) & (d <= track_days)).sum()
        over_track = (d > track_days).sum()
        no_hit = d.isna().sum()
        rows.append({
            "목표": f"+{int(tgt*100)}%",
            "달성": f"{in_track}/{n} ({in_track/n*100:.0f}%)",
            "초과달성": f"{over_track}/{n} ({over_track/n*100:.0f}%)",
            "미달성": f"{no_hit}/{n} ({no_hit/n*100:.0f}%)",
            "평균도달일": (
                f"{d[d.notna()].mean():.1f}일"
                if d.notna().any() else "-"
            ),
        })
    return pd.DataFrame(rows)


def _individual_table(group: pd.DataFrame, targets: tuple[float, ...],
                      track_days: int) -> pd.DataFrame:
    """선택된 날짜의 개별 종목 결과."""
    rows = []
    for _, r in group.iterrows():
        row = {
            "티커": r["티커"],
            "종목명": r["종목명"],
            "시장": r.get("시장", ""),
            "진입가": (f"{r['진입가']:,.0f}원"
                      if pd.notna(r.get("진입가")) else "-"),
        }
        for tgt in targets:
            col = f"d_{int(tgt*100)}"
            if col not in group.columns:
                continue
            v = r[col]
            label_col = f"+{int(tgt*100)}%"
            if pd.isna(v):
                row[label_col] = "❌"
            elif v <= track_days:
                row[label_col] = f"✅ {int(v)}일"
            else:
                row[label_col] = f"🟡 {int(v)}일"
        row["MDD"] = (f"{r['MDD']*100:+.1f}%"
                      if pd.notna(r.get("MDD")) else "-")
        row["최종손익"] = (f"{r['최종손익']*100:+.1f}%"
                          if pd.notna(r.get("최종손익")) else "-")
        rows.append(row)
    return pd.DataFrame(rows)


def _candle_with_signal(ticker: str, name: str, signal_date: pd.Timestamp,
                        entry_price: float | None,
                        targets: tuple[float, ...]) -> None:
    """특정 신호 한 건의 캔들차트 (신호 ± 기간) + 인터랙션."""
    path = OHLCV_DIR / f"{ticker}.csv"
    if not path.exists():
        st.warning(f"{ticker} OHLCV 파일 없음")
        return

    df = pd.read_csv(path, parse_dates=["날짜"], index_col="날짜").sort_index()
    window_start = signal_date - pd.Timedelta(days=90)
    window_end = signal_date + pd.Timedelta(days=60)
    view = df.loc[window_start:window_end].copy()

    if view.empty:
        st.info("표시할 데이터 없음")
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
        name=f"{name}",
        increasing_line_color=theme.CANDLE_UP,
        decreasing_line_color=theme.CANDLE_DOWN,
        customdata=customdata,
        hovertemplate=hovertemplate,
    ))

    # 신호일 마킹
    if signal_date in df.index:
        sig_high = float(df.loc[signal_date, "High"])
        fig.add_trace(go.Scatter(
            x=[signal_date], y=[sig_high * 1.03],
            mode="markers+text",
            marker=dict(symbol="triangle-down", size=14,
                        color=theme.SIGNAL_MARK),
            text=["신호"],
            textposition="top center",
            textfont=dict(color=theme.SIGNAL_MARK, size=11),
            name="신호 발생",
            showlegend=True,
        ))

    # 진입가 + 목표가 라인
    if entry_price and entry_price > 0:
        fig.add_hline(
            y=entry_price, line_dash="dot", line_color=theme.TEXT,
            annotation_text=f"진입가 {entry_price:,.0f}",
            annotation_position="left",
            annotation_font_color=theme.TEXT,
        )
        for tgt in targets:
            target_price = entry_price * (1 + tgt)
            fig.add_hline(
                y=target_price, line_dash="dash",
                line_color=theme.SUCCESS, opacity=0.55,
                annotation_text=f"+{int(tgt*100)}%: {target_price:,.0f}",
                annotation_position="right",
                annotation_font_color=theme.SUCCESS,
            )

    theme.apply_layout(
        fig,
        title=f"{name} ({ticker}) — 신호일 {signal_date.date()} ± 추적",
        xaxis_title="날짜", yaxis_title="가격 (원)",
        height=480,
        xaxis_rangeslider_visible=False,
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


def render(results: pd.DataFrame, cfg: dict) -> None:
    cond_label = CONDITION_LABELS.get(cfg["cond"], cfg["cond"])
    market_label = {"all": "전체", "KOSPI": "KOSPI", "KOSDAQ": "KOSDAQ"}.get(
        cfg.get("market", "all"), cfg.get("market", "all")
    )
    st.subheader(
        f"📅 {cond_label} · {market_label} · 진입: {ENTRY_LABELS[cfg['entry']]}"
    )

    valid = results[results["skipped"].isna()].copy()
    if valid.empty:
        st.info("이 조건/시장 조합에 신호가 없습니다.")
        return

    # ===== 1) 날짜 선택 =====
    available_dates = _signal_dates(valid)
    if not available_dates:
        st.info("신호 발생 날짜가 없습니다.")
        return

    col_left, col_right = st.columns([1, 2])
    with col_left:
        # 사용자가 캘린더에서 임의 날짜 선택 가능. 신호 없는 날엔 빈 결과.
        picked = st.date_input(
            "분석할 날짜 선택",
            value=available_dates[0],
            min_value=available_dates[-1],
            max_value=available_dates[0],
            help=f"신호 발생일 {len(available_dates):,}개 중 선택",
        )
    with col_right:
        st.markdown("##### 또는 신호 발생일에서 골라오기")
        # 가장 최근 신호일 5개 빠른 선택 버튼
        quick_dates = available_dates[:5]
        cols = st.columns(len(quick_dates))
        for i, d in enumerate(quick_dates):
            if cols[i].button(d.strftime("%m-%d"),
                              key=f"qd_{i}",
                              use_container_width=True):
                picked = d

    pick_dt = pd.Timestamp(picked)
    valid["_d"] = pd.to_datetime(valid["신호일"]).dt.normalize()
    group = valid[valid["_d"] == pick_dt].drop(columns=["_d"])

    if group.empty:
        st.warning(f"{picked} 에 발생한 신호가 없습니다.")
        nearest = min(available_dates, key=lambda x: abs(x - picked))
        st.caption(f"가장 가까운 신호 발생일: **{nearest}** (위 캘린더에서 선택해보세요)")
        return

    # ===== 2) 묶음 통계 =====
    n = len(group)
    st.markdown(f"### {pick_dt.date()} — 신호 발생 {n}종목")

    if n == 1:
        st.caption("이 날은 1종목만 잡혔어요. 묶음 통계는 의미가 적지만 개별 결과를 확인할 수 있습니다.")

    bundle = _bundle_stats(group, cfg["targets"], cfg["track_days"])
    st.markdown(f"##### 📊 묶음 통계 (추적 {cfg['track_days']}일 기준)")
    st.dataframe(bundle, use_container_width=True, hide_index=True)

    # ===== 3) 개별 종목 결과 =====
    st.markdown("##### 📋 개별 종목 결과")
    indiv = _individual_table(group, cfg["targets"], cfg["track_days"])

    selected = st.dataframe(
        indiv, use_container_width=True, hide_index=True,
        on_select="rerun", selection_mode="single-row",
    )

    # ===== 4) 선택 종목 차트 =====
    sel_rows = selected.selection.rows
    if sel_rows:
        sel = group.iloc[sel_rows[0]]
    else:
        sel = group.iloc[0]
        st.caption("아래는 첫 번째 종목입니다. 위 표에서 다른 종목 행을 클릭하면 차트가 바뀝니다.")

    st.markdown(f"### 📈 {sel['종목명']} ({sel['티커']}) · {sel.get('시장','')}")
    _candle_with_signal(
        ticker=sel["티커"],
        name=sel["종목명"],
        signal_date=pd.Timestamp(sel["신호일"]),
        entry_price=sel.get("진입가"),
        targets=cfg["targets"],
    )
