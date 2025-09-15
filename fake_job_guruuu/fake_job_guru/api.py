from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
import time
import platform
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, ValidationError
from pydantic import field_validator
from pydantic import ConfigDict

from .scam_detector import predict_job


app = FastAPI(title="Fake Job Scam Detector API", version="1.0.0")


# ===============================
# Logging
# ===============================
logger = logging.getLogger("scam_api")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


# ===============================
# Load enriched dataset (optional, for context/validation)
# ===============================
ENRICHED_DF = None
_ROOT_DIR = Path(__file__).resolve().parent.parent
ENRICHED_PATH = _ROOT_DIR / "enriched_dataset.csv"
if not ENRICHED_PATH.exists():
    # Fallback: same directory as API file
    ENRICHED_PATH = Path(__file__).resolve().parent / "enriched_dataset.csv"
try:
    import pandas as _pd  # lazy dependency only for loading
    if ENRICHED_PATH.exists():
        ENRICHED_DF = _pd.read_csv(ENRICHED_PATH)
except Exception:
    ENRICHED_DF = None


class AnalyzeJobRequest(BaseModel):
    # Core text fields
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    company_profile: Optional[str] = None

    # Enriched numeric signals (optional)
    company_followers: Optional[int] = Field(default=None, alias="followers")
    company_employees: Optional[int] = Field(default=None, alias="employees")
    engagement_score: Optional[int] = Field(default=None, alias="engagement")

    # Derived/enriched categorical/flags (optional)
    company_strength: Optional[str] = None
    missing_website_flag: Optional[int] = None
    suspicious_email_flag: Optional[int] = None
    short_profile_flag: Optional[int] = None
    suspicion_score: Optional[int] = None

    @field_validator("company_strength")
    def validate_company_strength(cls, v):
        if v is None:
            return v
        allowed = {"weak", "medium", "strong"}
        lv = str(v).lower()
        if lv not in allowed:
            raise ValueError(f"company_strength must be one of {sorted(allowed)}")
        return lv

    @field_validator("missing_website_flag", "suspicious_email_flag", "short_profile_flag", mode="before")
    def validate_binary_flags(cls, v):
        if v is None:
            return v
        try:
            iv = int(v)
        except Exception:
            raise ValueError("flag fields must be integers 0 or 1")
        if iv not in (0, 1):
            raise ValueError("flag fields must be 0 or 1")
        return iv

    model_config = ConfigDict(populate_by_name=True)


class AnalyzeJobResponse(BaseModel):
    prediction: str
    probabilities: Dict[str, float]
    risk_score: float
    signals: Dict[str, Any]


@app.get("/", response_class=HTMLResponse)
def serve_ui():
    """Serve the main UI page."""
    template_path = Path(__file__).resolve().parent / "templates" / "index.html"
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        # Fallback: return a simple HTML string if template file is not found
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><title>Fake Job Guru</title></head>
        <body>
            <h1>Fake Job Guru</h1>
            <p>Template file not found. Please ensure templates/index.html exists.</p>
        </body>
        </html>
        """)


@app.get("/health")
def health() -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "status": "ok",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "pid": os.getpid(),
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "app_version": app.version,
    }
    if ENRICHED_DF is not None:
        try:
            info.update({
                "dataset_rows": int(ENRICHED_DF.shape[0]),
                "dataset_cols": int(ENRICHED_DF.shape[1]),
            })
        except Exception:
            pass
    return info


@app.post("/analyze_job", response_model=AnalyzeJobResponse)
def analyze_job(payload: AnalyzeJobRequest, request: Request):
    start = time.time()
    try:
        logger.info("analyze_job request: %s", {
            "remote": request.client.host if request.client else None,
            "title_len": len(payload.title or ""),
            "description_len": len(payload.description or ""),
            "followers": payload.company_followers,
            "employees": payload.company_employees,
            "engagement": payload.engagement_score,
        })

        result = predict_job(
            title=payload.title,
            description=payload.description,
            requirements=payload.requirements,
            company_profile=payload.company_profile,
            followers=payload.company_followers,
            employees=payload.company_employees,
            engagement=payload.engagement_score,
            company_strength=payload.company_strength,
            missing_website_flag=payload.missing_website_flag,
            suspicious_email_flag=payload.suspicious_email_flag,
            short_profile_flag=payload.short_profile_flag,
            suspicion_score=payload.suspicion_score,
        )

        logger.info("analyze_job response: %s", {
            "prediction": result.get("prediction"),
            "risk_score": result.get("risk_score"),
            "prob_scam": result.get("probabilities", {}).get("scam"),
            "keyword_hits": len(result.get("signals", {}).get("keywords_triggered", [])),
            "latency_ms": int((time.time() - start) * 1000),
        })
        return AnalyzeJobResponse(**result)
    except ValidationError as ve:
        logger.warning("validation error: %s", ve)
        raise HTTPException(status_code=422, detail=ve.errors())
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("unhandled error")
        raise HTTPException(status_code=500, detail="Internal server error")


# Local dev entrypoint: uvicorn fake_job_guru.api:app --reload

