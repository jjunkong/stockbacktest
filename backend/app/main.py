"""
StockBacktest FastAPI 백엔드 진입점.

실행:
    cd backend
    ..\\venv\\Scripts\\python.exe -m uvicorn app.main:app --reload --port 8000

API 문서:
    http://localhost:8000/docs
"""

from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import meta, backtest, tickers, kospi, themes
from app.schemas.common import HealthResponse
from app.services.data_store import store
from app.services.theme_store import theme_store


# ===== Lifespan: 서버 시작 시 OHLCV 1,543개를 메모리에 미리 로드 =====
@asynccontextmanager
async def lifespan(_app: FastAPI):
    print("[lifespan] priming data store...")
    t0 = time.time()
    store.prime()
    theme_store.load()
    elapsed = time.time() - t0
    print(
        f"[lifespan] loaded in {elapsed:.1f}s | "
        f"signals={len(store.signals) if store.signals is not None else 0}, "
        f"tickers={len(store.tickers) if store.tickers is not None else 0}, "
        f"themes={len(theme_store.themes)} (ohlcv: lazy)"
    )
    yield
    # shutdown 시 정리할 것 없음


app = FastAPI(
    title="StockBacktest API",
    description="키움 조건검색식 백테스팅 — Next.js 프론트엔드용 API",
    version="0.1.0",
    lifespan=lifespan,
)


# ===== CORS =====
# 개발: localhost / 배포: Vercel 도메인은 regex로 자동 허용 + 환경변수로 추가 도메인
extra_origins = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        *extra_origins,
    ],
    # Vercel preview/production 도메인 자동 허용 (*.vercel.app)
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== 라우터 등록 =====
API_PREFIX = "/api/v1"
app.include_router(meta.router, prefix=API_PREFIX)
app.include_router(backtest.router, prefix=API_PREFIX)
app.include_router(tickers.router, prefix=API_PREFIX)
app.include_router(kospi.router, prefix=API_PREFIX)
app.include_router(themes.router, prefix=API_PREFIX)


# ===== Health check =====
@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "service": "StockBacktest API",
        "version": "0.1.0",
        "docs": "/docs",
        "api_prefix": API_PREFIX,
    }


@app.get(f"{API_PREFIX}/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        cache_ready=store.is_ready(),
        n_tickers=len(store.tickers) if store.tickers is not None else 0,
        n_signals=len(store.signals) if store.signals is not None else 0,
    )
