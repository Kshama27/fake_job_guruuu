## Project structure notes

- **Models**: Stored in `models/`
  - Expected file: `models/scam_detector.pkl`

- **Data**: Stored in `data/`
  - Expected file: `data/fake_job_postings.csv`

If these files do not exist locally, create the directories as above and place the model and dataset in the indicated paths.


### Run locally

1) Activate virtualenv
- Windows PowerShell:
  - `& .\.venv\Scripts\Activate.ps1` (create with `python -m venv .venv` if missing)
- macOS/Linux/Git Bash:
  - `source .venv/bin/activate` (create with `python -m venv .venv` if missing)

2) Start server
- PowerShell: `./run_dev.ps1`
- macOS/Linux/Git Bash: `./run_dev.sh`
- Or directly: `uvicorn asgi:app --reload`

Notes:
- These scripts only set environment/import path. Do not change backend model files.
- Ensure `fake_job_guru/api.py` exposes a FastAPI `app` or `create_app()`.

