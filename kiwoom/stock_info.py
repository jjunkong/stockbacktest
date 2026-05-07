"""
키움 TR opt10001 (주식기본정보요청) 으로 종목별 PER/PBR/시총 가져오기.

백로그 B2 해결 — 무료 소스로는 신뢰할 수 없었던 PER/PBR을 키움에서 정확히 가져옴.

흐름:
  1. 로그인
  2. tickers_filtered.csv 로드 → 1,543종목 리스트
  3. 종목당 opt10001 호출 (TR 호출 제한 1초 5회 → 0.25초 sleep)
  4. PER/PBR/EPS/BPS/시가총액 등 받아서 data/fundamentals.json 저장

총 소요: 1,543 × 0.25초 = 약 7분
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TICKERS_CSV = PROJECT_ROOT / "data" / "tickers_filtered.csv"
OUTPUT_JSON = PROJECT_ROOT / "data" / "fundamentals.json"


def main(limit: int | None = None) -> None:
    from pykiwoom.kiwoom import Kiwoom

    kiwoom = Kiwoom()
    print("[1] 키움 로그인...")
    kiwoom.CommConnect(block=True)

    print(f"[2] 종목 리스트 로드: {TICKERS_CSV}")
    tickers_df = pd.read_csv(TICKERS_CSV, dtype={"티커": str})
    tickers_df["티커"] = tickers_df["티커"].str.zfill(6)
    tickers = tickers_df["티커"].tolist()
    if limit:
        tickers = tickers[:limit]
    print(f"  대상: {len(tickers)}종목")

    print("[3] opt10001 (주식기본정보) 종목별 조회")
    fundamentals: dict[str, dict] = {}
    for i, code in enumerate(tickers):
        df = kiwoom.block_request(
            "opt10001",
            종목코드=code,
            output="주식기본정보",
            next=0,
        )
        if df is not None and not df.empty:
            r = df.iloc[0]
            fundamentals[code] = {
                "per": float(r.get("PER", 0) or 0),
                "pbr": float(r.get("PBR", 0) or 0),
                "eps": float(r.get("EPS", 0) or 0),
                "bps": float(r.get("BPS", 0) or 0),
            }
        if (i + 1) % 50 == 0:
            print(f"  진행 {i+1}/{len(tickers)}")
        time.sleep(0.25)  # TR 호출 제한

    print(f"[4] 저장: {OUTPUT_JSON}")
    OUTPUT_JSON.write_text(
        json.dumps(fundamentals, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  완료. {len(fundamentals)}종목")


if __name__ == "__main__":
    import sys
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(limit=lim)
