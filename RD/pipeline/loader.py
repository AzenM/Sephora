"""Load and clean the raw Sephora CSV."""

import pandas as pd
import numpy as np
from pathlib import Path

STATUS_MAP = {1: "Gold", 2: "Silver", 3: "Bronze", 4: "No Loyalty"}

RFM_MAP = {
    1: "Champions",
    2: "Loyal",
    3: "Potential Loyalist",
    4: "Recent",
    5: "Promising",
    6: "Need Attention",
    7: "About to Sleep",
    8: "At Risk",
    9: "Can't Lose",
    10: "Hibernating",
    11: "Lost",
}

CHANNEL_CLEAN = {
    "store": "Store",
    "app": "App",
    "web": "Web",
    "click_and_collect": "Click & Collect",
    "customer_service": "Customer Service",
}


def load_raw(path: str | Path | None = None) -> pd.DataFrame:
    """Read CSV, parse dates, clean types."""
    if path is None:
        path = Path(__file__).resolve().parents[1] / ".." / "BDD#7_Database_Albert_School_Sephora.csv"
    df = pd.read_csv(path, low_memory=False)

    # --- dates ---
    for col in ["transactionDate", "subscription_date", "first_purchase_dt"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=False)

    # --- numeric ---
    for col in ["salesVatEUR", "discountEUR", "quantity",
                 "salesVatEUR_first_purchase", "discountEUR_first_purchase",
                 "quantity_first_purchase", "age"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- categorical labels ---
    df["loyalty_label"] = df["status"].map(STATUS_MAP).fillna("Unknown")
    df["rfm_label"] = df["RFM_Segment_ID"].map(RFM_MAP).fillna("Unknown")
    df["channel_clean"] = df["channel"].map(CHANNEL_CLEAN).fillna(df["channel"])

    # --- drop exact duplicate rows ---
    df = df.drop_duplicates()

    # --- discount ratio ---
    df["discount_ratio"] = np.where(
        df["salesVatEUR"] > 0,
        df["discountEUR"] / (df["salesVatEUR"] + df["discountEUR"]),
        0,
    )

    return df
