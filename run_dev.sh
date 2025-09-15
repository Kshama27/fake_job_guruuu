#!/usr/bin/env bash
# Dev run helper — run from project root
export SCAM_MODEL_PATH="$(pwd)/models/scam_detector.pkl"
# optionally set Python env
# python -m venv .venv && source .venv/bin/activate
uvicorn fake_job_guru.api:app --reload --host 127.0.0.1 --port 8000


