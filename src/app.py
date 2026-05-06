"""
한국 주식 조건검색식 백테스팅 대시보드.

실행:
    .\venv\Scripts\streamlit.exe run src\app.py
"""

from __future__ import annotations

import streamlit as st

from data_loader import (
    load_signals_all,
    load_tickers_meta,
    run_backtest,
    attach_regime,
    get_aggregate,
    filter_by_market,
)
from backtest import ENTRY_OPTIONS, ENTRY_LABELS

MARKET_OPTIONS = ("all", "KOSPI", "KOSDAQ")
MARKET_LABELS = {"all": "전체 (KOSPI+KOSDAQ)", "KOSPI": "KOSPI", "KOSDAQ": "KOSDAQ"}

CONDITION_LABELS = {
    "cond1": "급등주 추격형",
    "cond2": "갭상승 정배열형",
}


# ===== 페이지 설정 =====
st.set_page_config(
    page_title="조건식 백테스팅",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ===== 글로벌 CSS =====
# 컨셉: 화이트 베이스 + 에메랄드 그린 액센트 + 도트 패턴 배경
# 폰트: 나눔고딕 (본문), 지마켓산스 (강조/타이틀/숫자)
GLOBAL_CSS = """
<style>
/* ===== 폰트 로드 ===== */
@import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800&display=swap');

@font-face {
    font-family: 'GmarketSansMedium';
    src: url('https://gcore.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/GmarketSansMedium.woff') format('woff');
    font-weight: normal;
    font-style: normal;
}
@font-face {
    font-family: 'GmarketSansBold';
    src: url('https://gcore.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/GmarketSansBold.woff') format('woff');
    font-weight: normal;
    font-style: normal;
}

/* ===== 기본 ===== */
html, body, [class*="st-"], button, input, select, textarea, p, div, span, li {
    font-family: 'Nanum Gothic', sans-serif !important;
}

/* 메인 컨테이너 + 도트 패턴 배경 */
.stApp {
    background-color: #FFFFFF;
    background-image: radial-gradient(circle, #E5E7EB 1px, transparent 1px);
    background-size: 24px 24px;
}
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 4rem;
    max-width: 1400px;
}

/* ===== 헤딩 — GmarketSans ===== */
h1, h2, h3, h4 {
    font-family: 'GmarketSansBold', 'Nanum Gothic', sans-serif !important;
    color: #111827;
    letter-spacing: -0.01em;
}
h1 {
    font-size: 2.2rem !important;
    margin-bottom: 0.3rem !important;
}
h2 {
    font-size: 1.5rem !important;
}
h3 {
    font-size: 1.15rem !important;
    margin-top: 1.2rem !important;
}
h5 {
    font-family: 'GmarketSansMedium', 'Nanum Gothic', sans-serif !important;
    font-size: 0.95rem !important;
    color: #111827 !important;
    margin-top: 1.4rem !important;
    margin-bottom: 0.6rem !important;
}

.big-number {
    font-family: 'GmarketSansBold', sans-serif !important;
}

/* 캡션 */
.stCaption, [data-testid="stCaptionContainer"] {
    color: #6B7280 !important;
    font-size: 0.82rem !important;
    font-family: 'Nanum Gothic', sans-serif !important;
}

/* ===== KPI 카드 (st.metric) ===== */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 0.5rem;
    padding: 20px 22px 18px;
    transition: border-color 0.2s ease, transform 0.15s ease;
}
[data-testid="stMetric"]:hover {
    border-color: #10B981;
}
[data-testid="stMetric"] [data-testid="stMetricLabel"] {
    color: #6B7280 !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    font-family: 'Nanum Gothic', sans-serif !important;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-family: 'GmarketSansBold', sans-serif !important;
    font-size: 2rem !important;
    color: #111827;
    letter-spacing: -0.01em;
}
[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
}

/* ===== 사이드바 ===== */
[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E5E7EB;
}
[data-testid="stSidebar"] .stMarkdown h2 {
    font-family: 'GmarketSansBold', sans-serif !important;
    font-size: 1rem !important;
    color: #111827 !important;
}
[data-testid="stSidebar"] label {
    color: #6B7280 !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    font-family: 'Nanum Gothic', sans-serif !important;
}

/* ===== 데이터프레임 ===== */
[data-testid="stDataFrame"] {
    border: 1px solid #E5E7EB;
    border-radius: 0.5rem;
    overflow: hidden;
}

/* ===== 버튼 — 메인은 그린 ===== */
.stButton > button {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    color: #111827;
    border-radius: 0.5rem;
    padding: 0.45rem 1rem;
    font-weight: 700;
    font-size: 0.85rem;
    font-family: 'Nanum Gothic', sans-serif;
    transition: all 0.15s ease;
}
.stButton > button:hover {
    border-color: #10B981;
    color: #047857;
    background: #D1FAE5;
}
.stButton > button:focus {
    box-shadow: 0 0 0 2px rgba(16,185,129,0.2);
}

/* 다운로드 버튼 — 그린 강조 */
.stDownloadButton > button {
    background: #10B981;
    border: 1px solid #10B981;
    color: #FFFFFF;
    border-radius: 0.5rem;
    padding: 0.45rem 1rem;
    font-weight: 700;
    font-family: 'Nanum Gothic', sans-serif;
}
.stDownloadButton > button:hover {
    background: #059669;
    border-color: #059669;
}

/* ===== 탭 ===== */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 1rem;
    border-bottom: 1px solid #E5E7EB;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    padding: 0.75rem 0.4rem;
    color: #6B7280;
    font-weight: 700;
    font-size: 0.95rem;
    background: transparent !important;
    font-family: 'Nanum Gothic', sans-serif;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #10B981 !important;
    border-bottom: 2px solid #10B981 !important;
}

/* ===== 알림 박스 ===== */
[data-testid="stAlert"] {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-left: 3px solid #10B981;
    border-radius: 0.5rem;
}

/* ===== select / radio / input ===== */
[data-baseweb="select"] > div, [data-baseweb="input"] input {
    background: #FFFFFF !important;
    border-color: #E5E7EB !important;
    border-radius: 0.5rem !important;
}
[data-baseweb="select"] > div:hover {
    border-color: #10B981 !important;
}

/* slider 트랙을 그린으로 */
[data-baseweb="slider"] [role="slider"] {
    background-color: #10B981 !important;
}

/* ===== 헤더 / 푸터 정리 ===== */
[data-testid="stHeader"] { background: transparent; }
footer { visibility: hidden; }

/* ===== 그린 배지 (재사용용) ===== */
.green-badge {
    display: inline-block;
    background: #D1FAE5;
    color: #047857;
    font-size: 0.75rem;
    font-weight: 700;
    border-radius: 0.375rem;
    padding: 2px 8px;
    font-family: 'Nanum Gothic', sans-serif;
}
</style>
"""


# ===== 사이드바: 조작 패널 =====
def render_sidebar() -> dict:
    st.sidebar.markdown("## ⚙️ 백테스트 설정")

    cond = st.sidebar.selectbox(
        "조건식",
        options=list(CONDITION_LABELS.keys()),
        format_func=lambda k: f"{k} · {CONDITION_LABELS[k]}",
        index=0,
    )

    market = st.sidebar.radio(
        "시장",
        options=list(MARKET_OPTIONS),
        format_func=lambda k: MARKET_LABELS[k],
        index=0,
        horizontal=True,
    )

    entry = st.sidebar.selectbox(
        "진입가",
        options=list(ENTRY_OPTIONS),
        format_func=lambda k: ENTRY_LABELS[k],
        index=1,  # open_next 기본
    )

    track_days = st.sidebar.slider(
        "추적 기간 (일)",
        min_value=5, max_value=20, value=10, step=1,
    )
    extra_days = st.sidebar.slider(
        "초과 추적 (추가 일수)",
        min_value=0, max_value=30, value=20, step=5,
    )

    st.sidebar.markdown("##### 목표 수익률 (%)")
    targets_str = st.sidebar.text_input(
        "쉼표로 구분",
        value="5,10,15,20",
        help="예: 5,10,15,20  /  3,7,12  같이 자유 입력",
    )
    try:
        targets = tuple(sorted(set(
            float(x.strip()) / 100
            for x in targets_str.split(",")
            if x.strip()
        )))
    except ValueError:
        st.sidebar.error("목표 수익률 입력 형식이 잘못됨. 예: 5,10,15,20")
        targets = (0.05, 0.10, 0.15, 0.20)

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "캐시: 같은 설정이면 즉시 반응. 첫 실행은 5초~10초 걸림."
    )

    return {
        "cond": cond,
        "market": market,
        "entry": entry,
        "track_days": track_days,
        "extra_days": extra_days,
        "targets": targets,
    }


