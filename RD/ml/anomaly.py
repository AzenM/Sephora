"""Path anomaly detection — find rare but profitable journeys."""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


def detect_anomalies(journey_features: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    """Identify rare journey patterns, then flag which are high-value anomalies."""

    feature_cols = [
        "total_revenue", "n_tickets", "avg_basket", "revenue_90d",
        "tenure_days", "avg_inter_purchase_days", "days_to_second",
        "n_unique_categories", "n_unique_channels", "discount_ratio",
        "first_basket_value", "spending_volatility",
    ]

    X = journey_features[feature_cols].fillna(0).copy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    iso = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=42,
    )
    labels = iso.fit_predict(X_scaled)
    scores = iso.decision_function(X_scaled)

    result = journey_features[["anonymized_card_code"]].copy()
    result["anomaly_label"] = labels  # -1 = anomaly, 1 = normal
    result["anomaly_score"] = scores  # lower = more anomalous
    result["is_anomaly"] = (labels == -1).astype(int)

    # merge with customer value
    result = result.merge(
        customers[["anonymized_card_code", "total_revenue", "high_value", "rfm_label"]],
        on="anonymized_card_code",
        how="left",
    )

    # flag high-value anomalies (rare AND profitable)
    result["high_value_anomaly"] = (
        (result["is_anomaly"] == 1) & (result["high_value"] == 1)
    ).astype(int)

    # summary stats
    anomalies = result[result["is_anomaly"] == 1]
    normals = result[result["is_anomaly"] == 0]
    print(f"Anomalies: {len(anomalies)} ({len(anomalies)/len(result)*100:.1f}%)")
    print(f"  High-value anomalies: {result['high_value_anomaly'].sum()}")
    print(f"  Avg revenue (anomalies): €{anomalies['total_revenue'].mean():,.0f}")
    print(f"  Avg revenue (normal): €{normals['total_revenue'].mean():,.0f}")

    return result
