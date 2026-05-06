"""
매일 자동 갱신 통합 스크립트.

GitHub Actions cron 또는 Windows 작업 스케줄러에서 매일 16:00 KST 실행.

순서:
  1. 종목 메타 갱신 (Step A: KOSPI/KOSDAQ 종목 + 최신 시총)
  2. 시총 1,000억 필터 (Step B)
  3. 종목별 일봉 incremental 갱신 (Step C-incremental, 최근 10일치만)
  4. SQLite stocks.db 재생성 (build_db)
  5. 신호 재검출 (test_signals → all_signals.csv)

산출물:
  - data/stocks.db (배포용 단일 파일)
  - data/signals/all_signals.csv
  - data/tickers_filtered.csv

GitHub Actions에서:
  실행 후 data/stocks.db 와 data/signals/all_signals.csv 를 Release 'data-latest'에 업로드.
  Railway 백엔드는 시작 시 그 Release에서 두 파일 다운로드.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(label: str, args: list[str]) -> None:
    print(f"\n{'=' * 60}")
    print(f"  [{label}] {' '.join(args)}")
    print(f"{'=' * 60}")
    t0 = time.time()
    subprocess.check_call([sys.executable, *args], cwd=str(ROOT))
    print(f"  → 완료 ({time.time() - t0:.1f}s)")


def main() -> None:
    print("=" * 60)
    print("  StockBacktest 일일 갱신")
    print("=" * 60)
    t_total = time.time()

    # 1. 종목 메타 갱신
    run("Step A · 종목 리스트 + 시총", ["src/download_data.py", "a"])

    # 2. 필터링
    run("Step B · 1,000억 필터", ["src/download_data.py", "b"])

    # 3. 일봉 incremental (최근 10일)
    run("Step C · 일봉 incremental", ["src/download_data.py", "incremental"])

    # 4. DB 재생성
    run("Build DB", ["src/build_db.py"])

    # 5. 신호 재검출
    run("Detect signals", ["src/test_signals.py"])

    print()
    print("=" * 60)
    print(f"  ALL DONE. 총 {time.time() - t_total:.1f}s")
    print("=" * 60)
    print()
    print("산출물:")
    for p in [
        ROOT / "data" / "stocks.db",
        ROOT / "data" / "signals" / "all_signals.csv",
        ROOT / "data" / "tickers_filtered.csv",
    ]:
        if p.exists():
            size_mb = p.stat().st_size / (1024 * 1024)
            print(f"  ✓ {p.relative_to(ROOT)} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