def render_status_card(cfg: dict, results) -> None:
    """메인 헤더 아래의 그린 박스 — '현재 분석 중' 카드."""
    valid = results[results["skipped"].isna()] if results is not None and not results.empty else None
    n_signals = len(valid) if valid is not None else 0

    # 평균 도달률 (모든 목표의 track_days 내 도달률 평균)
    avg_hit = "-"
    if valid is not None and n_signals > 0:
        track_days = cfg["track_days"]
        rates = []
        for tgt in cfg["targets"]:
            col = f"d_{int(tgt*100)}"
            if col in valid.columns:
                d = valid[col]
                rates.append(((d >= 1) & (d <= track_days)).mean())
        if rates:
            avg_hit = f"{sum(rates)/len(rates)*100:.0f}%"

    cond_label = CONDITION_LABELS.get(cfg["cond"], cfg["cond"])
    market_label = MARKET_LABELS.get(cfg["market"], cfg["market"])
    entry_label = ENTRY_LABELS.get(cfg["entry"], cfg["entry"])

    st.markdown(
        f"""
<div style="
    background: #10B981;
    color: white;
    padding: 1.5rem 2rem;
    border-radius: 0.75rem;
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 16px rgba(16, 185, 129, 0.18);
">
    <div>
        <div style="font-size: 0.85rem; opacity: 0.85; font-family: 'Nanum Gothic', sans-serif;">
            현재 분석 중
        </div>
        <div style="font-size: 1.5rem; font-family: 'GmarketSansBold', sans-serif; margin-top: 0.25rem;">
            {cond_label} · {entry_label} · 추적 {cfg['track_days']}일
        </div>
        <div style="font-size: 0.9rem; opacity: 0.85; margin-top: 0.5rem; font-family: 'Nanum Gothic', sans-serif;">
            {cfg['cond']} · {market_label} · 신호 {n_signals:,}건
        </div>
    </div>
    <div style="font-size: 3rem; font-family: 'GmarketSansBold', sans-serif; line-height: 1;">
        {avg_hit}
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


# ===== 메인 =====
def main() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    # 헤더
    col_title, col_sub = st.columns([3, 2])
    with col_title:
        st.markdown(
            "<h1>Backtest Studio</h1>"
            "<p style='color:#6B7280; margin:0; font-size:0.95rem; "
            "font-family: \"Nanum Gothic\", sans-serif;'>"
            "키움 조건검색식 신호의 N일 도달률 분석"
            "</p>",
            unsafe_allow_html=True,
        )
    with col_sub:
        st.markdown(
            "<div style='text-align:right; padding-top:1.2rem;'>"
            "<span class='green-badge'>KOSPI · KOSDAQ</span> "
            "<span class='green-badge'>5Y DAILY</span> "
            "<span class='green-badge'>v1.0</span>"
            "</div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        "<hr style='margin:1rem 0 1.5rem; border:none; "
        "border-top:1px solid #E5E7EB;'/>",
        unsafe_allow_html=True,
    )

    cfg = render_sidebar()

    # 백테스트 실행 (캐시됨)
    results = run_backtest(
        condition=cfg["cond"],
        entry=cfg["entry"],
        targets_tuple=cfg["targets"],
        track_days=cfg["track_days"],
        extra_days=cfg["extra_days"],
    )

    if results.empty:
        st.warning("백테스트 결과가 비어있음. 조건/데이터 확인 필요.")
        return

    # 시장 필터 적용
    results = filter_by_market(results, cfg["market"])
    if results.empty:
        st.warning(f"{MARKET_LABELS[cfg['market']]} 시장에 신호가 없습니다.")
        return

    # 그린 박스 카드 — '현재 분석 중'
    render_status_card(cfg, results)

    # 탭 구성: 날짜별 분석을 첫 탭으로
    tab_date, tab_matrix, tab_regime, tab_detail = st.tabs([
        "📅 날짜별 분석",
        "📊 전체 매트릭스",
        "🌗 장세별 비교",
        "🔍 종목별 상세",
    ])

    from ui import date_tab, matrix_tab, regime_tab, detail_tab

    with tab_date:
        date_tab.render(results, cfg)
    with tab_matrix:
        matrix_tab.render(results, cfg)
    with tab_regime:
        regime_tab.render(results, cfg)
    with tab_detail:
        detail_tab.render(results, cfg)


if __name__ == "__main__":
    main()
