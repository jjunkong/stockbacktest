"""
키움 테마군 정보 수집 → 우리 themes.json 자동 갱신.

백로그 B1 해결 — 수동 큐레이션을 키움 공식 테마군으로 교체.

키움 TR:
  - opt90001 (테마그룹별요청): 모든 테마 그룹 목록
  - opt90002 (테마구성종목요청): 특정 테마 그룹의 종목 리스트

산출물: data/themes.json (기존 수동 파일을 덮어씀)
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
THEMES_JSON = PROJECT_ROOT / "data" / "themes.json"


def _decode(s) -> str:
    try:
        return str(s).encode("latin1").decode("cp949")
    except Exception:
        return str(s)


def main() -> None:
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    from pykiwoom.kiwoom import Kiwoom

    kiwoom = Kiwoom()
    print("[1] 키움 로그인...")
    kiwoom.CommConnect(block=True)

    print("[2] opt90001 (테마그룹별요청) — 전체 테마 목록")
    df = kiwoom.block_request(
        "opt90001",
        검색구분="0",            # 0: 전체검색
        종목코드="",
        날짜구분="10",           # 기간 (1, 5, 10, 20)
        테마명="",
        등락수익구분="0",        # 0: 등락률
        거래소구분="0",          # 0: 전체
        output="테마그룹별",
        next=0,
    )
    if df is None or df.empty:
        print("  [!] 테마 목록 못 받음")
        return

    print(f"  테마 {len(df)}개 받음")

    themes_out = []
    for i, row in df.iterrows():
        # opt90001 의 '종목코드' 가 실제로는 테마 그룹 코드
        theme_code = _decode(row.get("종목코드", "")).strip()
        theme_name = _decode(row.get("테마명", "")).strip()
        if not theme_code or not theme_name:
            continue

        print(f"  [{i+1}/{len(df)}] {theme_code} {theme_name}")

        # opt90002 (테마구성종목요청)
        # 키움 작명 주의: 인자명 '종목코드' 가 실제로는 테마 그룹 코드를 받음
        sub = kiwoom.block_request(
            "opt90002",
            날짜구분="2",
            종목코드=theme_code,
            거래소구분="0",
            output="테마구성종목",
            next=0,
        )
        if sub is None or sub.empty:
            stocks = []
        else:
            # 종목코드는 ASCII 6자리. 앞에 'A' 같은 prefix 가 붙는 경우 정리
            stocks = []
            for c in sub["종목코드"].tolist():
                code = str(c).strip().lstrip("A").lstrip("a")
                if code and code.isdigit() and len(code) == 6:
                    stocks.append(code)

        themes_out.append({
            "id": theme_code,
            "name": theme_name,
            "description": "",
            "leaders": stocks[:5],          # 임시: 상위 5개를 주도주로
            "related": stocks[5:],
        })
        time.sleep(0.5)  # TR 호출 제한

    out = {
        "version": "kiwoom-1.0",
        "updated": datetime.now().strftime("%Y-%m-%d"),
        "note": "키움 OpenAPI+ 자동 동기화 (opt90001 / opt90002)",
        "themes": themes_out,
    }
    THEMES_JSON.write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[3] 저장 완료: {THEMES_JSON} ({len(themes_out)}개 테마)")


if __name__ == "__main__":
    main()
