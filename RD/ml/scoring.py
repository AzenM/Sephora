"""Winning Path Score + XGBoost high-value prediction."""

import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None

try:
    from catboost import CatBoostClassifier
except ImportError:
    CatBoostClassifier = None


FEATURE_COLS = [
    "total_revenue", "n_tickets", "avg_basket", "revenue_90d",
    "tenure_days", "avg_inter_purchase_days", "days_to_second",
    "n_unique_categories", "n_unique_channels", "is_omnichannel",
    "discount_ratio", "first_basket_value", "spending_volatility",
]

MODEL_FEATURE_COLS = [
    "revenue_90d",
    "days_to_second",
    "first_basket_value",
    "first_purchase_discounted",
    "first_purchase_discount_ratio",
    "second_purchase_within_30d",
    "second_purchase_within_60d",
    "revenue_first_2_visits",
    "avg_basket_first_2_visits",
    "categories_first_2_visits",
    "channels_first_2_visits",
]


def compute_winning_path_score(journey_features: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    """
    Fusion score: process conformance + survival proxy + similarity to elites + discount resilience.
    Returns customers with a 0–100 Winning Path Score.
    """

    df = journey_features.merge(
        customers[["anonymized_card_code", "high_value", "repeat_customer", "RFM_Segment_ID", "loyalty_label"]],
        on="anonymized_card_code",
        how="left",
    )

    # --- Component 1: RFM quality (lower ID = better) ---
    max_rfm = df["RFM_Segment_ID"].max()
    df["rfm_score"] = np.where(
        df["RFM_Segment_ID"].notna(),
        1 - (df["RFM_Segment_ID"] - 1) / max(max_rfm - 1, 1),
        0,
    )

    # --- Component 2: Retention / repeat signal ---
    df["retention_score"] = np.where(df["repeat_customer"] == 1, 1.0, 0.0)

    # --- Component 3: Revenue percentile ---
    df["revenue_pct"] = df["total_revenue"].rank(pct=True)

    # --- Component 4: Speed to second purchase (inverted, faster = better) ---
    d2s = df["days_to_second"].replace(9999, np.nan)
    max_d2s = d2s.quantile(0.95)
    df["speed_score"] = np.where(
        d2s.notna(),
        1 - (d2s.clip(upper=max_d2s) / max_d2s),
        0,
    )

    # --- Component 5: Omnichannel + category diversity ---
    df["diversity_score"] = (
        0.5 * df["is_omnichannel"] +
        0.5 * (df["n_unique_categories"] / df["n_unique_categories"].max())
    )

    # --- Component 6: Discount resilience (lower discount ratio = better) ---
    df["discount_resilience"] = 1 - df["discount_ratio"]

    # --- Component 7: Loyalty tier ---
    tier_scores = {"Gold": 1.0, "Silver": 0.66, "Bronze": 0.33, "No Loyalty": 0.0}
    df["loyalty_score"] = df["loyalty_label"].map(tier_scores).fillna(0)

    # --- Weighted fusion ---
    df["winning_path_score"] = (
        0.20 * df["rfm_score"] +
        0.15 * df["retention_score"] +
        0.20 * df["revenue_pct"] +
        0.10 * df["speed_score"] +
        0.10 * df["diversity_score"] +
        0.10 * df["discount_resilience"] +
        0.15 * df["loyalty_score"]
    ) * 100

    df["winning_path_score"] = df["winning_path_score"].clip(0, 100).round(1)

    # --- Tier assignment ---
    df["wp_tier"] = pd.cut(
        df["winning_path_score"],
        bins=[0, 25, 50, 75, 100],
        labels=["At Risk", "Developing", "Strong", "Elite"],
        include_lowest=True,
    )

    return df


def train_high_value_model(
    journey_features: pd.DataFrame,
    customers: pd.DataFrame,
    save_path=None,
    preferred_model: str = "catboost",
):
    """Train high-value prediction model (CatBoost priority, XGBoost fallback)."""

    if CatBoostClassifier is None and XGBClassifier is None:
        print("catboost/xgboost not installed — skipping model training")
        return None, None, None

    df = journey_features.merge(
        customers[["anonymized_card_code", "high_value"]],
        on="anonymized_card_code",
        how="left",
    )
    df = df.dropna(subset=["high_value"])

    X = df[MODEL_FEATURE_COLS].fillna(0)
    y = df["high_value"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    use_catboost = preferred_model.lower() == "catboost" and CatBoostClassifier is not None

    if use_catboost:
        model = CatBoostClassifier(
            iterations=500,
            depth=6,
            learning_rate=0.05,
            loss_function="Logloss",
            eval_metric="AUC",
            random_seed=42,
            verbose=False,
        )
        model.fit(X_train, y_train, eval_set=(X_test, y_test), use_best_model=True)
        model_name = "catboost"
    else:
        model = XGBClassifier(
            n_estimators=350,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric="logloss",
        )
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
        model_name = "xgboost"

    y_pred_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_pred_proba)
    print(f"{model_name} AUC: {auc:.4f}")

    report = classification_report(y_test, model.predict(X_test), output_dict=True)

    # feature importance
    importance = pd.DataFrame(
        {
            "feature": MODEL_FEATURE_COLS,
            "importance": model.feature_importances_,
            "model": model_name,
        }
    ).sort_values("importance", ascending=False)

    if save_path:
        with open(save_path, "wb") as f:
            pickle.dump(model, f)

    return model, importance, {"auc": auc, "report": report, "model": model_name}
