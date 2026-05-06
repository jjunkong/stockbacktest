"""
키움 조건검색 자동 실행 스켈레톤.

흐름:
  1. 로그인
  2. GetConditionLoad() → 등록된 조건검색식 목록 동기화
  3. GetConditionNameList() → 조건식 이름/번호 목록
  4. SendCondition(screen, name, index, search_type) → 만족 종목 받기
  5. 결과를 data/kiwoom_signals/<YYYY-MM-DD>.json 으로 저장

키움이 등록한 조건식의 이름과 우리 conditions.py의 cond1/cond2가 매칭되어야 의미.
사용자가 키움 조건검색식 빌더에서 만든 이름을 알려주시면 매핑 가능.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path


KIWOOM_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = KIWOOM_DIR.parent
SAVE_DIR = PROJECT_ROOT / "data" / "kiwoom_signals"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# 사용자가 키움에서 만든 조건검색식 이름 → 우리 시스템의 cond_id 매핑
# Phase 4 진행 시 사용자에게 받아 채울 예정
CONDITION_NAME_MAP = {
    # "급등주 추격형": "cond1",
    # "갭상승 정배열형": "cond2",
}


def main() -> None:
    from pykiwoom.kiwoom import Kiwoom

    kiwoom = Kiwoom()
    print("[1] 키움 로그인 중...")
    kiwoom.CommConnect(block=True)
    print(f"  로그인 OK ({kiwoom.GetLoginInfo('USER_NAME')})")

    print("[2] 조건검색식 목록 동기화 (GetConditionLoad)...")
    kiwoom.GetConditionLoad()

    print("[3] 등록된 조건검색식 목록")
    conditions = kiwoom.GetConditionNameList()  # [(index, name), ...]
    if not conditions:
        print("  [!] 등록된 조건검색식이 없습니다. 영웅문에서 먼저 만들어 저장하세요.")
        sys.exit(1)
    for idx, name in conditions:
        mapped = CONDITION_NAME_MAP.get(name, "(매핑 없음)")
        print(f"    [{idx}] {name}  →  {mapped}")

    print()
    print("[4] 각 조건식 실행 (조회 한 번씩 — 너무 자주 부르지 말 것)")
    today = datetime.now().strftime("%Y-%m-%d")
    output: dict[str, list[str]] = {}

    for idx, name in conditions:
        print(f"  실행: [{idx}] {name}")
        codes = kiwoom.SendCondition(
            screen_no="0156",
            cond_name=name,
            index=int(idx),
            search_type=0,   # 0: 일반 조회 (실시간 X)
        )
        # codes: 조건 만족 종목 코드 리스트
        cond_id = CONDITION_NAME_MAP.get(name, name)
        output[cond_id] = list(codes) if codes else []
        print(f"    → {len(output[cond_id])}종목")
        time.sleep(2)  # TR 호출 제한 회피

    out_path = SAVE_DIR / f"{today}.json"
    out_path.write_text(json.dumps({
        "date": today,
        "conditions": output,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print()
    print(f"[5] 저장 완료: {out_path}")


if __name__ == "__main__":
    main()
