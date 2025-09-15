import re
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib

"""
Prediction utilities for scam detection with structured risk scoring.

Responsibilities:
- Load the trained text model artifact safely.
- Provide `predict_job` which accepts job details and optional enriched features.
- Return structured prediction with probabilities, a composite risk score,
  and a transparent breakdown of contributing signals.

Backwards compatibility:
- Output retains keys: `prediction`, `probabilities`, `risk_score`, and `signals`.
- Additional non-breaking fields may be present (e.g., `risk_breakdown`).
"""

# ===============================
# Load trained model (path-safe)
# ===============================
# To override the model location, set environment variable `SCAM_MODEL_PATH`
# to an absolute path or project-relative path to the `.pkl` file.
_THIS_DIR = Path(__file__).resolve().parent
# default: project_root/models/scam_detector.pkl
_DEFAULT_MODEL = _THIS_DIR.parent / "models" / "scam_detector.pkl"
_MODEL_PATH = Path(os.getenv("SCAM_MODEL_PATH", str(_DEFAULT_MODEL)))

# If the env path does not exist, fall back to a local file (legacy)
if not _MODEL_PATH.exists():
    _LEGACY = _THIS_DIR / "scam_detector.pkl"
    if _LEGACY.exists():
        _MODEL_PATH = _LEGACY

model = joblib.load(str(_MODEL_PATH))

# Scammy keywords list
SCAM_KEYWORDS = [
    "work from home", "no experience", "quick money",
    "earn $", "gmail.com", "telegram", "whatsapp",
    "fast cash", "limited slots", "easy income"
]

