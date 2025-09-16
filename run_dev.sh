#!/usr/bin/env bash
# run_dev.sh — run the FastAPI app on Unix-like shells / Git Bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
export SCAM_MODEL_PATH="${ROOT}/models/scam_detector.pkl"
export PYTHONPATH="${ROOT}:${ROOT}/fake_job_guruuu${PYTHONPATH:+:$PYTHONPATH}"
exec uvicorn asgi:app --reload --host 127.0.0.1 --port 8000


