import pandas as pd
import numpy as np
import re

# Load the dataset
df = pd.read_csv("../fake_job_postings.csv")


# ============================
# STEP 1: Synthetic Company Stats
# ============================
df["company_followers"] = np.random.randint(50, 50001, df.shape[0])
df["company_employees"] = np.random.randint(1, 10001, df.shape[0])
df["engagement_score"] = np.random.randint(0, 101, df.shape[0])

def get_company_strength(followers, employees):
    if followers < 500 or employees < 20:
        return "weak"
    elif 500 <= followers <= 5000:
        return "medium"
    else:
        return "strong"

df["company_strength"] = df.apply(
    lambda row: get_company_strength(row["company_followers"], row["company_employees"]),
    axis=1
)

# ============================
# STEP 2: Scammy Indicator Flags
# ============================
# Missing website
df["missing_website_flag"] = df["company_profile"].apply(
    lambda x: 1 if (pd.isna(x) or "http" not in str(x).lower()) else 0
)

# Suspicious contact terms
def suspicious_contact(text):
    if pd.isna(text):
        return 0
    text = text.lower()
    suspicious_terms = ["gmail", "yahoo", "telegram", "whatsapp"]
    return 1 if any(term in text for term in suspicious_terms) else 0

df["suspicious_email_flag"] = df.apply(
    lambda row: suspicious_contact(str(row["description"])) or suspicious_contact(str(row["requirements"])),
    axis=1
)

# Short company profile
df["short_profile_flag"] = df["company_profile"].apply(
    lambda x: 1 if (pd.isna(x) or len(str(x).split()) < 30) else 0
)

# ============================
# STEP 3: Aggregate Suspicion Score
# ============================
df["suspicion_score"] = (
    df["missing_website_flag"] +
    df["suspicious_email_flag"] +
    df["short_profile_flag"]
)

# Save enriched dataset
df.to_csv("enriched_dataset.csv", index=False)

print("✅ Enrichment complete. Saved as enriched_dataset.csv")