def _safe_int(value: Optional[Any], default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _compute_company_strength(followers: int, employees: int) -> str:
    if followers < 500 or employees < 20:
        return "weak"
    elif 500 <= followers <= 5000:
        return "medium"
    else:
        return "strong"


def _heuristic_flags(company_profile: Optional[str], description: Optional[str], requirements: Optional[str]) -> Dict[str, int]:
    text_profile = "" if company_profile is None else str(company_profile)
    text_desc = "" if description is None else str(description)
    text_req = "" if requirements is None else str(requirements)

    missing_website_flag = 1 if (len(text_profile) == 0 or "http" not in text_profile.lower()) else 0

    def suspicious_contact(text: str) -> int:
        lowered = text.lower()
        suspicious_terms = ["gmail", "yahoo", "telegram", "whatsapp"]
        return 1 if any(term in lowered for term in suspicious_terms) else 0

    suspicious_email_flag = 1 if (suspicious_contact(text_desc) or suspicious_contact(text_req)) else 0
    short_profile_flag = 1 if (len(text_profile.strip()) == 0 or len(text_profile.split()) < 30) else 0

    suspicion_score = missing_website_flag + suspicious_email_flag + short_profile_flag
    return {
        "missing_website_flag": missing_website_flag,
        "suspicious_email_flag": suspicious_email_flag,
        "short_profile_flag": short_profile_flag,
        "suspicion_score": suspicion_score,
    }


def _composite_risk(prob_scam: float, weak_company: bool, suspicion_score: int, keyword_hits: int) -> Dict[str, Any]:
    """Compute an explainable composite risk score in [0, 1].

    Approach: start at model probability and add small, bounded contributions from
    heuristics. Keep weights conservative to avoid overshadowing the model.
    Returns both the final score and a per-factor breakdown for transparency.
    """
    base = float(prob_scam)
    contrib_weak_company = 0.08 if weak_company else 0.0
    contrib_suspicion = min(0.12, 0.04 * max(0, suspicion_score))
    contrib_keywords = min(0.10, 0.03 * max(0, keyword_hits))

    raw_score = base + contrib_weak_company + contrib_suspicion + contrib_keywords
    score = max(0.0, min(1.0, raw_score))

    return {
        "score": score,
        "breakdown": {
            "model_probability": base,
            "weak_company": contrib_weak_company,
            "suspicion_score": contrib_suspicion,
            "keyword_hits": contrib_keywords,
            "clamped": score != raw_score,
        }
    }


def predict_job(
    title: Optional[str] = None,
    description: Optional[str] = None,
    requirements: Optional[str] = None,
    company_profile: Optional[str] = None,
    followers: Optional[int] = None,
    employees: Optional[int] = None,
    engagement: Optional[int] = None,
    company_strength: Optional[str] = None,
    missing_website_flag: Optional[int] = None,
    suspicious_email_flag: Optional[int] = None,
    short_profile_flag: Optional[int] = None,
    suspicion_score: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Predict whether a job posting is scam or legit and return structured signals.

    Any enriched feature parameters are optional. If omitted, lightweight heuristics
    are applied to derive reasonable defaults.
    """
    # Combine text for model
    text = " ".join([
        str(title or ""),
        str(description or ""),
        str(requirements or ""),
        str(company_profile or ""),
    ])

    # Model probability for class 1 (scam)
    # Ensure we extract the probability for label 1 irrespective of ordering
    proba = model.predict_proba([text])[0]
    # model.classes_ is typically [0,1]; find index of class 1
    try:
        idx_scam = list(getattr(model, "classes_", [0, 1])).index(1)
    except ValueError:
        idx_scam = 1 if len(proba) > 1 else 0
    prob_scam = float(proba[idx_scam])

    # Keyword explainability
    lowered = text.lower()
    found_keywords = [kw for kw in SCAM_KEYWORDS if re.search(kw, lowered)]

    # Company signals
    followers_i = _safe_int(followers, 0)
    employees_i = _safe_int(employees, 0)
    engagement_i = _safe_int(engagement, 0)

    if not company_strength:
        company_strength = _compute_company_strength(followers_i, employees_i)
    weak_company = (followers_i < 500) or (employees_i < 10) or (engagement_i < 5)

    # Heuristic flags (prefer provided flags if supplied)
    if missing_website_flag is None or suspicious_email_flag is None or short_profile_flag is None or suspicion_score is None:
        heur = _heuristic_flags(company_profile, description, requirements)
        missing_website_flag = heur["missing_website_flag"] if missing_website_flag is None else missing_website_flag
        suspicious_email_flag = heur["suspicious_email_flag"] if suspicious_email_flag is None else suspicious_email_flag
        short_profile_flag = heur["short_profile_flag"] if short_profile_flag is None else short_profile_flag
        suspicion_score = heur["suspicion_score"] if suspicion_score is None else suspicion_score

    # Composite risk with breakdown
    risk = _composite_risk(prob_scam, weak_company, int(suspicion_score), len(found_keywords))
    risk_score = float(risk["score"])  # maintain existing field name

    prediction_label = "scam" if prob_scam >= 0.5 else "legit"

    result = {
        "prediction": prediction_label,
        "probabilities": {
            "scam": round(prob_scam, 4),
            "legit": round(1.0 - prob_scam, 4),
        },
        "risk_score": round(risk_score, 4),
        "signals": {
            "keywords_triggered": found_keywords,
            "weak_company": weak_company,
            "company_strength": company_strength,
            "followers": followers_i,
            "employees": employees_i,
            "engagement": engagement_i,
            "missing_website_flag": int(missing_website_flag),
            "suspicious_email_flag": int(suspicious_email_flag),
            "short_profile_flag": int(short_profile_flag),
            "suspicion_score": int(suspicion_score),
        },
    }
    # Non-breaking, additional explainability
    result["risk_breakdown"] = risk["breakdown"]
    result["model_artifact"] = {
        "path": str(_MODEL_PATH),
    }
    return result


# ===============================
# Self-Test (runs if file is executed directly)
# ===============================
if __name__ == "__main__":
    # Quick self-test
    scam_test = predict_job(
        title="Data Entry Clerk",
        description="Earn $500/day working from home. No experience required. Apply via Gmail.",
        requirements="Basic typing skills",
        company_profile="Small startup",
        followers=120,
        employees=3,
        engagement=1
    )
    print("\n🚨 Scam Example Test:")
    print(scam_test)

    legit_test = predict_job(
        title="Software Engineer",
        description="We are seeking an experienced software engineer to join our team and work on scalable backend systems.",
        requirements="3+ years of experience, knowledge of Python/Java",
        company_profile="Reputed multinational",
        followers=450000,
        employees=1200,
        engagement=200
    )
    print("\n✅ Legit Example Test:")
    print(legit_test)
