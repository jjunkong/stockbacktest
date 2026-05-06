"""디자인 토큰 — 모든 탭에서 import해서 사용.

테마: White Base + Emerald Green Accent + Dot Pattern Background
"""

# ===== 컬러 팔레트 =====

# 베이스
BG = "#FFFFFF"            # 페이지 배경 (화이트)
CARD = "#FFFFFF"          # 카드 배경
TEXT = "#111827"          # 주 텍스트
TEXT_SUB = "#6B7280"      # 보조 텍스트
BORDER = "#E5E7EB"        # 옅은 보더/구분선
BORDER_STRONG = "#10B981" # 강조 보더 (그린)

# 그린 액센트
SUCCESS = "#10B981"       # 메인 에메랄드 그린
ACCENT_DARK = "#059669"   # 호버용 진한 그린
ACCENT_LIGHT_BG = "#D1FAE5"  # 배지 배경 (옅은 그린)
ACCENT_TEXT = "#047857"   # 그린 텍스트

# 상태 컬러
PARTIAL = "#F59E0B"       # 앰버 (초과 도달)
FAIL = "#EF4444"          # 레드 (미도달)
NEUTRAL = "#9CA3AF"       # 중립 그레이

# 시장
BULL = "#10B981"          # 상승장 = 그린
BEAR = "#EF4444"          # 하락장 = 레드

# 차트 보조
KOSPI_LINE = "#111827"
MA_LINE = "#9CA3AF"
SIGNAL_MARK = "#F59E0B"   # 신호 마킹 (앰버)

# 캔들 (한국식 유지)
CANDLE_UP = "#EF4444"     # 양봉 = 빨강
CANDLE_DOWN = "#3B82F6"   # 음봉 = 파랑


PLOTLY_LAYOUT = dict(
    paper_bgcolor=CARD,
    plot_bgcolor=CARD,
    font=dict(
        family="Nanum Gothic, sans-serif",
        color=TEXT,
        size=13,
    ),
    title_font=dict(size=15, color=TEXT),
    xaxis=dict(
        gridcolor=BORDER,
        linecolor=BORDER,
        zerolinecolor=BORDER,
    ),
    yaxis=dict(
        gridcolor=BORDER,
        linecolor=BORDER,
        zerolinecolor=BORDER,
    ),
    margin=dict(l=20, r=20, t=50, b=20),
)


def apply_layout(fig, **overrides):
    """Plotly figure에 공통 레이아웃 적용."""
    layout = {**PLOTLY_LAYOUT, **overrides}
    fig.update_layout(**layout)
    return fig
