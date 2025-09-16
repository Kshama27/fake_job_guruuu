$ErrorActionPreference = "Stop"

# set optional model path env var if models/scam_detector.pkl exists
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$defaultModel = Join-Path $root "models\scam_detector.pkl"
if (Test-Path $defaultModel) {
  $env:SCAM_MODEL_PATH = $defaultModel
}

# ensure Python can import nested package path (fake_job_guruuu\fake_job_guru)
$env:PYTHONPATH = "$root;" + (Join-Path $root "fake_job_guruuu")

# run uvicorn using the new asgi entrypoint
uvicorn asgi:app --reload --host 127.0.0.1 --port 8000


