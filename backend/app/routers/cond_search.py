"""
키움 영웅문 조건검색 라우터 — 장중 라이브 종목 조회.

GET /cond-search/list           : 사용자가 영웅문에 등록한 조건식 목록
GET /cond-search/{idx}/tickers  : 그 조건식의 현재 만족 종목 (5초 TTL)
"""

from __future__ import annotations

import time
from threading import Lock

from fastapi import APIRouter, HTTPException

from app.services import kiwoom_client, kiwoom_ws
from app.services.theme_store import theme_store

router = APIRouter(prefix="/cond-search", tags=["cond-search"])

_LIST_TTL = 60.0  # 조건식 목록은 거의 안 바뀌므로 길게
_TICKERS_TTL = 5.0  # 만족 종목 — 라이브 체감 위해 짧게
_list_cache: dict = {"ts": 0.0, "data": None}
_tickers_cache: dict[str, tuple[float, list]] = {}
_lock = Lock()


@router.get("/list")
def list_conditions() -> list[dict]:
    """사용자가 영웅문에 등록한 조건식 목록 (idx, name)."""
    if not kiwoom_client.is_configured():
        raise HTTPException(503, "키움 API 키 미설정")

    now = time.time()
    with _lock:
        if _list_cache["data"] is not None and now - _list_cache["ts"] < _LIST_TTL:
            return _list_cache["data"]
    try:
        data = kiwoom_ws.fetch_condition_list()
    except Exception as e:
        raise HTTPException(502, f"키움 WebSocket 실패: {e}")
    with _lock:
        _list_cache["ts"] = now
        _list_cache["data"] = data
    return data


@router.get("/{idx}/tickers")
def list_tickers(idx: str) -> dict:
    """조건식 idx 의 현재 만족 종목 + 조회 시각.

    라이브 체감용 5초 TTL. 너무 자주 호출하면 키움 부하.
    """
    if not kiwoom_client.is_configured():
        raise HTTPException(503, "키움 API 키 미설정")

    now = time.time()
    with _lock:
        cached = _tickers_cache.get(idx)
        if cached and now - cached[0] < _TICKERS_TTL:
            return {"idx": idx, "tickers": cached[1], "fetched_at": cached[0]}

    try:
        items = kiwoom_ws.fetch_condition_tickers(idx)
    except Exception as e:
        raise HTTPException(502, f"키움 WebSocket 실패: {e}")

    # 테마 부착 — 종목별 attached themes
    for it in items:
        it["themes"] = theme_store.themes_for_ticker(it["ticker"])

    with _lock:
        _tickers_cache[idx] = (now, items)
    return {"idx": idx, "tickers": items, "fetched_at": now}
