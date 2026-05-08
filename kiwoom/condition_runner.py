"""
키움 조건검색식 자동 실행 (인터랙티브).

흐름:
  1. 키움 영웅문에 먼저 로그인되어 있어야 함 (또는 이 스크립트가 띄움)
  2. GetConditionLoad → GetConditionNameList 로 등록된 139개 조건식 목록 가져옴
  3. 사용자가 번호 입력 (예: "1,40,52") → 선택 저장
  4. 다음번 실행 시 저장된 선택 그대로 재사용 가능 (Y/n 확인)
  5. SendCondition 으로 만족 종목 받음
  6. data/kiwoom_signals/<YYYY-MM-DD>.json 으로 저장

cond_id 는 자동 생성: kiwoom_<3자리 인덱스> (예: kiwoom_001, kiwoom_040)
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

SELECTED_PATH = KIWOOM_DIR / "selected_conditions.json"


def _decode(s: str) -> str:
    try:
        return s.encode("latin1").decode("cp949")
    except Exception:
        return s


def _load_selected() -> list[str] | None:
    if not SELECTED_PATH.exists():
        return None
    try:
        data = json.loads(SELECTED_PATH.read_text(encoding="utf-8"))
        idxs = data.get("indices")
        return [str(i).zfill(3) for i in idxs] if idxs else None
    except Exception:
        return None


def _save_selected(indices: list[str]) -> None:
    SELECTED_PATH.write_text(
        json.dumps({"indices": indices}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _ask_indices(available: dict[str, str]) -> list[str]:
    """사용자에게 번호 입력 받음. 유효한 번호만 반환."""
    while True:
        raw = input("\n실행할 조건식 번호 (콤마로 구분, 예: 1,40,52): ").strip()
        if not raw:
            print("  입력이 비어 있습니다.")
            continue
        try:
            picked = [s.strip().zfill(3) for s in raw.split(",") if s.strip()]
        except Exception:
            print("  형식 오류. 다시 입력하세요.")
            continue
        bad = [p for p in picked if p not in available]
        if bad:
            print(f"  목록에 없는 번호: {', '.join(bad)}")
            continue
        if not picked:
            print("  선택된 번호가 없습니다.")
            continue
        return picked


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
    print(f"  로그인 OK ({_decode(raw_name)})")

    print("[2] 조건검색식 목록 동기화 (GetConditionLoad)...")
    kiwoom.GetConditionLoad()

    conditions = kiwoom.GetConditionNameList()  # [(index, raw_name), ...]
    if not conditions:
        print("  [!] 등록된 조건검색식이 없습니다. 영웅문에서 먼저 만들어 저장하세요.")
        sys.exit(1)

    # idx(3자리) → (raw_name, decoded_name)
    available: dict[str, tuple[str, str]] = {}
    for idx, raw_name in conditions:
        idx3 = str(idx).zfill(3)
        available[idx3] = (raw_name, _decode(raw_name))

    print(f"[3] 등록된 조건검색식 {len(available)}개")
    for idx3 in sorted(available.keys()):
        print(f"    [{idx3}] {available[idx3][1]}")

    # 이전 선택 재사용
    prev = _load_selected()
    selected: list[str] | None = None
    if prev:
        valid_prev = [p for p in prev if p in available]
        if valid_prev:
            names = ", ".join(f"[{p}] {available[p][1]}" for p in valid_prev)
            print(f"\n이전 선택: {names}")
            ans = input("그대로 진행할까요? [Y/n]: ").strip().lower()
            if ans in ("", "y", "yes"):
                selected = valid_prev

    if selected is None:
        selected = _ask_indices({k: v[1] for k, v in available.items()})
        _save_selected(selected)
        print(f"  → 선택 저장됨 ({SELECTED_PATH.name})")

    print("\n[4] 선택된 조건식 실행")
    today = datetime.now().strftime("%Y-%m-%d")
    output: dict[str, dict] = {}

    for idx3 in selected:
        raw_name, name = available[idx3]
        cond_id = f"kiwoom_{idx3}"
        print(f"  실행: [{idx3}] {name}  →  {cond_id}")
        # raw_name 그대로 OCX 에 넘김 (pykiwoom 내부에서 cp949 로 되돌림)
        codes = kiwoom.SendCondition("0156", raw_name, int(idx3), 0)
        tickers = list(codes) if codes else []
        output[cond_id] = {"name": name, "tickers": tickers}
        print(f"    → {len(tickers)}종목")
        time.sleep(2)  # TR 호출 제한 회피

    out_path = SAVE_DIR / f"{today}.json"
    out_path.write_text(
        json.dumps(
            {"date": today, "conditions": output},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n[5] 저장 완료: {out_path}")
    print("\n다음 단계:")
    print("  python scripts/merge_kiwoom_signals.py")


if __name__ == "__main__":
    main()
