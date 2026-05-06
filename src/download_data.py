"""
한국 주식 데이터 다운로드 (FinanceDataReader 기반)

단계:
  A) 코스피+코스닥 전체 종목 리스트 + 최신 시총/상장주식수 → data/tickers_all.csv
  B) 시총 1,000억 이상 + 보통주만 필터링 → data/tickers_filtered.csv
  C) 필터된 종목 N년치 일봉 → data/ohlcv/<ticker>.csv

원래 pykrx를 쓰려 했으나, KRX API 응답이 비어 와서 FinanceDataReader로 전환.
시점별 시가총액은 (일봉 종가 × 현재 상장주식수)로 근사.
- 정확한 시점별 상장주식수가 필요하면 추후 보강 가능.
- 단순 1,000억 컷오프엔 이 근사로 충분.

각 단계는 독립 실행 가능 (재실행 안전).
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import FinanceDataReader as fdr
from tqdm import tqdm

# ===== 경로 =====
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OHLCV_DIR = DATA_DIR / "ohlcv"
DATA_DIR.mkdir(exist_ok=True)
OHLCV_DIR.mkdir(exist_ok=True)

TICKERS_ALL_CSV = DATA_DIR / "tickers_all.csv"
TICKERS_FILTERED_CSV = DATA_DIR / "tickers_filtered.csv"
FAILED_TXT = DATA_DIR / "failed_tickers.txt"

# ===== 설정 =====
MARKET_CAP_THRESHOLD = 100_000_000_000  # 1,000억 원
YEARS_BACK = 5  # 다운로드 기간(년)


# ===== Step A: 종목 리스트 + 최신 시총 =====
def step_a_fetch_all_tickers() -> pd.DataFrame:
    """
    fdr.StockListing으로 KOSPI/KOSDAQ 종목 리스트 + 시총 받음.
    한 번 호출에 시장별 모든 종목 데이터가 옵니다.
    """
    print("[Step A] 종목 리스트 + 최신 시총 다운로드 중...")
    frames = []
    for market in ("KOSPI", "KOSDAQ"):
        df = fdr.StockListing(market)
        df = df.copy()
        df["Market"] = market
        frames.append(df)
        print(f"  {market}: {len(df)}개 종목")

    all_df = pd.concat(frames, ignore_index=True)

    # 컬럼 정리 (필요한 것만)
    keep_cols = ["Code", "Name", "Market", "Marcap", "Stocks", "Close", "Volume"]
    all_df = all_df[keep_cols].copy()
    all_df.columns = ["티커", "종목명", "시장", "시가총액", "상장주식수", "종가", "거래량"]
    all_df["티커"] = all_df["티커"].astype(str).str.zfill(6)

    all_df.to_csv(TICKERS_ALL_CSV, index=False, encoding="utf-8-sig")
    print(f"  저장: {TICKERS_ALL_CSV} (총 {len(all_df)}개)")
    return all_df


# ===== Step B: 시총 + 보통주 필터링 =====
def step_b_filter() -> pd.DataFrame:
    """
    시총 1,000억 이상 & 보통주(코드 끝자리 0)만 추려냄.
    우선주(끝자리 5,7,9 등)는 보통주 백테스트에서 제외.
    """
    print("[Step B] 시총 1,000억 이상 + 보통주 필터링...")
    if not TICKERS_ALL_CSV.exists():
        raise FileNotFoundError(f"{TICKERS_ALL_CSV} 없음. Step A 먼저 실행.")

    all_df = pd.read_csv(TICKERS_ALL_CSV, dtype={"티커": str})
    all_df["티커"] = all_df["티커"].str.zfill(6)

    # 시총 결측/0 제거
    all_df = all_df.dropna(subset=["시가총액"])
    all_df = all_df[all_df["시가총액"] > 0]

    # 시총 컷
    cap_pass = all_df[all_df["시가총액"] >= MARKET_CAP_THRESHOLD].copy()
    print(f"  시총 1,000억 통과: {len(cap_pass)}개 / {len(all_df)}개")

    # 보통주만 (코드 끝자리 0)
    common = cap_pass[cap_pass["티커"].str.endswith("0")].copy()
    print(f"  보통주만: {len(common)}개")

    common = common.sort_values("시가총액", ascending=False).reset_index(drop=True)
    common.to_csv(TICKERS_FILTERED_CSV, index=False, encoding="utf-8-sig")
    print(f"  저장: {TICKERS_FILTERED_CSV}")
    return common


# ===== Step C: 일봉 다운로드 =====
def step_c_download_ohlcv(years_back: int = YEARS_BACK, sleep_sec: float = 0.05) -> None:
    """
    필터된 종목들의 N년치 일봉을 받아 종목별 CSV로 저장.
    이미 다운로드된 종목은 스킵.
    """
    print(f"[Step C] {years_back}년치 일봉 데이터 다운로드 중...")
    if not TICKERS_FILTERED_CSV.exists():
        raise FileNotFoundError(f"{TICKERS_FILTERED_CSV} 없음. Step B 먼저 실행.")

    filtered = pd.read_csv(TICKERS_FILTERED_CSV, dtype={"티커": str})
    filtered["티커"] = filtered["티커"].str.zfill(6)

    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=years_back * 365 + 30)
    start_str = start_dt.strftime("%Y-%m-%d")
    end_str = end_dt.strftime("%Y-%m-%d")
    print(f"  기간: {start_str} ~ {end_str}")

    targets = filtered["티커"].tolist()
    skipped = 0
    failed: list[str] = []

    for ticker in tqdm(targets, desc="다운로드"):
        out_path = OHLCV_DIR / f"{ticker}.csv"
        if out_path.exists() and out_path.stat().st_size > 200:
            skipped += 1
            continue
        try:
            df = fdr.DataReader(ticker, start_str, end_str)
            if df is None or df.empty:
                failed.append(ticker)
                continue
            # 미마감(미체결) 행 제거 — Open=0인 행 (보통 마지막 미마감 행)
            df = df[df["Open"] > 0]
            if df.empty:
                failed.append(ticker)
                continue
            # 컬럼 표준화
            df.index.name = "날짜"
            df.to_csv(out_path, encoding="utf-8-sig")
            time.sleep(sleep_sec)
        except Exception as e:
            failed.append(ticker)
            print(f"\n  [경고] {ticker} 실패: {e}")

    print(f"  완료. 스킵 {skipped}개, 실패 {len(failed)}개")
    if failed:
        FAILED_TXT.write_text("\n".join(failed), encoding="utf-8")
        print(f"  실패 목록: {FAILED_TXT}")


def step_c_incremental(days_back: int = 10, sleep_sec: float = 0.05) -> None:
    """
    Incremental 갱신 — 기존 CSV에 최근 N일치만 추가. 매일 자동 갱신용.

    동작:
      - 기존 파일 있으면 마지막 날짜 확인 → 그 다음 날부터 받음 (또는 days_back 안전마진)
      - 새로 받은 데이터를 기존에 append + 날짜 중복 제거
    """
    print(f"[Step C-incremental] 최근 {days_back}일치 갱신 중...")
    if not TICKERS_FILTERED_CSV.exists():
        raise FileNotFoundError(f"{TICKERS_FILTERED_CSV} 없음. Step A/B 먼저.")

    filtered = pd.read_csv(TICKERS_FILTERED_CSV, dtype={"티커": str})
    filtered["티커"] = filtered["티커"].str.zfill(6)
    today = datetime.now()
    end_str = today.strftime("%Y-%m-%d")

    targets = filtered["티커"].tolist()
    updated = 0
    new_files = 0
    failed: list[str] = []

    for ticker in tqdm(targets, desc="갱신"):
        out_path = OHLCV_DIR / f"{ticker}.csv"

        if out_path.exists() and out_path.stat().st_size > 200:
            existing = pd.read_csv(out_path, parse_dates=["날짜"])
            last_date = existing["날짜"].max()
            # 안전 마진 N일 빼고 그 이후부터 다시 받아 append (휴장/누락 보정)
            start_dt = last_date - timedelta(days=days_back)
        else:
            existing = None
            start_dt = today - timedelta(days=365 * 5 + 30)

        start_str = start_dt.strftime("%Y-%m-%d")

        try:
            new_df = fdr.DataReader(ticker, start_str, end_str)
            if new_df is None or new_df.empty:
                continue
            # 미마감 제거
            new_df = new_df[new_df["Open"] > 0]
            if new_df.empty:
                continue
            new_df.index.name = "날짜"
            new_df = new_df.reset_index()

            if existing is not None:
                merged = pd.concat([existing, new_df], ignore_index=True)
                merged = merged.drop_duplicates(subset=["날짜"], keep="last").sort_values("날짜")
                merged.to_csv(out_path, index=False, encoding="utf-8-sig")
                updated += 1
            else:
                new_df.to_csv(out_path, index=False, encoding="utf-8-sig")
                new_files += 1

            time.sleep(sleep_sec)
        except Exception as e:
            failed.append(ticker)
            print(f"\n  [경고] {ticker} 실패: {e}")

    print(f"  완료. 갱신 {updated}, 신규 {new_files}, 실패 {len(failed)}")
    if failed:
        FAILED_TXT.write_text("\n".join(failed), encoding="utf-8")


def main() -> None:
    import sys
    args = sys.argv[1:]
    runners = {
        "a": step_a_fetch_all_tickers,
        "b": step_b_filter,
        "c": step_c_download_ohlcv,
        "incremental": step_c_incremental,
    }
    if not args or "all" in args:
        step_a_fetch_all_tickers()
        step_b_filter()
        step_c_download_ohlcv()
    else:
        for s in args:
            if s in runners:
                runners[s]()
            else:
                print(f"알 수 없는 단계: {s}")


if __name__ == "__main__":
    main()
