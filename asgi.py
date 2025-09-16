# asgi.py — robust entrypoint so uvicorn can import the app from project root
import importlib
import sys
from pathlib import Path

# ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# try importing the main app module
try:
    mod = importlib.import_module("fake_job_guru.api")
except Exception as e:
    # helpful error for debugging when module import fails
    raise RuntimeError(f"Failed to import fake_job_guru.api — check package name and file path. Original error: {e}") from e

# locate FastAPI app instance or factory
if hasattr(mod, "app"):
    app = getattr(mod, "app")
elif hasattr(mod, "create_app"):
    # support factory pattern if present
    app = getattr(mod, "create_app")()
else:
    raise RuntimeError("No FastAPI 'app' instance or 'create_app' factory found in fake_job_guru.api")


