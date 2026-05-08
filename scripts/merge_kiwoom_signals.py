"""
키움 조건식 신호 병합.

흐름:
  1. data/kiwoom_signals/*.json 모두 읽음 (condition_runner.py 가 매일 생성)
  2. 각 신호를 (날짜, 티커, 종목명, 조건식, 조건식이름) 행으로 변환
  3. data/signals/all_signals.csv 읽어서 cond1/cond2 행만 보존, 기존 kiwoom_* 행은 제거
  4. 새 kiwoom_* 행 append → 저장

Idempotent: 매번 실행해도 같은 결과.
백테스트는 csv 의 (날짜, 티커, 종목명, 조건식) 만 읽고 OHLCV/지표는 stocks.db 에서
lookup 하므로, kiwoom_* 행의 OHLCV/지표 컬럼은 빈 값으로 둬도 됨.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
KIWOOM_SIGNALS_DIR = ROOT / "data" / "kiwoom_signals"
ALL_SIGNALS_CSV = ROOT / "data" / "signals" / "all_signals.csv"
TICKERS_CSV = ROOT / "data" / "tickers_filtered.csv"


def _load_ticker_names() -> dict[str, str]:
    if not TICKERS_CSV.exists():
        return {}
    df = pd.read_csv(TICKERS_CSV, dtype={"티커": str})
    df["티커"] = df["티커"].str.zfill(6)
    return dict(zip(df["티커"], df["종목명"]))


def _collect_kiwoom_rows(name_map: dict[str, str]) -> list[dict]:
    rows: list[dict] = []
    if not KIWOOM_SIGNALS_DIR.exists():
        return rows

    for jf in sorted(KIWOOM_SIGNALS_DIR.glob("*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [!] {jf.name} 파싱 실패: {e}")
            continue

        date = data.get("date") or jf.stem
        conditions = data.get("conditions", {})
        for cond_id, payload in conditions.items():
            cond_name = payload.get("name", cond_id)
            tickers = payload.get("tickers", [])
            for t in tickers:
                t6 = str(t).zfill(6)
                rows.append({
                    "날짜": date,
                    "티커": t6,
                    "종목명": name_map.get(t6, ""),
                    "조건식": cond_id,
                    "조건식이름": cond_name,
                })
    return rows


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if not ALL_SIGNALS_CSV.exists():
        print(f"[!] {ALL_SIGNALS_CSV} 없음. test_signals.py 먼저 실행 필요.")
        sys.exit(1)

    print(f"[1] 기존 all_signals.csv 로드: {ALL_SIGNALS_CSV}")
    df = pd.read_csv(ALL_SIGNALS_CSV, dtype={"티커": str})
    df["티커"] = df["티커"].str.zfill(6)
    n_before = len(df)
    n_kiwoom_old = (df["조건식"].str.startswith("kiwoom_")).sum()
    print(f"  총 {n_before}행 (기존 kiwoom_* 행: {n_kiwoom_old}개 — 제거됨)")

    # cond1/cond2 같은 비-키움 행만 보존
    base = df[~df["조건식"].str.startswith("kiwoom_")].copy()

    print(f"[2] data/kiwoom_signals/ JSON 수집")
    name_map = _load_ticker_names()
    new_rows = _collect_kiwoom_rows(name_map)
    print(f"  새 키움 신호: {len(new_rows)}행")
    if not new_rows:
        print("  → 추가할 키움 신호 없음. 종료.")
        return

    new_df = pd.DataFrame(new_rows)
    # base 의 모든 컬럼을 갖추되, OHLCV/지표는 비워둠
    for col in base.columns:
        if col not in new_df.columns:
            new_df[col] = pd.NA
    new_df = new_df[base.columns]  # 컬럼 순서 일치

    merged = pd.concat([base, new_df], ignore_index=True)
    # 정렬: 날짜 내림차순 → 조건식 → 티커 (가독성)
    merged = merged.sort_values(["날짜", "조건식", "티커"]).reset_index(drop=True)

    print(f"[3] 저장: {ALL_SIGNALS_CSV}")
    merged.to_csv(ALL_SIGNALS_CSV, index=False, encoding="utf-8-sig")
    n_after = len(merged)
    n_kiwoom_new = (merged["조건식"].str.startswith("kiwoom_")).sum()
    print(f"  완료. 총 {n_after}행 (cond1/cond2: {n_after - n_kiwoom_new}, kiwoom_*: {n_kiwoom_new})")

    # 새로 등장한 조건식 ID 요약
    new_cond_ids = new_df[["조건식", "조건식이름"]].drop_duplicates().sort_values("조건식")
    print(f"\n[4] 등록된 키움 조건식")
    for _, r in new_cond_ids.iterrows():
        n = (new_df["조건식"] == r["조건식"]).sum()
        print(f"    {r['조건식']}  ({r['조건식이름']})  — {n}건")


if __name__ == "__main__":
    main()
