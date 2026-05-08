"""
키움 WebSocket 조건검색 클라이언트.

키움 REST API 의 조건검색은 WebSocket 전용:
  wss://api.kiwoom.com:10000/api/dostk/websocket

단발 호출 패턴 (간단, 매 호출 시 connect → LOGIN → req → close):
  - fetch_condition_list()      : 등록된 조건식 목록
  - fetch_condition_tickers(idx): 그 조건식 만족 종목 코드 리스트

응답 필드 (CNSRREQ):
  9001: 종목코드 ('A381620' 같은 형태 → 'A' 떼고 6자리)
  302 : 종목명
"""

from __future__ import annotations

import json
import time
from threading import Lock
from typing import Any

import websocket

from app.services.kiwoom_client import get_token

WS_URL = "wss://api.kiwoom.com:10000/api/dostk/websocket"
_call_lock = Lock()  # WebSocket 호출 직렬화 — 단발 호출 충돌 방지


def _request(ws: websocket.WebSocket, payload: dict, timeout: float = 15) -> dict:
    """payload 의 trnm 과 같은 trnm 의 응답이 올 때까지 대기. 그 외 메시지(PING 등) 는 무시."""
    expected = payload.get("trnm")
    ws.send(json.dumps(payload))
    end = time.time() + timeout
    while time.time() < end:
        ws.settimeout(max(end - time.time(), 0.1))
        try:
            raw = ws.recv()
        except websocket.WebSocketTimeoutException:
            break
        d = json.loads(raw)
        if d.get("trnm") == expected:
            return d
        # 그 외 메시지(PING, 이전 응답 잔여 등) 무시
    raise TimeoutError(f"WebSocket 응답 timeout: {payload}")


def _connect_login() -> websocket.WebSocket:
    ws = websocket.create_connection(WS_URL, timeout=8)
    r = _request(ws, {"trnm": "LOGIN", "token": get_token()})
    if r.get("return_code") != 0:
        ws.close()
        raise RuntimeError(f"WebSocket LOGIN 실패: {r}")
    return ws


def fetch_condition_list() -> list[dict]:
    """등록된 조건식 목록 [{idx, name}, ...]"""
    with _call_lock:
        ws = _connect_login()
        try:
            r = _request(ws, {"trnm": "CNSRLST"})
            data = r.get("data") or []
            out: list[dict] = []
            for row in data:
                if isinstance(row, list) and len(row) >= 2:
                    out.append({"idx": str(row[0]).strip(), "name": str(row[1])})
            return out
        finally:
            ws.close()


def _strip_ticker(code: str | Any) -> str:
    """A381620 → 381620"""
    s = str(code).strip()
    if s.startswith("A") or s.startswith("a"):
        s = s[1:]
    return s.zfill(6)


def fetch_condition_tickers(idx: str | int) -> list[dict]:
    """조건식 idx 의 현재 만족 종목 [{ticker, name}, ...].

    키움 규약상 같은 connect 안에서 CNSRLST 가 선행되어야 CNSRREQ 가 동작.
    """
    seq = str(idx)
    with _call_lock:
        ws = _connect_login()
        try:
            # 선행 CNSRLST (응답 자체는 버리고 prerequisite 만 충족)
            _request(ws, {"trnm": "CNSRLST"})

            r = _request(
                ws,
                {
                    "trnm": "CNSRREQ",
                    "seq": seq,
                    "search_type": "0",
                    "stex_tp": "K",  # KRX
                },
            )
            if r.get("return_code") != 0:
                raise RuntimeError(f"CNSRREQ 실패: {r.get('return_msg')}")
            data = r.get("data") or []
            out: list[dict] = []
            for row in data:
                if not isinstance(row, dict):
                    continue
                ticker = _strip_ticker(row.get("9001", ""))
                name = row.get("302") or ""
                if ticker:
                    out.append({"ticker": ticker, "name": str(name).strip()})
            return out
        finally:
            ws.close()
