#!/bin/bash
set -e

APP_NAME="fashiye"
APP_DIR="/www/wwwroot/fashiye"
LOG_DIR="/var/log/fashiye"

cd "$APP_DIR"

GUNICORN_WORKERS=${GUNICORN_WORKERS:-4}
GUNICORN_BIND=${GUNICORN_BIND:-"0.0.0.0:8888"}

mkdir -p "$LOG_DIR"

exec gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers "$GUNICORN_WORKERS" \
    --bind "$GUNICORN_BIND" \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 10000 \
    --max-requests-jitter 1000 \
    --access-logfile "$LOG_DIR/access.log" \
    --error-logfile "$LOG_DIR/error.log" \
    --log-level info
