"""
키움 REST API 클라이언트.

- OAuth 토큰 자동 발급/갱신 (메모리 + 파일 캐시, 24시간 유효)
- KA10001 (주식기본정보) 호출 → 정규화된 dict 반환
- 환경변수: KIWOOM_APP_KEY, KIWOOM_APP_SECRET, KIWOOM_API_BASE
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = ROOT / "backend" / ".env"
TOKEN_PATH = ROOT / "backend" / ".kiwoom_token.json"
KST = timezone(timedelta(hours=9))


def _load_env() -> None:
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


_load_env()

APP_KEY = os.getenv("KIWOOM_APP_KEY", "")
APP_SECRET = os.getenv("KIWOOM_APP_SECRET", "")
BASE = os.getenv("KIWOOM_API_BASE", "https://api.kiwoom.com")

_token_cache: dict[str, Any] = {"token": None, "expires": 0}
_lock = Lock()


def is_configured() -> bool:
    return bool(APP_KEY and APP_SECRET)


def _parse_expires(expires_dt: str) -> int:
    """expires_dt 형식: '20260509135016' (KST). epoch seconds 반환."""
    try:
        dt = datetime.strptime(expires_dt, "%Y%m%d%H%M%S").replace(tzinfo=KST)
        return int(dt.timestamp())
    except Exception:
        return int(time.time()) + 60 * 60 * 23


def _read_token_file() -> dict | None:
    if not TOKEN_PATH.exists():
        return None
    try:
        return json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_token_file(token: str, expires_dt: str) -> None:
    TOKEN_PATH.write_text(
        json.dumps({"token": token, "expires_dt": expires_dt}, ensure_ascii=False),
        encoding="utf-8",
    )


def get_token(force: bool = False) -> str:
    if not is_configured():
        raise RuntimeError("KIWOOM_APP_KEY/SECRET 이 설정되지 않음")

    with _lock:
        now = int(time.time())
        if not force and _token_cache["token"] and now < _token_cache["expires"] - 60:
            return _token_cache["token"]

        if not force:
            saved = _read_token_file()
            if saved and saved.get("token") and saved.get("expires_dt"):
                exp = _parse_expires(saved["expires_dt"])
                if now < exp - 60:
                    _token_cache["token"] = saved["token"]
                    _token_cache["expires"] = exp
                    return saved["token"]

        resp = requests.post(
            f"{BASE}/oauth2/token",
            json={
                "grant_type": "client_credentials",
                "appkey": APP_KEY,
                "secretkey": APP_SECRET,
            },
            headers={"Content-Type": "application/json;charset=UTF-8"},
            timeout=10,
        )
        resp.raise_for_status()
        d = resp.json()
        if d.get("return_code") != 0:
            raise RuntimeError(f"키움 토큰 발급 실패: {d.get('return_msg')}")
        token = d["token"]
        expires_dt = d["expires_dt"]
        _write_token_file(token, expires_dt)
        _token_cache["token"] = token
        _token_cache["expires"] = _parse_expires(expires_dt)
        return token


def _api_post(path: str, api_id: str, body: dict, retry: bool = True) -> dict:
    token = get_token()
    resp = requests.post(
        f"{BASE}{path}",
        json=body,
        headers={
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": f"Bearer {token}",
            "api-id": api_id,
        },
        timeout=10,
    )
    if resp.status_code == 401 and retry:
        get_token(force=True)
        return _api_post(path, api_id, body, retry=False)
    resp.raise_for_status()
    return resp.json()


def _to_float(s: Any) -> float | None:
    """'+13380' / '-100' / '13380' / '' / None → float (부호 유지)."""
    if s is None or s == "":
        return None
    try:
        return float(str(s).replace("+", "").replace(",", ""))
    except (ValueError, TypeError):
        return None


def _to_price(s: Any) -> float | None:
    """가격 컬럼 - 키움이 base 대비 부호를 붙여 보내므로 절대값 사용."""
    v = _to_float(s)
    return abs(v) if v is not None else None


def get_basic_info(ticker: str) -> dict:
    """KA10001 주식기본정보. 정규화된 dict 반환.

    오류 시 {"ticker": ..., "error": "..."} 형태.
    """
    t = ticker.zfill(6)
    try:
        raw = _api_post("/api/dostk/stkinfo", "ka10001", {"stk_cd": t})
    except Exception as e:
        return {"ticker": t, "error": str(e)}
    if raw.get("return_code") != 0:
        return {"ticker": t, "error": raw.get("return_msg", "unknown")}
    cur = _to_price(raw.get("cur_prc"))
    vol = _to_float(raw.get("trde_qty"))  # 거래량 (주)
    amt = (cur * vol) if (cur and vol) else None  # 거래대금 근사 (원)
    return {
        "ticker": t,
        "name": raw.get("stk_nm"),
        "current_price": cur,
        "change": _to_float(raw.get("pred_pre")),
        "change_rate": _to_float(raw.get("flu_rt")),
        "open": _to_price(raw.get("open_pric")),
        "high": _to_price(raw.get("high_pric")),
        "low": _to_price(raw.get("low_pric")),
        "base_price": _to_price(raw.get("base_pric")),
        # 신규
        "volume": vol,                       # 당일 누적 거래량 (주)
        "amount": amt,                       # 당일 누적 거래대금 (원, 근사)
        "market_cap": _to_float(raw.get("mac")),  # 시가총액 (단위: 억원)
        "volume_pre_rate": _to_float(raw.get("trde_pre")),  # 거래량 전일비 %
    }


def get_quotes(tickers: list[str]) -> list[dict]:
    """다수 종목 시세. 단순 순차 호출."""
    return [get_basic_info(t) for t in tickers]
