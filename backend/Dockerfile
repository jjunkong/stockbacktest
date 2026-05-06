# StockBacktest 백엔드 (FastAPI) — Railway 배포용
#
# 컨테이너 시작 시:
#   1. data/stocks.db, data/signals/all_signals.csv, data/tickers_filtered.csv,
#      data/themes.json 을 GitHub Release에서 다운로드
#   2. uvicorn으로 FastAPI 시작
#
# 매일 GitHub Actions cron이 새 데이터를 Release에 업로드 → Railway 컨테이너 재시작 시 자동 반영.

FROM python:3.11-slim AS base

WORKDIR /app

# 시스템 의존성 (FDR 등 일부 패키지에 필요)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Python 의존성 — 캐시 효율 위해 먼저 복사
COPY backend/requirements.txt ./backend-requirements.txt
RUN pip install --no-cache-dir -r backend-requirements.txt

# 백엔드 + src + 작은 데이터 (테마, 메타) 복사
COPY backend ./backend
COPY src ./src
COPY data/themes.json ./data/themes.json
COPY data/tickers_filtered.csv ./data/tickers_filtered.csv

# 큰 데이터(stocks.db, signals)는 시작 시 GitHub Release에서 받음
# entrypoint.sh로 처리
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
