#!/usr/bin/env bash
set -e

# 환경변수:
#   DATA_RELEASE_URL_DB      : stocks.db 다운로드 URL (GitHub Release asset)
#   DATA_RELEASE_URL_SIGNALS : all_signals.csv 다운로드 URL
#   PORT                     : Railway가 자동 주입
#   ALLOWED_ORIGINS          : CORS 허용 도메인 (선택, 콤마 구분)

DATA_DIR="/app/data"
mkdir -p "$DATA_DIR" "$DATA_DIR/signals"

DB_PATH="$DATA_DIR/stocks.db"
SIGNALS_PATH="$DATA_DIR/signals/all_signals.csv"

# 1. stocks.db 다운로드 (이미 있으면 스킵)
if [ ! -f "$DB_PATH" ]; then
    if [ -n "$DATA_RELEASE_URL_DB" ]; then
        echo "[entrypoint] Downloading stocks.db ..."
        curl -fsSL -o "$DB_PATH" "$DATA_RELEASE_URL_DB"
        echo "[entrypoint] stocks.db: $(stat -c%s "$DB_PATH" 2>/dev/null || stat -f%z "$DB_PATH") bytes"
    else
        echo "[entrypoint] WARNING: DATA_RELEASE_URL_DB 미설정. stocks.db 없이 시작"
    fi
else
    echo "[entrypoint] stocks.db already exists, skip download"
fi

# 2. all_signals.csv 다운로드
if [ ! -f "$SIGNALS_PATH" ]; then
    if [ -n "$DATA_RELEASE_URL_SIGNALS" ]; then
        echo "[entrypoint] Downloading all_signals.csv ..."
        curl -fsSL -o "$SIGNALS_PATH" "$DATA_RELEASE_URL_SIGNALS"
    else
        echo "[entrypoint] WARNING: DATA_RELEASE_URL_SIGNALS 미설정"
    fi
fi

# 3. uvicorn 시작
PORT="${PORT:-8000}"
echo "[entrypoint] Starting uvicorn on port $PORT"
cd /app
exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port "$PORT"
