from pathlib import Path
import sys

# Ensure nested app package is importable when running `uvicorn api:app --reload` from repo root
ROOT = Path(__file__).resolve().parent
NESTED = ROOT / "fake_job_guruuu"
if str(NESTED) not in sys.path:
    sys.path.insert(0, str(NESTED))

from fake_job_guru.api import app  # re-export FastAPI app


