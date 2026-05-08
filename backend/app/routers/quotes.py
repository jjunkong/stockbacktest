"""실시간 시세 라우터 — 키움 REST API 통해 현재가/등락률 제공."""

from __future__ import annotations

import time
from threading import Lock

from fastapi import APIRouter, HTTPException, Query

from app.services import kiwoom_client

router = APIRouter(prefix="/quotes", tags=["quotes"])

# (ticker → (timestamp, payload)) 짧은 TTL 캐시
_CACHE_TTL = 1.0  # 초
_cache: dict[str, tuple[float, dict]] = {}
_cache_lock = Lock()


@router.get("")
def get_multi_quotes(
    tickers: str = Query(..., description="콤마 구분 종목코드, 예: 147830,005930"),
) -> list[dict]:
    """다수 종목 현재가/등락률 한 번에 조회.

    1초 TTL 캐시 — 같은 종목 여러 클라이언트 polling 시 키움 호출 분산.
    """
    if not kiwoom_client.is_configured():
        raise HTTPException(503, "키움 API 키가 설정되지 않았습니다 (.env)")

    requested = [t.strip().zfill(6) for t in tickers.split(",") if t.strip()]
    if not requested:
        return []

    now = time.time()
    out: dict[str, dict] = {}
    miss: list[str] = []
    with _cache_lock:
        for t in requested:
            entry = _cache.get(t)
            if entry and now - entry[0] < _CACHE_TTL:
                out[t] = entry[1]
            else:
                miss.append(t)

    if miss:
        fresh = kiwoom_client.get_quotes(miss)
        with _cache_lock:
            ts = time.time()
            for q in fresh:
                _cache[q["ticker"]] = (ts, q)
                out[q["ticker"]] = q

    return [out.get(t, {"ticker": t, "error": "not_loaded"}) for t in requested]
