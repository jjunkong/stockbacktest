"""
다운로드된 CSV 일봉 데이터를 SQLite DB로 통합.

CSV 파일 단위는 종목 추가/제거가 쉽지만 분석 시 매번 1,500개 파일을 여는 건 느림.
DB로 합쳐두면:
  - 한 번에 모든 종목 SQL 쿼리 가능 (예: 특정 날짜 모든 종목)
  - 인덱스로 빠른 조회
  - 단일 파일이라 백업/이동 편함

사용:
    python src/build_db.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OHLCV_DIR = DATA_DIR / "ohlcv"
DB_PATH = DATA_DIR / "stocks.db"
TICKERS_CSV = DATA_DIR / "tickers_filtered.csv"


def main() -> None:
    if not TICKERS_CSV.exists():
        raise FileNotFoundError("tickers_filtered.csv 없음. download_data.py 먼저 실행.")

    print(f"DB 경로: {DB_PATH}")
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("  기존 DB 삭제 후 새로 생성")

    engine = create_engine(f"sqlite:///{DB_PATH}")

    # 1) 메타 테이블
    print("[1/2] 메타 테이블 작성...")
    meta = pd.read_csv(TICKERS_CSV, dtype={"티커": str})
    meta["티커"] = meta["티커"].str.zfill(6)
    meta.to_sql("tickers", engine, index=False, if_exists="replace")
    print(f"  tickers 테이블: {len(meta)}건")

    # 2) 일봉 테이블 (모든 종목 long-format)
    print("[2/2] 일봉 데이터 통합...")
    csv_files = sorted(OHLCV_DIR.glob("*.csv"))
    print(f"  대상 파일: {len(csv_files)}개")

    rows_total = 0
    chunk = []
    chunk_size = 100  # 100종목씩 모아서 한 번에 INSERT

    for i, path in enumerate(tqdm(csv_files, desc="DB 적재")):
        ticker = path.stem
        try:
            df = pd.read_csv(path, parse_dates=["날짜"])
        except Exception:
            continue
        if df.empty:
            continue
        df["티커"] = ticker
        chunk.append(df)

        if len(chunk) >= chunk_size or i == len(csv_files) - 1:
            merged = pd.concat(chunk, ignore_index=True)
            merged.to_sql("ohlcv", engine, index=False, if_exists="append")
            rows_total += len(merged)
            chunk = []

    # 남은 chunk 처리 (위 루프 마지막 처리가 i == last로 이미 들어갔지만 보험)
    if chunk:
        merged = pd.concat(chunk, ignore_index=True)
        merged.to_sql("ohlcv", engine, index=False, if_exists="append")
        rows_total += len(merged)

    print(f"  ohlcv 테이블: {rows_total:,}건")

    # 인덱스 생성 (빠른 조회용)
    print("인덱스 생성 중...")
    with engine.begin() as conn:
        conn.execute(text("CREATE INDEX idx_ohlcv_ticker ON ohlcv(티커)"))
        conn.execute(text("CREATE INDEX idx_ohlcv_date ON ohlcv(날짜)"))
        conn.execute(text("CREATE INDEX idx_ohlcv_ticker_date ON ohlcv(티커, 날짜)"))
    print("완료.")

    # 검증
    with engine.connect() as conn:
        n_tickers = conn.execute(text("SELECT COUNT(DISTINCT 티커) FROM ohlcv")).scalar()
        date_min = conn.execute(text("SELECT MIN(날짜) FROM ohlcv")).scalar()
        date_max = conn.execute(text("SELECT MAX(날짜) FROM ohlcv")).scalar()
    print(f"\n=== DB 요약 ===")
    print(f"  종목 수: {n_tickers}")
    print(f"  기간: {date_min} ~ {date_max}")
    print(f"  파일 크기: {DB_PATH.stat().st_size / (1024**2):.1f} MB")


if __name__ == "__main__":
    main()
