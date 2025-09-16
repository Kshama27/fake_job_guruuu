$ErrorActionPreference = 'Stop'

# Ensure venv exists
if (-not (Test-Path .\.venv\Scripts\python.exe)) {
  Write-Host "Creating virtual environment..."
  python -m venv .venv
}

$py = Resolve-Path .\.venv\Scripts\python.exe

# Install deps if needed
if (-not (Test-Path .\.venv\Lib\site-packages\fastapi)) {
  & $py -m pip install --upgrade pip
  if (Test-Path .\requirements.txt) {
    & $py -m pip install -r .\requirements.txt
  } elseif (Test-Path .\fake_job_guruuu\requirements.txt) {
    & $py -m pip install -r .\fake_job_guruuu\requirements.txt
  }
}

# Set model path if present
if (Test-Path .\models\scam_detector.pkl) {
  $env:SCAM_MODEL_PATH = (Resolve-Path .\models\scam_detector.pkl).Path
}

# Run from app directory
Set-Location .\fake_job_guruuu

# Start server
& $py -m uvicorn fake_job_guru.api:app --reload --host 127.0.0.1 --port 8000


