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
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    from pykiwoom.kiwoom import Kiwoom

    kiwoom = Kiwoom()
    print("[1] 키움 로그인 중...")
    kiwoom.CommConnect(block=True)
    raw_name = kiwoom.GetLoginInfo("USER_NAME")
    try:
        user_name = raw_name.encode("latin1").decode("cp949")
    except Exception:
        user_name = raw_name
    print(f"  로그인 OK ({user_name})")

    print("[2] 조건검색식 목록 동기화 (GetConditionLoad)...")
    kiwoom.GetConditionLoad()

    def _decode(s: str) -> str:
        try:
            return s.encode("latin1").decode("cp949")
        except Exception:
            return s

    print("[3] 등록된 조건검색식 목록")
    conditions = kiwoom.GetConditionNameList()  # [(index, raw_name), ...]
    if not conditions:
        print("  [!] 등록된 조건검색식이 없습니다. 영웅문에서 먼저 만들어 저장하세요.")
        sys.exit(1)
    for idx, raw_name in conditions:
        name = _decode(raw_name)
        mapped = CONDITION_NAME_MAP.get(name, "(매핑 없음)")
        print(f"    [{idx}] {name}  →  {mapped}")

    print()
    if not CONDITION_NAME_MAP:
        print("[!] CONDITION_NAME_MAP 이 비어 있어 실행할 조건이 없습니다.")
        print("    위 목록에서 사용할 이름을 골라 condition_runner.py 의 CONDITION_NAME_MAP 에 추가하세요.")
        return

    print("[4] 매핑된 조건식만 실행")
    today = datetime.now().strftime("%Y-%m-%d")
    output: dict[str, list[str]] = {}

    for idx, raw_name in conditions:
        name = _decode(raw_name)
        if name not in CONDITION_NAME_MAP:
            continue
        cond_id = CONDITION_NAME_MAP[name]
        print(f"  실행: [{idx}] {name}  →  {cond_id}")
        # raw_name 그대로 OCX 에 넘겨야 함 (pykiwoom 이 latin1->원본 CP949 로 되돌림)
        codes = kiwoom.SendCondition("0156", raw_name, int(idx), 0)
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
