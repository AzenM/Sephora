"""Native Streamlit app for Winning Paths.

This app intentionally uses Streamlit-native layout primitives only.
No custom JS components are required.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_loader import store
from pipeline.paths import summarize_journey_variants


INK = "#17120F"
PEARL = "#F4EFE7"
IVORY = "#FBF8F2"
TAUPE = "#6F6255"
GOLD = "#B68A3A"
CHAMPAGNE = "#D9BC79"
GREEN = "#2F8A60"
RED = "#B55248"

FRAGILE_SEGMENTS = {"Need Attention", "About to Sleep", "At Risk", "Hibernating", "Lost", "Can't Lose"}
GROWTH_SEGMENTS = {"Potential Loyalist", "Recent", "Promising"}
HIGH_VALUE_SEGMENTS = {"Champions", "Loyal"}
MILESTONE_EVENTS = [
    "first_purchase",
    "second_purchase_under_30d",
    "second_purchase_under_60d",
    "second_purchase_late",
    "omnichannel_adoption",
    "category_expansion",
    "high_basket_event",
    "high_discount_purchase",
    "bronze_reached",
    "silver_reached",
    "gold_reached",
    "moved_to_rfm_1",
    "moved_to_rfm_2",
    "moved_to_rfm_3",
    "reactivated",
]
MILESTONE_LABELS = {
    "first_purchase": "First",
    "second_purchase_under_30d": "P2 <30d",
    "second_purchase_under_60d": "P2 30-60d",
    "second_purchase_late": "P2 >60d",
    "omnichannel_adoption": "Omni",
    "category_expansion": "Cat+",
    "high_basket_event": "Basket+",
    "high_discount_purchase": "Promo+",
    "bronze_reached": "Bronze",
    "silver_reached": "Silver",
    "gold_reached": "Gold",
    "moved_to_rfm_1": "RFM1",
    "moved_to_rfm_2": "RFM2",
    "moved_to_rfm_3": "RFM3",
    "reactivated": "React",
}
MILESTONE_STAGE = {
    "first_purchase": 0,
    "second_purchase_under_30d": 1,
    "second_purchase_under_60d": 1,
    "second_purchase_late": 1,
    "high_basket_event": 2,
    "high_discount_purchase": 2,
    "category_expansion": 2,
    "omnichannel_adoption": 2,
    "bronze_reached": 3,
    "silver_reached": 3,
    "gold_reached": 3,
    "moved_to_rfm_3": 3,
    "moved_to_rfm_2": 4,
    "moved_to_rfm_1": 5,
    "reactivated": 4,
}
RFM_ORDER = [
    "Champions",
    "Loyal",
    "Potential Loyalist",
    "Recent",
    "Promising",
    "Need Attention",
    "About to Sleep",
    "At Risk",
    "Can't Lose",
    "Hibernating",
    "Lost",
]
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Georgia, serif", color=INK, size=13),
    margin=dict(l=24, r=18, t=44, b=24),
    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1.0),
)
PLOTLY_CONFIG = {"displayModeBar": False, "displaylogo": False, "responsive": True}
OUTPUT_PACK_ROOT = Path(__file__).resolve().parents[1] / "output" / "RD_product_pack"


def _apply_base_style() -> None:
    st.markdown(
        f"""
        <style>
        [data-testid="stSidebarNav"] {{
            display: none;
        }}
        [data-testid="stToolbar"] {{
            visibility: hidden;
            height: 0;
            position: fixed;
        }}
        [data-testid="collapsedControl"] {{
            display: none;
        }}
        .block-container {{
            max-width: 1450px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }}
        html, body, [class*="css"] {{
            color: {INK};
        }}
        h1, h2, h3 {{
            letter-spacing: -0.03em;
            color: {INK};
        }}
        div[data-testid="stMetric"] {{
            background: {IVORY};
            border: 1px solid rgba(182, 138, 58, 0.22);
            border-radius: 18px;
            padding: 1rem 1.05rem;
        }}
        div[data-testid="stMetricLabel"] {{
            color: {TAUPE};
            font-size: 0.86rem;
        }}
        div[data-testid="stMetricValue"] {{
            color: {INK};
            font-size: 1.9rem;
        }}
        div[data-testid="stDataFrame"] {{
            border: 1px solid rgba(182, 138, 58, 0.16);
            border-radius: 18px;
            overflow: hidden;
        }}
        .stButton > button, .stDownloadButton > button {{
            border-radius: 999px;
            border: 1px solid rgba(182, 138, 58, 0.35);
            color: {INK};
            background: {IVORY};
        }}
        .body-copy {{
            color: {TAUPE};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def load_store():
    return store.load()


def _fmt_eur(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "EUR 0"
    return f"EUR {float(value):,.0f}"


def _fmt_eur_short(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "EUR 0"
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"EUR {value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"EUR {value / 1_000:.0f}K"
    return f"EUR {value:,.0f}"


def _fmt_pct(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "0.0%"
    return f"{float(value) * 100:.1f}%"


def _shorten(text: str | None, width: int = 88) -> str:
    if text is None or pd.isna(text):
        return "Unknown"
    text = str(text)
    return text if len(text) <= width else text[: width - 3] + "..."


def _mode(series: pd.Series, fallback: str = "Mixed") -> str:
    cleaned = series.dropna().astype(str)
    if cleaned.empty:
        return fallback
    mode = cleaned.mode()
    if mode.empty:
        return fallback
    return str(mode.iloc[0])


def _normalize_makeup(text: str) -> str:
    return text.replace("MAEK UP", "MAKE UP")


def _first_token(path: str | float | None, fallback: str = "Unknown") -> str:
    if path is None or pd.isna(path):
        return fallback
    text = str(path).strip()
    if not text:
        return fallback
    return _normalize_makeup(text.split(" -> ")[0].strip()).title()


def _pretty_label(value: str | float | None, fallback: str = "Unknown") -> str:
    if value is None or pd.isna(value):
        return fallback
    text = _normalize_makeup(str(value).strip())
    if not text or text.lower() in {"nan", "none", "unknown"}:
        return fallback
    if "|" in text:
        parts = []
        for raw in text.split("|"):
            part = raw.strip()
            if part and part not in parts:
                parts.append(part.title())
        if not parts:
            return fallback
        if len(parts) == 1:
            return parts[0]
        return f"Mixed Basket ({parts[0]} + {len(parts) - 1} others)"
    return text.title()


def _to_csv_download(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()


def _prepare_customers(
    customers: pd.DataFrame,
    path_scores: pd.DataFrame | None,
    anomalies: pd.DataFrame | None,
) -> pd.DataFrame:
    df = customers.copy()
    df["anonymized_card_code"] = df["anonymized_card_code"].astype(str)
    df["customer_id"] = df["anonymized_card_code"]
    df["first_category_display"] = df["Axe_Desc_first_purchase"].apply(_pretty_label)
    df.loc[df["first_category_display"] == "Unknown", "first_category_display"] = df["category_path"].apply(_first_token)
    df["first_channel_display"] = df["channel_recruitment"].apply(_pretty_label)
    df.loc[df["first_channel_display"] == "Unknown", "first_channel_display"] = df["channel_path"].apply(_first_token)
    df["first_brand_display"] = df["brand_first_purchase"].apply(_pretty_label)
    df.loc[df["first_brand_display"] == "Unknown", "first_brand_display"] = df["brand_path"].apply(_first_token)
    df["country_display"] = df["countryIsoCode"].fillna("Unknown").astype(str).str.upper()
    df["city_display"] = df["customer_city"].fillna("Unknown").astype(str).str.title()
    df["age_display"] = df["age_category"].fillna("Unknown").astype(str)
    df["gender_display"] = df["gender"].fillna("Unknown").astype(str)
    df["value_band"] = pd.cut(
        df["value_12m_proxy"],
        bins=[-np.inf, df["value_12m_proxy"].quantile(0.5), df["value_12m_proxy"].quantile(0.85), np.inf],
        labels=["Core", "Growth", "Premium"],
    ).astype(str)

    max_date = df["last_date"].max()
    df["days_since_last"] = (max_date - df["last_date"]).dt.days
    df["risk_band"] = pd.cut(
        df["days_since_last"],
        bins=[-1, 30, 60, 90, 180, np.inf],
        labels=["Active", "Cooling", "Drifting", "At Risk", "Inactive"],
    ).astype(str)

    df["phase_proxy"] = np.select(
        [
            df["repeat_customer"] == 0,
            df["risk_band"].isin(["At Risk", "Inactive"]),
            df["discount_ratio"] >= 0.30,
            (df["is_omnichannel"] == 1) & (df["n_unique_categories"] >= 3),
            (df["repeat_customer"] == 1) & (df["days_to_second"].fillna(9999) <= 60),
        ],
        ["Onboarding", "Erosion", "Promo Dependence", "Exploration", "Acceleration"],
        default="Consolidation",
    )

    if path_scores is not None and not path_scores.empty:
        scores = path_scores.copy()
        scores["anonymized_card_code"] = scores["anonymized_card_code"].astype(str)
        df = df.merge(
            scores[["anonymized_card_code", "winning_path_score", "wp_tier", "archetype"]],
            on="anonymized_card_code",
            how="left",
        )
    else:
        df["winning_path_score"] = np.nan
        df["wp_tier"] = "Unknown"
        df["archetype"] = "Unknown"

    if anomalies is not None and not anomalies.empty:
        anomaly_view = anomalies.copy()
        anomaly_view["anonymized_card_code"] = anomaly_view["anonymized_card_code"].astype(str)
        df = df.merge(
            anomaly_view[["anonymized_card_code", "is_anomaly", "high_value_anomaly"]],
            on="anonymized_card_code",
            how="left",
        )
    else:
        df["is_anomaly"] = 0
        df["high_value_anomaly"] = 0

    return df


def _prepare_cohort_summary(cohort_summary: pd.DataFrame) -> pd.DataFrame:
    summary = cohort_summary.copy()
    summary["first_category_display"] = summary["Axe_Desc_first_purchase"].apply(_pretty_label)
    summary["channel_display"] = summary["channel_recruitment"].apply(_pretty_label)
    summary["discount_label"] = summary["discount_label"].fillna("Unknown")
    summary["cohort_label"] = (
        summary["first_category_display"] + " / "
        + summary["channel_display"] + " / "
        + summary["discount_label"]
    )
    summary["estimated_value_pool"] = summary["customers"] * summary["avg_12m_value"]
    return summary


def _category_opportunities(transitions_category: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    if transitions_category is None or transitions_category.empty:
        return pd.DataFrame()

    customer_lookup = customers[[
        "customer_id",
        "value_12m_proxy",
        "margin_12m_proxy",
        "repeat_customer",
        "high_value",
    ]].copy()

    moves = transitions_category.copy()
    moves["anonymized_card_code"] = moves["anonymized_card_code"].astype(str)
    moves = moves.merge(
        customer_lookup,
        left_on="anonymized_card_code",
        right_on="customer_id",
        how="left",
    )

    split = moves["cat_transition"].fillna("Unknown -> Unknown").str.split(" -> ", n=1, expand=True)
    moves["from_category"] = split[0].fillna("Unknown").map(_pretty_label)
    moves["to_category"] = split[1].fillna("Unknown").map(_pretty_label)
    moves = moves[
        (moves["from_category"] != "Unknown")
        & (moves["to_category"] != "Unknown")
        & (moves["from_category"] != moves["to_category"])
    ]

    summary = (
        moves.groupby(["cat_transition", "from_category", "to_category"], dropna=False)
        .agg(
            customers=("anonymized_card_code", "nunique"),
            avg_12m_value=("value_12m_proxy", "mean"),
            avg_margin_12m=("margin_12m_proxy", "mean"),
            high_value_rate=("high_value", "mean"),
            repeat_rate=("repeat_customer", "mean"),
            median_gap_days=("days_between_visits", "median"),
        )
        .reset_index()
    )
    summary = summary[summary["customers"] >= 50].copy()
    if summary.empty:
        return summary

    summary["transition_value_pool"] = summary["customers"] * summary["avg_12m_value"]
    summary["commercial_play"] = (
        "When customers start in "
        + summary["from_category"]
        + ", push "
        + summary["to_category"]
        + " before day 60 with a routine-led cross-sell."
    )
    return summary.sort_values(
        ["high_value_rate", "avg_12m_value", "customers"],
        ascending=[False, False, False],
    )


def _variant_actions(journey_variants: pd.DataFrame) -> pd.DataFrame:
    if journey_variants is None or journey_variants.empty:
        return pd.DataFrame()

    variants = journey_variants.copy()
    robust = variants[variants["customers"] >= 25].copy()
    if robust.empty:
        robust = variants.copy()

    high_value_q = robust["avg_12m_value"].quantile(0.75)
    low_value_q = robust["avg_12m_value"].quantile(0.25)
    high_hv_q = robust["high_value_rate"].quantile(0.75)
    low_hv_q = robust["high_value_rate"].quantile(0.25)
    high_discount_q = robust["discount_reliance"].quantile(0.75)
    low_omni_floor = max(0.25, float(robust["omnichannel_rate"].median()))
    scale_size = max(25, int(robust["customers"].quantile(0.60)))

    variants["motion"] = np.select(
        [
            (variants["customers"] >= scale_size)
            & (variants["avg_12m_value"] >= high_value_q)
            & (variants["high_value_rate"] >= high_hv_q),
            (variants["customers"] >= max(15, scale_size // 2))
            & (
                (variants["discount_reliance"] >= high_discount_q)
                | (variants["avg_days_to_second"].fillna(9999) > 60)
                | (variants["omnichannel_rate"] < low_omni_floor)
            )
            & (variants["avg_12m_value"] >= low_value_q),
            (variants["customers"] >= scale_size)
            & (variants["avg_12m_value"] <= low_value_q)
            & (variants["high_value_rate"] <= low_hv_q)
            & (variants["discount_reliance"] >= high_discount_q),
        ],
        ["Scale", "Fix", "Stop"],
        default="Monitor",
    )

    def reason(row: pd.Series) -> str:
        reasons: list[str] = []
        path = str(row.get("milestone_path", ""))
        if row["high_value_rate"] >= high_hv_q:
            reasons.append("high-value conversion is structurally strong")
        if "category_expansion" not in path:
            reasons.append("category depth is still missing")
        if "omnichannel_adoption" not in path or row["omnichannel_rate"] < low_omni_floor:
            reasons.append("omnichannel adoption stays too low")
        if row["avg_days_to_second"] > 60:
            reasons.append("second purchase happens too late")
        if row["discount_reliance"] >= high_discount_q:
            reasons.append("economics are too promo-heavy")
        if not reasons:
            reasons.append("the economics are balanced but not decisive yet")
        return "; ".join(reasons[:3]).capitalize() + "."

    def move(row: pd.Series) -> str:
        path = str(row.get("milestone_path", ""))
        if row["motion"] == "Scale":
            if "omnichannel_adoption" not in path:
                return "Scale the acquisition pattern and add a second-channel trigger inside 45 days."
            return "Replicate this path with lookalike targeting and protect it with routine-building CRM."
        if row["motion"] == "Fix":
            if "category_expansion" not in path:
                return "Keep the path, but insert adjacent-category cross-sell after purchase two."
            if row["discount_reliance"] >= high_discount_q:
                return "Reduce discounting and replace it with bundle, sample, or exclusivity mechanics."
            return "Speed up purchase two with a timed welcome sequence and tighter replenishment cadence."
        if row["motion"] == "Stop":
            return "Stop scaling this path with paid pressure and avoid teaching discount-first behavior."
        return row.get("recommended_action", "Monitor the path and test one lever at a time.")

    def owner(row: pd.Series) -> str:
        action = move(row)
        if "second-channel" in action:
            return "CRM + Omnichannel"
        if "adjacent-category" in action:
            return "CRM + Category"
        if "discount" in action or "bundle" in action:
            return "CRM + Merchandising"
        return "CRM"

    def kpi(row: pd.Series) -> str:
        if row["motion"] == "Scale":
            return "Share of new customers entering this path"
        if row["motion"] == "Fix":
            return "Repeat rate and omnichannel adoption"
        if row["motion"] == "Stop":
            return "Budget share reduced on weak economics"
        return "12m value trend"

    variants["why_it_matters"] = variants.apply(reason, axis=1)
    variants["recommended_move"] = variants.apply(move, axis=1)
    variants["owner"] = variants.apply(owner, axis=1)
    variants["kpi"] = variants.apply(kpi, axis=1)
    variants["value_pool_eur"] = variants["customers"] * variants["avg_12m_value"]
    variants["path_display"] = variants["path_label"].map(lambda text: _shorten(text, 110))
    return variants.sort_values(["value_pool_eur", "customers"], ascending=[False, False])


def _cohort_actions(cohorts: pd.DataFrame) -> pd.DataFrame:
    if cohorts is None or cohorts.empty:
        return pd.DataFrame()

    df = cohorts.copy()
    robust = df[df["customers"] >= 100].copy()
    if robust.empty:
        robust = df.copy()

    high_value_q = robust["avg_12m_value"].quantile(0.75)
    low_value_q = robust["avg_12m_value"].quantile(0.25)
    margin_floor = robust["avg_margin_12m"].median()
    high_speed_cut = robust["median_days_to_second"].dropna().quantile(0.75) if robust["median_days_to_second"].notna().any() else 60
    low_hv_q = robust["high_value_rate"].quantile(0.25)

    df["decision"] = np.select(
        [
            (df["customers"] >= 100) & (df["avg_12m_value"] >= high_value_q) & (df["avg_margin_12m"] >= margin_floor),
            (df["discount_label"] == "Discounted") & (df["avg_margin_12m"] < margin_floor),
            df["median_days_to_second"].fillna(9999) >= high_speed_cut,
            (df["customers"] >= 100) & (df["avg_12m_value"] <= low_value_q) & (df["high_value_rate"] <= low_hv_q),
        ],
        ["Scale", "Fix economics", "Fix speed", "Stop scaling"],
        default="Monitor",
    )

    def play(row: pd.Series) -> str:
        if row["decision"] == "Scale":
            return "Increase budget and replicate the first 30-day onboarding sequence on lookalikes."
        if row["decision"] == "Fix economics":
            return "Keep the cohort but swap blanket discounts for bundles, samples, or exclusivity."
        if row["decision"] == "Fix speed":
            return "Add a purchase-two trigger within 30 days and shorten the welcome sequence."
        if row["decision"] == "Stop scaling":
            return "Reduce paid acquisition on this cohort until the economics improve."
        return "Hold budget steady and run controlled message tests."

    def why(row: pd.Series) -> str:
        if row["decision"] == "Scale":
            return "This cohort combines value, margin, and enough volume to matter."
        if row["decision"] == "Fix economics":
            return "Top-line value exists, but too much of it is bought through discounting."
        if row["decision"] == "Fix speed":
            return "The first basket is acceptable, but the path slows before a profitable habit forms."
        if row["decision"] == "Stop scaling":
            return "This cohort is not converting enough value to justify aggressive acquisition."
        return "The cohort is directionally interesting but not yet strong enough to scale."

    df["commercial_play"] = df.apply(play, axis=1)
    df["why_it_matters"] = df.apply(why, axis=1)
    df["owner"] = np.select(
        [
            df["decision"] == "Scale",
            df["decision"] == "Fix economics",
            df["decision"] == "Fix speed",
            df["decision"] == "Stop scaling",
        ],
        ["Acquisition + CRM", "Acquisition + Merchandising", "CRM", "Acquisition"],
        default="CRM + Analytics",
    )
    df["kpi"] = np.select(
        [
            df["decision"] == "Scale",
            df["decision"] == "Fix economics",
            df["decision"] == "Fix speed",
            df["decision"] == "Stop scaling",
        ],
        [
            "12m value per recruited customer",
            "Margin per recruited customer",
            "Second purchase within 30 days",
            "Budget reallocation efficiency",
        ],
        default="Incremental value from tests",
    )
    return df.sort_values(["estimated_value_pool", "customers"], ascending=[False, False])


def _transition_playbook(transitions: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    if transitions is None or transitions.empty:
        return pd.DataFrame()

    base = transitions.copy()
    base["anonymized_card_code"] = base["anonymized_card_code"].astype(str)
    enriched = base.merge(
        customers[["customer_id", "country_display", "first_category_display", "first_channel_display"]],
        left_on="anonymized_card_code",
        right_on="customer_id",
        how="left",
    )

    summary = (
        enriched.groupby(["transition", "transition_type"], dropna=False)
        .agg(
            customers=("anonymized_card_code", "nunique"),
            avg_delta_revenue=("delta_monthly_revenue", "mean"),
            avg_delta_categories=("delta_monthly_categories", "mean"),
            avg_delta_channels=("delta_monthly_channels", "mean"),
            avg_delta_discount=("delta_monthly_discount_ratio", "mean"),
            driver_summary=("driver_summary", _mode),
            focus_country=("country_display", _mode),
            focus_category=("first_category_display", _mode),
            focus_channel=("first_channel_display", _mode),
        )
        .reset_index()
    )
    summary = summary[summary["customers"] >= 100].copy()
    if summary.empty:
        return summary

    def action(row: pd.Series) -> str:
        if row["transition_type"] == "upgrade":
            if row["avg_delta_channels"] > 0:
                return "Industrialize second-channel adoption in similar cohorts."
            if row["avg_delta_categories"] > 0:
                return "Build adjacent-category routines and guided cross-sell."
            if row["avg_delta_discount"] > 0.05:
                return "Protect the gain but stop relying on rising promo intensity."
            return "Lock the upgrade with loyalty and replenishment CRM."
        if row["avg_delta_discount"] > 0.05:
            return "Repair promo dependence before the segment weakens further."
        if row["avg_delta_categories"] <= 0 and row["avg_delta_channels"] <= 0:
            return "Reopen breadth: add a new category or channel before the next visit window closes."
        return "Launch a save sequence now: reminder, routine, then selective offer."

    def owner(row: pd.Series) -> str:
        if row["avg_delta_channels"] > 0:
            return "CRM + Omnichannel"
        if row["avg_delta_categories"] > 0:
            return "CRM + Category"
        if row["avg_delta_discount"] > 0.05:
            return "CRM + Merchandising"
        if row["transition_type"] == "upgrade":
            return "CRM + Loyalty"
        return "CRM"

    def kpi(row: pd.Series) -> str:
        if row["transition_type"] == "upgrade":
            return "Share of customers completing the winning transition"
        if row["transition_type"] == "downgrade":
            return "Downgrade rate reduction"
        return "Stable share with higher value per customer"

    def next_14_days(row: pd.Series) -> str:
        if row["transition_type"] == "upgrade":
            return "Replicate the trigger in the next campaign cycle and protect the post-upgrade experience."
        return "Prioritize save journeys in the next 14 days before the customer slips further."

    summary["recommended_action"] = summary.apply(action, axis=1)
    summary["owner"] = summary.apply(owner, axis=1)
    summary["kpi"] = summary.apply(kpi, axis=1)
    summary["next_14_days"] = summary.apply(next_14_days, axis=1)
    summary["impact_eur"] = summary["customers"] * summary["avg_delta_revenue"].abs()
    summary["play_type"] = np.where(
        summary["transition_type"] == "upgrade",
        "Scale",
        np.where(summary["transition_type"] == "downgrade", "Repair", "Monitor"),
    )
    return summary.sort_values(["impact_eur", "customers"], ascending=[False, False])


def _action_audiences(customers: pd.DataFrame) -> dict[str, pd.DataFrame]:
    strong_cut = customers["value_12m_proxy"].quantile(0.75)
    protect = customers[
        (customers["value_12m_proxy"] >= strong_cut)
        & (customers["rfm_label"].isin(FRAGILE_SEGMENTS))
    ].copy()
    reactivate = customers[
        (customers["repeat_customer"] == 1)
        & customers["winning_path_score"].fillna(0).between(60, 80, inclusive="both")
        & customers["days_since_last"].between(60, 180, inclusive="both")
        & (~customers["rfm_label"].isin({"Lost", "Hibernating"}))
    ].copy()
    accelerate = customers[
        (customers["repeat_customer"] == 1)
        & (customers["is_omnichannel"] == 0)
        & (customers["days_to_second"].fillna(9999) <= 60)
        & (customers["rfm_label"].isin(GROWTH_SEGMENTS | HIGH_VALUE_SEGMENTS))
        & (customers["days_since_last"] <= 90)
    ].copy()
    depromo = customers[
        (customers["discount_ratio"] >= 0.30)
        & (customers["repeat_customer"] == 1)
        & (customers["winning_path_score"].fillna(0) >= 60)
    ].copy()
    return {
        "Protect premium drifters": protect,
        "Reactivate warm lapsed": reactivate,
        "Accelerate omnichannel growth": accelerate,
        "Recover margin leakage": depromo,
    }


def _priority_actions(customers: pd.DataFrame, cohort_actions: pd.DataFrame, audiences: dict[str, pd.DataFrame]) -> pd.DataFrame:
    growth = customers[
        (customers["repeat_customer"] == 1)
        & (customers["rfm_label"].isin(GROWTH_SEGMENTS | HIGH_VALUE_SEGMENTS))
    ].copy()
    omni_peer_delta = (
        growth.loc[growth["is_omnichannel"] == 1, "value_12m_proxy"].mean()
        - growth.loc[growth["is_omnichannel"] == 0, "value_12m_proxy"].mean()
    )

    profitable_repeaters = customers[
        (customers["repeat_customer"] == 1)
        & (customers["winning_path_score"].fillna(0) >= 60)
    ].copy()
    margin_gap = (
        profitable_repeaters.loc[profitable_repeaters["discount_ratio"] < 0.20, "margin_12m_proxy"].mean()
        - profitable_repeaters.loc[profitable_repeaters["discount_ratio"] >= 0.30, "margin_12m_proxy"].mean()
    )

    robust_cohorts = cohort_actions[
        (cohort_actions["customers"] >= 100)
        & (cohort_actions["decision"].isin(["Scale", "Fix economics", "Fix speed"]))
        & (cohort_actions["first_category_display"] != "Unknown")
        & (cohort_actions["channel_display"] != "Unknown")
    ]
    top_cohort = robust_cohorts.head(1)
    top_cohort_delta = (
        float(top_cohort["avg_12m_value"].iloc[0] - cohort_actions["avg_12m_value"].median())
        if not top_cohort.empty else np.nan
    )

    rows = []

    protect = audiences["Protect premium drifters"]
    rows.append(
        {
            "play": "Protect premium drifters",
            "audience": "High-value customers already sliding into fragile RFM states",
            "customers": int(len(protect)),
            "value_pool_eur": float(protect["value_12m_proxy"].sum()),
            "commercial_case": "Existing value is already proven here; saving even a small share beats buying equivalent value from scratch.",
            "trigger": "High-value customer enters Need Attention, At Risk, or Hibernating",
            "channel": "Email + Push + Clienteling",
            "offer_strategy": "Service-led reminder, samples, loyalty perk; no blanket discount first",
            "message_angle": "Protect the routine and the premium relationship",
            "recommended_move": "Launch a save sequence inside 7 days: replenishment, category reminder, then tier recognition.",
            "owner": "CRM + Loyalty",
            "kpi": "30-day reactivation and RFM recovery",
            "time_window": "Next 7 days",
            "priority_rank": 1,
        }
    )

    reactivate = audiences["Reactivate warm lapsed"]
    rows.append(
        {
            "play": "Reactivate warm lapsed",
            "audience": "Customers with decent path score but 60+ days of inactivity",
            "customers": int(len(reactivate)),
            "value_pool_eur": float(reactivate["value_12m_proxy"].sum()),
            "commercial_case": "This is the cheapest pool to win back before customers become truly lost.",
            "trigger": "Winning path score between 50 and 80 and no purchase for 60+ days",
            "channel": "Email + Push + Paid retargeting",
            "offer_strategy": "Value-led reminder first, selective incentive only after no engagement",
            "message_angle": "Rebuild the routine before the customer forgets it",
            "recommended_move": "Use a two-step win-back: editorial value first, offer second only if there is no click.",
            "owner": "CRM",
            "kpi": "30-day reactivation rate",
            "time_window": "Next 14 days",
            "priority_rank": 2,
        }
    )

    accelerate = audiences["Accelerate omnichannel growth"]
    rows.append(
        {
            "play": "Accelerate omnichannel growth",
            "audience": "Repeat customers in growth or high-value states who are still mono-channel",
            "customers": int(len(accelerate)),
            "value_pool_eur": float(accelerate["value_12m_proxy"].sum()),
            "commercial_case": f"Comparable omnichannel peers are worth about {_fmt_eur(omni_peer_delta)} more per customer.",
            "trigger": "Second purchase done within 60 days but customer still uses one channel only",
            "channel": "App inbox + Website personalization + Store receipt / advisor",
            "offer_strategy": "Convenience and exclusivity, not price cuts",
            "message_angle": "Show why the second channel makes the routine easier",
            "recommended_move": "Push store-to-app or app-to-store adoption in the 45 days after purchase two.",
            "owner": "CRM + Omnichannel",
            "kpi": "Omnichannel adoption within 45 days",
            "time_window": "Next 30 days",
            "priority_rank": 3,
        }
    )

    depromo = audiences["Recover margin leakage"]
    rows.append(
        {
            "play": "Recover margin leakage",
            "audience": "Repeat customers with upside still intact but discount reliance above 30%",
            "customers": int(len(depromo)),
            "value_pool_eur": float(depromo["margin_12m_proxy"].sum()),
            "commercial_case": f"Low-promo peers generate about {_fmt_eur(margin_gap)} more margin per customer.",
            "trigger": "Discount ratio above 30% with repeat behavior still present",
            "channel": "CRM + Merchandising",
            "offer_strategy": "Bundles, gifts, replenishment cues, exclusives",
            "message_angle": "Move the habit from price to routine and exclusivity",
            "recommended_move": "Replace blanket discounts with bundles, loyalty benefits, and replenishment-led offers.",
            "owner": "CRM + Merchandising",
            "kpi": "Margin per active customer",
            "time_window": "Next 30 days",
            "priority_rank": 4,
        }
    )

    if not top_cohort.empty:
        row = top_cohort.iloc[0]
        rows.append(
            {
                "play": "Scale the best acquisition seed",
                "audience": row["cohort_label"],
                "customers": int(row["customers"]),
                "value_pool_eur": float(row["estimated_value_pool"]),
                "commercial_case": f"This cohort is worth about {_fmt_eur(top_cohort_delta)} more than the median recruited cohort.",
                "trigger": "Budget reallocation and welcome-journey planning",
                "channel": "Acquisition + CRM onboarding",
                "offer_strategy": "Replicate the first-basket mix and the first 30-day welcome sequence",
                "message_angle": "Acquire more customers who start the right routine, not just more customers",
                "recommended_move": row["commercial_play"],
                "owner": row["owner"],
                "kpi": row["kpi"],
                "time_window": "Next budget cycle",
                "priority_rank": 5,
            }
        )

    actions = pd.DataFrame(rows)
    if actions.empty:
        return actions
    return actions.sort_values(["priority_rank", "value_pool_eur"], ascending=[True, False]).reset_index(drop=True)


def _crm_briefs(priority_actions: pd.DataFrame) -> pd.DataFrame:
    if priority_actions is None or priority_actions.empty:
        return pd.DataFrame()
    briefs = priority_actions.copy()
    briefs["value_pool"] = briefs["value_pool_eur"].map(_fmt_eur)
    return briefs[[
        "play",
        "audience",
        "trigger",
        "channel",
        "offer_strategy",
        "message_angle",
        "owner",
        "kpi",
        "time_window",
        "customers",
        "value_pool",
    ]]


def _operating_rules(
    variant_actions: pd.DataFrame,
    transition_playbook: pd.DataFrame,
    cohort_actions: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, str | int | float]] = []

    for _, row in transition_playbook.head(6).iterrows():
        rows.append(
            {
                "rule_type": "Transition",
                "signal": row["transition"],
                "priority": row["play_type"],
                "what_to_do": row["recommended_action"],
                "owner": row["owner"],
                "kpi": row["kpi"],
            }
        )

    for _, row in variant_actions[variant_actions["motion"].isin(["Scale", "Fix"])].head(6).iterrows():
        rows.append(
            {
                "rule_type": "Journey",
                "signal": row["journey_archetype"],
                "priority": row["motion"],
                "what_to_do": row["recommended_move"],
                "owner": row["owner"],
                "kpi": row["kpi"],
            }
        )

    for _, row in cohort_actions[cohort_actions["decision"].isin(["Scale", "Fix economics", "Fix speed"])].head(6).iterrows():
        rows.append(
            {
                "rule_type": "Acquisition",
                "signal": row["cohort_label"],
                "priority": row["decision"],
                "what_to_do": row["commercial_play"],
                "owner": row["owner"],
                "kpi": row["kpi"],
            }
        )

    return pd.DataFrame(rows)


def _timeline_value(km_by_channel: pd.DataFrame, column: str, day: int) -> float | None:
    if km_by_channel is None or km_by_channel.empty or column not in km_by_channel.columns:
        return None
    series = km_by_channel[["timeline", column]].dropna()
    if series.empty:
        return None
    idx = (series["timeline"] - day).abs().idxmin()
    return float(series.loc[idx, column])


def _evidence_points(
    customers: pd.DataFrame,
    feature_importance: pd.DataFrame | None,
    cox_summary: pd.DataFrame | None,
    km_by_channel: pd.DataFrame | None,
) -> list[dict[str, str]]:
    points: list[dict[str, str]] = []

    if feature_importance is not None and not feature_importance.empty:
        fi = feature_importance.set_index("feature")["importance"]
        speed_weight = float(fi.get("second_purchase_within_60d", 0.0) + fi.get("days_to_second", 0.0))
        points.append(
            {
                "label": "Early repeat speed",
                "headline": "Purchase-two timing is one of the clearest early signals of long-term value.",
                "body": f"The model allocates about {speed_weight * 100:.0f}% of total importance to repeat-speed features alone.",
            }
        )

    if cox_summary is not None and not cox_summary.empty:
        cox = cox_summary.set_index("covariate")
        if "n_categories" in cox.index:
            lift = float(cox.loc["n_categories", "exp(coef)"] - 1.0)
            points.append(
                {
                    "label": "Category depth",
                    "headline": "Category expansion is one of the strongest route-to-value mechanisms in the base.",
                    "body": f"Each additional category is associated with roughly {lift * 100:.0f}% higher event intensity in the survival model.",
                }
            )
        if "is_omnichannel" in cox.index:
            lift = float(cox.loc["is_omnichannel", "exp(coef)"] - 1.0)
            points.append(
                {
                    "label": "Omnichannel",
                    "headline": "Using more than one channel is a value accelerator, not just a descriptive trait.",
                    "body": f"Omnichannel behavior is associated with about {lift * 100:.0f}% higher event intensity in the survival model.",
                }
            )

    profitable_repeaters = customers[
        (customers["repeat_customer"] == 1)
        & (customers["winning_path_score"].fillna(0) >= 60)
    ]
    if not profitable_repeaters.empty:
        low_promo_margin = profitable_repeaters.loc[profitable_repeaters["discount_ratio"] < 0.20, "margin_12m_proxy"].mean()
        high_promo_margin = profitable_repeaters.loc[profitable_repeaters["discount_ratio"] >= 0.30, "margin_12m_proxy"].mean()
        margin_gap = low_promo_margin - high_promo_margin
        if not pd.isna(margin_gap):
            points.append(
                {
                    "label": "Promo leakage",
                    "headline": "Heavy discount reliance damages the quality of value, even when customers keep buying.",
                    "body": f"Among promising repeaters, lower-promo customers generate about {_fmt_eur(margin_gap)} more margin per customer.",
                }
            )

    store_90 = _timeline_value(km_by_channel, "store", 90)
    estore_90 = _timeline_value(km_by_channel, "estore", 90)
    if store_90 is not None and estore_90 is not None:
        gap = store_90 - estore_90
        winner = "store" if gap >= 0 else "estore"
        points.append(
            {
                "label": "Channel retention",
                "headline": f"The {winner} channel currently shows the better day-90 retention profile.",
                "body": f"The retention gap at roughly day 90 is about {abs(gap) * 100:.1f} points between store and estore.",
            }
        )

    return points[:4]


def _executive_story(
    priority_actions: pd.DataFrame,
    transition_playbook: pd.DataFrame,
    variant_actions: pd.DataFrame,
) -> dict[str, str]:
    top_action = priority_actions.iloc[0] if not priority_actions.empty else None

    downgrade = transition_playbook[transition_playbook["transition_type"] == "downgrade"].head(1)
    scale_path = variant_actions[variant_actions["motion"] == "Scale"].head(1)

    what_changed = "The base is moving, but not always in the right direction."
    if not downgrade.empty:
        row = downgrade.iloc[0]
        what_changed = f"The biggest destructive move right now is {row['transition']} with {int(row['customers']):,} customers exposed."

    why = "The economics are driven by speed to purchase two, category depth, and channel breadth."
    if not scale_path.empty:
        row = scale_path.iloc[0]
        why = f"The best scalable path converts at {_fmt_pct(row['high_value_rate'])} high-value rate with {_fmt_eur(row['avg_12m_value'])} average 12m value."

    who = "The most urgent audience is the one carrying proven value and early signs of erosion."
    action = "Prioritize one play at a time and turn it into an owned CRM or commercial motion."
    if top_action is not None:
        who = f"{top_action['audience']} ({int(top_action['customers']):,} customers)."
        action = top_action["recommended_move"]

    return {
        "What changed": what_changed,
        "Why": why,
        "Who is affected": who,
        "What we should do now": action,
    }


def _journey_filters(customers: pd.DataFrame) -> pd.DataFrame:
    with st.expander("Filter the slice", expanded=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        country = c1.multiselect("Country", sorted(customers["country_display"].dropna().unique()))
        channel = c2.multiselect("First channel", sorted(customers["first_channel_display"].dropna().unique()))
        category = c3.multiselect("First category", sorted(customers["first_category_display"].dropna().unique()))
        loyalty = c4.multiselect("Loyalty", sorted(customers["loyalty_label"].dropna().astype(str).unique()))
        rfm = c5.multiselect("RFM", sorted(customers["rfm_label"].dropna().astype(str).unique()))

        c6, c7, c8, c9 = st.columns(4)
        city = c6.multiselect("City", sorted(customers["city_display"].dropna().unique())[:300])
        age = c7.multiselect("Age", sorted(customers["age_display"].dropna().unique()))
        gender = c8.multiselect("Gender", sorted(customers["gender_display"].dropna().unique()))
        brand = c9.multiselect("First brand", sorted(customers["first_brand_display"].dropna().unique())[:200])

    mask = pd.Series(True, index=customers.index)
    filter_map = {
        "country_display": country,
        "first_channel_display": channel,
        "first_category_display": category,
        "loyalty_label": loyalty,
        "rfm_label": rfm,
        "city_display": city,
        "age_display": age,
        "gender_display": gender,
        "first_brand_display": brand,
    }
    for column, values in filter_map.items():
        if values:
            mask &= customers[column].astype(str).isin([str(value) for value in values])
    return customers.loc[mask].copy()


def _decision_card(slot, label: str, body: str) -> None:
    with slot:
        with st.container(border=True):
            st.caption(label)
            st.write(body)


def _retention_chart(retention_curves: pd.DataFrame) -> go.Figure:
    overall = retention_curves.groupby("days").agg(retained=("retained", "sum"), total=("total", "sum")).reset_index()
    overall["retention_rate"] = overall["retained"] / overall["total"]
    fig = px.line(
        overall,
        x="days",
        y="retention_rate",
        color_discrete_sequence=[GOLD],
        markers=True,
    )
    fig.update_traces(line_width=3)
    fig.update_layout(**PLOTLY_LAYOUT, yaxis_tickformat=".0%", height=340)
    return fig


def _bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    height: int = 420,
    horizontal: bool = False,
) -> go.Figure:
    fig = px.bar(
        df,
        x=x if not horizontal else y,
        y=y if not horizontal else x,
        color=color,
        orientation="h" if horizontal else "v",
        color_discrete_map={
            "upgrade": GREEN,
            "downgrade": RED,
            "stable": CHAMPAGNE,
            "Scale": GREEN,
            "Fix": GOLD,
            "Stop": RED,
            "Monitor": CHAMPAGNE,
        },
        color_discrete_sequence=[GOLD, CHAMPAGNE, GREEN, RED],
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=height, showlegend=color is not None)
    return fig


def _milestone_transition_tables(event_log: pd.DataFrame, customers: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if event_log is None or event_log.empty:
        return pd.DataFrame(), pd.DataFrame()

    event_view = event_log[event_log["concept:name"].isin(MILESTONE_EVENTS)].copy()
    if event_view.empty:
        return pd.DataFrame(), pd.DataFrame()

    event_view["case:concept:name"] = event_view["case:concept:name"].astype(str)
    event_view = (
        event_view.sort_values(["case:concept:name", "time:timestamp", "concept:name"])
        .drop_duplicates(["case:concept:name", "concept:name"], keep="first")
        .copy()
    )
    event_view["next_event"] = event_view.groupby("case:concept:name")["concept:name"].shift(-1)

    flow = (
        event_view.dropna(subset=["next_event"])
        .groupby(["concept:name", "next_event"], dropna=False)
        .agg(customers=("case:concept:name", "nunique"))
        .reset_index()
    )
    if flow.empty:
        return pd.DataFrame(), pd.DataFrame()

    source_totals = flow.groupby("concept:name")["customers"].sum().rename("source_total").reset_index()
    flow = flow.merge(source_totals, on="concept:name", how="left")
    flow["transition_rate"] = flow["customers"] / flow["source_total"].replace(0, np.nan)
    flow["source_label"] = flow["concept:name"].map(MILESTONE_LABELS).fillna(flow["concept:name"])
    flow["target_label"] = flow["next_event"].map(MILESTONE_LABELS).fillna(flow["next_event"])
    flow["source_stage"] = flow["concept:name"].map(MILESTONE_STAGE).fillna(0)
    flow["target_stage"] = flow["next_event"].map(MILESTONE_STAGE).fillna(flow["source_stage"] + 1)

    customer_view = customers[["customer_id", "value_12m_proxy", "high_value", "winning_path_score"]].copy()
    nodes = (
        event_view.merge(customer_view, left_on="case:concept:name", right_on="customer_id", how="left")
        .groupby("concept:name", dropna=False)
        .agg(
            customers=("case:concept:name", "nunique"),
            avg_12m_value=("value_12m_proxy", "mean"),
            high_value_rate=("high_value", "mean"),
            avg_path_score=("winning_path_score", "mean"),
        )
        .reset_index()
    )
    nodes["label"] = nodes["concept:name"].map(MILESTONE_LABELS).fillna(nodes["concept:name"])
    nodes["stage"] = nodes["concept:name"].map(MILESTONE_STAGE).fillna(0)
    nodes["value_rank"] = nodes["avg_12m_value"].rank(method="dense", ascending=True)
    return flow, nodes


def _journey_landscape_figure(flow: pd.DataFrame, nodes: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if flow.empty or nodes.empty:
        return fig

    flow_vis = (
        flow.sort_values(["concept:name", "customers"], ascending=[True, False])
        .groupby("concept:name", as_index=False, group_keys=False)
        .head(2)
        .sort_values("customers", ascending=False)
        .head(28)
        .copy()
    )
    if flow_vis.empty:
        flow_vis = flow.sort_values("customers", ascending=False).head(30).copy()

    node_keep = set(flow_vis["concept:name"]).union(set(flow_vis["next_event"]))
    nodes = nodes[nodes["concept:name"].isin(node_keep)].copy().sort_values(["stage", "avg_12m_value"])
    if nodes.empty:
        nodes = nodes.sort_values(["stage", "avg_12m_value"]).copy()

    stage_counts = nodes.groupby("stage").size().to_dict()
    stage_seen: dict[int, int] = {}
    positions: dict[str, tuple[float, float]] = {}
    for _, row in nodes.iterrows():
        stage = int(row["stage"])
        stage_seen[stage] = stage_seen.get(stage, 0) + 1
        idx = stage_seen[stage]
        denom = stage_counts[stage] + 1
        positions[str(row["concept:name"])] = (stage, idx / denom)

    max_count = max(float(flow_vis["customers"].max()), 1.0)
    for _, row in flow_vis.sort_values("customers").iterrows():
        source = str(row["concept:name"])
        target = str(row["next_event"])
        if source not in positions or target not in positions:
            continue
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        width = 1 + 8 * float(row["customers"]) / max_count
        color = f"rgba(182,138,58,{0.12 + 0.38 * float(row['transition_rate']):.3f})"
        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(color=color, width=width),
                hoverinfo="text",
                text=f"{MILESTONE_LABELS.get(source, source)} -> {MILESTONE_LABELS.get(target, target)}<br>"
                     f"Customers: {int(row['customers']):,}<br>"
                     f"Transition rate: {row['transition_rate'] * 100:.1f}%",
                showlegend=False,
            )
        )

    fig.add_trace(
        go.Scatter(
            x=[positions[str(name)][0] for name in nodes["concept:name"]],
            y=[positions[str(name)][1] for name in nodes["concept:name"]],
            mode="markers+text",
            text=nodes["label"],
            textposition="top center",
            marker=dict(
                size=np.sqrt(nodes["customers"].clip(lower=1)) * 2.2,
                color=nodes["high_value_rate"],
                colorscale=[[0.0, IVORY], [0.5, CHAMPAGNE], [1.0, GREEN]],
                line=dict(color=INK, width=1),
                colorbar=dict(title="HV rate", tickformat=".0%"),
                showscale=True,
            ),
            customdata=np.stack(
                [
                    nodes["customers"],
                    nodes["avg_12m_value"],
                    nodes["avg_path_score"].fillna(0.0),
                ],
                axis=1,
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Customers: %{customdata[0]:,.0f}<br>"
                "Avg 12m value: EUR %{customdata[1]:,.0f}<br>"
                "Avg path score: %{customdata[2]:.1f}<extra></extra>"
            ),
            showlegend=False,
        )
    )

    stage_names = {
        0: "Entry",
        1: "Repeat speed",
        2: "Behavior change",
        3: "Loyalty / RFM",
        4: "Upgrade zone",
        5: "Elite zone",
    }
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=560,
        xaxis=dict(
            tickmode="array",
            tickvals=list(stage_names.keys()),
            ticktext=list(stage_names.values()),
            title="Journey stage",
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(showticklabels=False, title="Milestone density", showgrid=False, zeroline=False),
    )
    return fig


def _transition_matrix_figure(flow: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if flow.empty:
        return fig
    top = (
        flow.sort_values(["concept:name", "customers"], ascending=[True, False])
        .groupby("concept:name", as_index=False, group_keys=False)
        .head(2)
        .sort_values("customers", ascending=False)
        .head(20)
        .copy()
    )
    if top.empty:
        top = flow.sort_values("customers", ascending=False).head(24).copy()
    pivot = (
        top.pivot_table(
            index="source_label",
            columns="target_label",
            values="transition_rate",
            aggfunc="max",
            fill_value=0.0,
        )
        .sort_index()
    )
    fig.add_trace(
        go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale=[[0.0, IVORY], [0.35, "#E7D7B4"], [0.7, CHAMPAGNE], [1.0, GOLD]],
            text=(pivot.values * 100).round(1),
            texttemplate="%{text}%",
            hovertemplate="From %{y}<br>To %{x}<br>Transition rate %{z:.1%}<extra></extra>",
        )
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=520, xaxis_tickangle=35, yaxis_title="")
    return fig


def _compressed_sankey(flow: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if flow.empty:
        return fig

    compact = (
        flow.sort_values(["concept:name", "customers"], ascending=[True, False])
        .groupby("concept:name", as_index=False, group_keys=False)
        .head(2)
        .sort_values(["source_stage", "target_stage", "customers"], ascending=[True, True, False])
        .head(18)
        .copy()
    )
    nodes = list(pd.unique(compact[["source_label", "target_label"]].values.ravel("K")))
    node_index = {node: idx for idx, node in enumerate(nodes)}
    fig = go.Figure(
        go.Sankey(
            arrangement="snap",
            node=dict(
                pad=20,
                thickness=18,
                line=dict(color="rgba(0,0,0,0.12)", width=0.8),
                label=nodes,
                color=[GOLD if i % 2 == 0 else CHAMPAGNE for i in range(len(nodes))],
            ),
            link=dict(
                source=[node_index[source] for source in compact["source_label"]],
                target=[node_index[target] for target in compact["target_label"]],
                value=compact["customers"].tolist(),
                color=["rgba(182,138,58,0.24)"] * len(compact),
                customdata=(compact["transition_rate"] * 100).round(1),
                hovertemplate="%{source.label} -> %{target.label}<br>Customers %{value:,.0f}<br>Rate %{customdata:.1f}%<extra></extra>",
            ),
        )
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=520)
    return fig


def _transition_waterfall(playbook: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if playbook is None or playbook.empty:
        return fig

    winners = playbook[playbook["transition_type"] == "upgrade"].nlargest(4, "impact_eur")
    losers = playbook[playbook["transition_type"] == "downgrade"].nlargest(4, "impact_eur")
    rows = []
    for _, row in winners.iterrows():
        rows.append((row["transition"], abs(float(row["avg_delta_revenue"])) * int(row["customers"]), "relative"))
    for _, row in losers.iterrows():
        rows.append((row["transition"], -abs(float(row["avg_delta_revenue"])) * int(row["customers"]), "relative"))
    if not rows:
        return fig

    labels = [label for label, _, _ in rows]
    values = [value for _, value, _ in rows]
    measures = [measure for _, _, measure in rows]
    colors = [GREEN if value >= 0 else RED for value in values]
    fig = go.Figure(
        go.Waterfall(
            x=labels,
            y=values,
            measure=measures,
            connector={"line": {"color": "rgba(111,98,85,0.35)"}},
            increasing={"marker": {"color": GREEN}},
            decreasing={"marker": {"color": RED}},
            totals={"marker": {"color": GOLD}},
        )
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=430, showlegend=False, xaxis_tickangle=25, yaxis_title="Revenue bridge")
    return fig


def _rfm_heatmap(matrix_rfm: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if matrix_rfm is None or matrix_rfm.empty:
        return fig

    index_order = [label for label in RFM_ORDER if label in matrix_rfm.index]
    column_order = [label for label in RFM_ORDER if label in matrix_rfm.columns]
    matrix = matrix_rfm.reindex(index=index_order, columns=column_order).fillna(0)
    row_sums = matrix.sum(axis=1).replace(0, 1)
    matrix_pct = matrix.div(row_sums, axis=0) * 100

    fig.add_trace(
        go.Heatmap(
            z=matrix_pct.values,
            x=matrix_pct.columns,
            y=matrix_pct.index,
            colorscale=[[0.0, IVORY], [0.35, "#E7D7B4"], [0.7, CHAMPAGNE], [1.0, GOLD]],
            text=matrix.values.astype(int),
            texttemplate="%{text}",
            hovertemplate="From %{y}<br>To %{x}<br>Rate %{z:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=520, xaxis_tickangle=45)
    return fig


def _metric_audit_table(
    customers: pd.DataFrame,
    audiences: dict[str, pd.DataFrame],
    transitions_rfm: pd.DataFrame,
) -> pd.DataFrame:
    latest_month = transitions_rfm["year_month_dt"].max()
    latest = transitions_rfm[transitions_rfm["year_month_dt"] == latest_month]
    growth = customers[
        (customers["repeat_customer"] == 1)
        & (customers["rfm_label"].isin(GROWTH_SEGMENTS | HIGH_VALUE_SEGMENTS))
    ]
    profitable_repeaters = customers[
        (customers["repeat_customer"] == 1)
        & (customers["winning_path_score"].fillna(0) >= 60)
    ]
    omni_peer_delta = (
        growth.loc[growth["is_omnichannel"] == 1, "value_12m_proxy"].mean()
        - growth.loc[growth["is_omnichannel"] == 0, "value_12m_proxy"].mean()
    )
    margin_gap = (
        profitable_repeaters.loc[profitable_repeaters["discount_ratio"] < 0.20, "margin_12m_proxy"].mean()
        - profitable_repeaters.loc[profitable_repeaters["discount_ratio"] >= 0.30, "margin_12m_proxy"].mean()
    )
    audit = pd.DataFrame(
        [
            {
                "metric": "Value at risk now",
                "value": _fmt_eur(audiences["Protect premium drifters"]["value_12m_proxy"].sum()),
                "formula": "Sum of 12m value proxy for top-quartile value customers already in fragile RFM states.",
                "sample": int(len(audiences["Protect premium drifters"])),
            },
            {
                "metric": "Warm reactivation pool",
                "value": _fmt_eur(audiences["Reactivate warm lapsed"]["value_12m_proxy"].sum()),
                "formula": "Sum of 12m value proxy for repeat customers with path score 60-80 and 60-180 days since last purchase.",
                "sample": int(len(audiences["Reactivate warm lapsed"])),
            },
            {
                "metric": "Omnichannel upside",
                "value": _fmt_eur(omni_peer_delta),
                "formula": "Difference in average 12m value between omnichannel and mono-channel customers among repeaters in growth/high-value states.",
                "sample": int(len(growth)),
            },
            {
                "metric": "Promo margin gap",
                "value": _fmt_eur(margin_gap),
                "formula": "Difference in average 12m margin between low-promo and high-promo promising repeaters with path score >= 60.",
                "sample": int(len(profitable_repeaters)),
            },
            {
                "metric": "Latest-month upgrades",
                "value": f"{int(latest['rfm_improved'].sum()):,}",
                "formula": "Sum of customer-month transitions flagged as RFM improvement in the latest observed month.",
                "sample": int(latest["anonymized_card_code"].nunique()),
            },
            {
                "metric": "Latest-month downgrades",
                "value": f"{int(latest['rfm_declined'].sum()):,}",
                "formula": "Sum of customer-month transitions flagged as RFM decline in the latest observed month.",
                "sample": int(latest["anonymized_card_code"].nunique()),
            },
        ]
    )
    return audit


def render_executive(data: dict[str, object]) -> None:
    customers: pd.DataFrame = data["customers"]  # type: ignore[assignment]
    audiences: dict[str, pd.DataFrame] = data["audiences"]  # type: ignore[assignment]
    priority_actions: pd.DataFrame = data["priority_actions"]  # type: ignore[assignment]
    journey_variants: pd.DataFrame = data["variant_actions"]  # type: ignore[assignment]
    transition_playbook: pd.DataFrame = data["transition_playbook"]  # type: ignore[assignment]
    cohorts: pd.DataFrame = data["cohort_actions"]  # type: ignore[assignment]
    retention_curves: pd.DataFrame = data["retention_curves"]  # type: ignore[assignment]
    evidence_points: list[dict[str, str]] = data["evidence_points"]  # type: ignore[assignment]
    story: dict[str, str] = data["executive_story"]  # type: ignore[assignment]
    metric_audit: pd.DataFrame = data["metric_audit"]  # type: ignore[assignment]

    protect = audiences["Protect premium drifters"]
    reactivate = audiences["Reactivate warm lapsed"]
    accelerate = audiences["Accelerate omnichannel growth"]
    depromo = audiences["Recover margin leakage"]

    growth = customers[
        (customers["repeat_customer"] == 1)
        & (customers["rfm_label"].isin(GROWTH_SEGMENTS | HIGH_VALUE_SEGMENTS))
    ]
    omni_peer_delta = (
        growth.loc[growth["is_omnichannel"] == 1, "value_12m_proxy"].mean()
        - growth.loc[growth["is_omnichannel"] == 0, "value_12m_proxy"].mean()
    )
    profitable_repeaters = customers[
        (customers["repeat_customer"] == 1)
        & (customers["winning_path_score"].fillna(0) >= 60)
    ]
    margin_gap = (
        profitable_repeaters.loc[profitable_repeaters["discount_ratio"] < 0.20, "margin_12m_proxy"].mean()
        - profitable_repeaters.loc[profitable_repeaters["discount_ratio"] >= 0.30, "margin_12m_proxy"].mean()
    )

    st.title("Winning Paths")
    st.markdown('<div class="body-copy">From customer history to profitable next moves.</div>', unsafe_allow_html=True)

    top_cards = st.columns(4)
    for column, (label, body) in zip(top_cards, story.items()):
        _decision_card(column, label, body)

    metrics = st.columns(4)
    metrics[0].metric("Value at risk now", _fmt_eur_short(protect["value_12m_proxy"].sum()), f"{len(protect):,} customers")
    metrics[1].metric("Warm reactivation pool", _fmt_eur_short(reactivate["value_12m_proxy"].sum()), f"{len(reactivate):,} customers")
    metrics[2].metric("Omnichannel upside", _fmt_eur_short(omni_peer_delta), "per comparable customer")
    metrics[3].metric("Promo margin gap", _fmt_eur_short(margin_gap), "per promising repeater")

    st.divider()
    st.subheader("What the data actually rewards")
    evidence_cols = st.columns(max(1, len(evidence_points)))
    for column, point in zip(evidence_cols, evidence_points):
        with column:
            with st.container(border=True):
                st.caption(point["label"])
                st.markdown(f"#### {point['headline']}")
                st.write(point["body"])

    st.divider()
    left, right = st.columns([1.1, 0.9])
    with left:
        st.subheader("Priority plays for the next 30 days")
        actions_view = priority_actions.copy()
        actions_view["value_pool_eur"] = actions_view["value_pool_eur"].map(_fmt_eur)
        st.dataframe(
            actions_view[[
                "play",
                "audience",
                "customers",
                "value_pool_eur",
                "recommended_move",
                "owner",
                "kpi",
                "time_window",
            ]].rename(columns={"value_pool_eur": "Value pool"}),
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "Download executive action plan",
            data=_to_csv_download(priority_actions),
            file_name="RD_executive_actions.csv",
            mime="text/csv",
        )

    with right:
        st.subheader("Value pools you can actually influence")
        focus_df = pd.DataFrame(
            {
                "play": [
                    "Protect premium drifters",
                    "Reactivate warm lapsed",
                    "Accelerate omnichannel growth",
                    "Recover margin leakage",
                ],
                "value_pool": [
                    float(protect["value_12m_proxy"].sum()),
                    float(reactivate["value_12m_proxy"].sum()),
                    float(accelerate["value_12m_proxy"].sum()),
                    float(depromo["margin_12m_proxy"].sum()),
                ],
            }
        ).sort_values("value_pool", ascending=True)
        fig = px.bar(
            focus_df,
            x="value_pool",
            y="play",
            orientation="h",
            color="play",
            color_discrete_sequence=[RED, GOLD, GREEN, CHAMPAGNE],
        )
        fig.update_layout(**PLOTLY_LAYOUT, height=340, showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    extra_left, extra_right = st.columns([1.1, 0.9])
    with extra_left:
        st.subheader("Transition impact bridge")
        st.plotly_chart(_transition_waterfall(transition_playbook), use_container_width=True, config=PLOTLY_CONFIG)
    with extra_right:
        st.subheader("Metric audit")
        st.dataframe(metric_audit, use_container_width=True, hide_index=True)

    lower_left, lower_right = st.columns([1.1, 0.9])
    with lower_left:
        st.subheader("Journeys worth scaling")
        scale_paths = journey_variants[journey_variants["motion"] == "Scale"].copy()
        if scale_paths.empty:
            scale_paths = journey_variants.head(10).copy()
        scale_paths = scale_paths.sort_values(["value_pool_eur", "customers"], ascending=[False, False]).head(12)
        scale_paths = scale_paths.sort_values("avg_12m_value", ascending=True)
        fig = px.bar(
            scale_paths,
            x="avg_12m_value",
            y="journey_archetype",
            orientation="h",
            color="high_value_rate",
            color_continuous_scale=["#E7D7B4", CHAMPAGNE, GOLD],
            hover_data={"customers": True, "path_display": True},
        )
        fig.update_layout(**PLOTLY_LAYOUT, height=420, coloraxis_colorbar_title="HV rate")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    with lower_right:
        st.subheader("Transitions creating the most damage")
        losing = transition_playbook[transition_playbook["transition_type"] == "downgrade"].head(10)
        if losing.empty:
            st.info("No meaningful downgrade transitions available.")
        else:
            fig = _bar_chart(
                losing.sort_values("impact_eur", ascending=True),
                x="impact_eur",
                y="transition",
                color="transition_type",
                horizontal=True,
                height=420,
            )
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    st.divider()
    c1, c2 = st.columns([1.1, 0.9])
    with c1:
        st.subheader("Best acquisition cohorts to scale")
        cohort_view = cohorts[cohorts["customers"] >= 100].head(12).copy()
        cohort_view["estimated_value_pool"] = cohort_view["estimated_value_pool"].map(_fmt_eur)
        st.dataframe(
            cohort_view[[
                "cohort_label",
                "decision",
                "customers",
                "avg_12m_value",
                "avg_margin_12m",
                "high_value_rate",
                "commercial_play",
                "owner",
            ]].rename(columns={"avg_12m_value": "Avg 12m value", "avg_margin_12m": "Avg margin 12m"}),
            use_container_width=True,
            hide_index=True,
        )

    with c2:
        st.subheader("Retention after first purchase")
        st.plotly_chart(_retention_chart(retention_curves), use_container_width=True, config=PLOTLY_CONFIG)


def render_journey_explorer(data: dict[str, object]) -> None:
    customers: pd.DataFrame = data["customers"]  # type: ignore[assignment]
    journey_paths: pd.DataFrame = data["journey_paths"]  # type: ignore[assignment]
    event_log: pd.DataFrame = data["event_log"]  # type: ignore[assignment]
    transitions_category: pd.DataFrame = data["transitions_category"]  # type: ignore[assignment]

    st.title("Journey Explorer")
    st.markdown(
        '<div class="body-copy">Use this screen to decide which journey families to scale, fix, suppress, or monitor.</div>',
        unsafe_allow_html=True,
    )

    filtered = _journey_filters(customers)
    if filtered.empty:
        st.warning("No customers match the selected filters.")
        return

    filtered_ids = set(filtered["customer_id"])
    journey_paths = journey_paths[journey_paths["anonymized_card_code"].astype(str).isin(filtered_ids)].copy()
    event_log = event_log[event_log["case:concept:name"].astype(str).isin(filtered_ids)].copy()

    variants = summarize_journey_variants(journey_paths)
    variants = _variant_actions(variants)
    variants = variants[variants["customers"] >= max(5, int(len(filtered) * 0.002))]
    flow, nodes = _milestone_transition_tables(event_log, filtered)

    slice_category_moves = _category_opportunities(
        transitions_category[transitions_category["anonymized_card_code"].astype(str).isin(filtered_ids)],
        filtered,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Customers in scope", f"{len(filtered):,}")
    c2.metric("Avg 12m value", _fmt_eur(filtered["value_12m_proxy"].mean()))
    c3.metric("High-value conversion", _fmt_pct(filtered["high_value"].mean()))
    c4.metric("Omnichannel adoption", _fmt_pct(filtered["is_omnichannel"].mean()))

    if variants.empty:
        st.info("No robust path variants in this slice.")
        return

    summary_cols = st.columns(4)
    motion_counts = variants["motion"].value_counts()
    summary_cols[0].metric("Scale paths", int(motion_counts.get("Scale", 0)))
    summary_cols[1].metric("Fix paths", int(motion_counts.get("Fix", 0)))
    summary_cols[2].metric("Stop paths", int(motion_counts.get("Stop", 0)))
    summary_cols[3].metric("Monitor paths", int(motion_counts.get("Monitor", 0)))

    left, right = st.columns([1.2, 0.8])
    with left:
        st.subheader("Journey landscape")
        viz_tabs = st.tabs(["Topology", "Transition matrix", "Compressed flow"])
        with viz_tabs[0]:
            st.plotly_chart(_journey_landscape_figure(flow, nodes), use_container_width=True, config=PLOTLY_CONFIG)
        with viz_tabs[1]:
            st.plotly_chart(_transition_matrix_figure(flow), use_container_width=True, config=PLOTLY_CONFIG)
        with viz_tabs[2]:
            st.plotly_chart(_compressed_sankey(flow), use_container_width=True, config=PLOTLY_CONFIG)

    with right:
        st.subheader("Variant economics")
        scatter = px.scatter(
            variants.head(40),
            x="avg_90d_value",
            y="avg_12m_value",
            size="customers",
            color="motion",
            hover_name="journey_archetype",
            hover_data={
                "path_display": True,
                "customers": True,
                "high_value_rate": ":.1%",
                "discount_reliance": ":.1%",
            },
            color_discrete_map={"Scale": GREEN, "Fix": GOLD, "Stop": RED, "Monitor": CHAMPAGNE},
        )
        scatter.update_layout(**PLOTLY_LAYOUT, height=560)
        st.plotly_chart(scatter, use_container_width=True, config=PLOTLY_CONFIG)

        if not nodes.empty:
            st.subheader("Milestone node economics")
            node_view = nodes.sort_values(["stage", "customers"], ascending=[True, False]).copy()
            node_view["avg_12m_value"] = node_view["avg_12m_value"].map(_fmt_eur)
            node_view["high_value_rate"] = node_view["high_value_rate"].map(_fmt_pct)
            node_view["avg_path_score"] = node_view["avg_path_score"].round(1)
            st.dataframe(
                node_view[["label", "customers", "avg_12m_value", "high_value_rate", "avg_path_score"]].rename(
                    columns={
                        "label": "Milestone",
                        "customers": "Customers",
                        "avg_12m_value": "Avg 12m value",
                        "high_value_rate": "HV rate",
                        "avg_path_score": "Avg path score",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

    st.divider()
    t1, t2 = st.columns([1.15, 0.85])
    with t1:
        st.subheader("Path variants you can act on")
        view = variants.copy()
        view["avg_90d_value"] = view["avg_90d_value"].map(_fmt_eur)
        view["avg_12m_value"] = view["avg_12m_value"].map(_fmt_eur)
        view["high_value_rate"] = view["high_value_rate"].map(_fmt_pct)
        view["repeat_rate"] = view["repeat_rate"].map(_fmt_pct)
        view["discount_reliance"] = view["discount_reliance"].map(_fmt_pct)
        st.dataframe(
            view[[
                "motion",
                "journey_archetype",
                "path_display",
                "customers",
                "high_value_rate",
                "avg_90d_value",
                "avg_12m_value",
                "discount_reliance",
                "why_it_matters",
                "recommended_move",
                "owner",
            ]].rename(columns={
                "motion": "Motion",
                "journey_archetype": "Archetype",
                "path_display": "Path",
                "high_value_rate": "HV conversion",
                "avg_90d_value": "Avg 90d value",
                "avg_12m_value": "Avg 12m value",
                "discount_reliance": "Discount reliance",
                "why_it_matters": "Why",
                "recommended_move": "Action",
                "owner": "Owner",
            }).head(25),
            use_container_width=True,
            hide_index=True,
        )

    with t2:
        st.subheader("Best category-expansion plays in this slice")
        if slice_category_moves.empty:
            st.info("No large enough category moves in this filtered slice.")
        else:
            move_view = slice_category_moves.head(10).copy()
            move_view["avg_12m_value"] = move_view["avg_12m_value"].map(_fmt_eur)
            move_view["high_value_rate"] = move_view["high_value_rate"].map(_fmt_pct)
            move_view["repeat_rate"] = move_view["repeat_rate"].map(_fmt_pct)
            st.dataframe(
                move_view[[
                    "from_category",
                    "to_category",
                    "customers",
                    "avg_12m_value",
                    "high_value_rate",
                    "repeat_rate",
                    "commercial_play",
                ]],
                use_container_width=True,
                hide_index=True,
            )

    best_scale = variants[variants["motion"] == "Scale"].head(1)
    worst_stop = variants[variants["motion"] == "Stop"].head(1)
    insight_cols = st.columns(2)
    if not best_scale.empty:
        row = best_scale.iloc[0]
        _decision_card(
            insight_cols[0],
            "Best move to scale in this slice",
            (
                f"{row['journey_archetype']} delivers {_fmt_eur(row['avg_12m_value'])} average 12m value with "
                f"{_fmt_pct(row['high_value_rate'])} high-value conversion. "
                f"Action: {row['recommended_move']}"
            ),
        )
    if not worst_stop.empty:
        row = worst_stop.iloc[0]
        _decision_card(
            insight_cols[1],
            "Most toxic path to suppress",
            (
                f"{row['journey_archetype']} stays weak despite scale pressure. "
                f"Why: {row['why_it_matters']} "
                f"Action: {row['recommended_move']}"
            ),
        )


def render_transition_engine(data: dict[str, object]) -> None:
    transitions: pd.DataFrame = data["transitions_rfm"]  # type: ignore[assignment]
    customers: pd.DataFrame = data["customers"]  # type: ignore[assignment]
    playbook: pd.DataFrame = data["transition_playbook"]  # type: ignore[assignment]
    matrix_rfm: pd.DataFrame = data["matrix_rfm"]  # type: ignore[assignment]
    category_moves: pd.DataFrame = data["category_moves"]  # type: ignore[assignment]

    st.title("Transition Engine")
    st.markdown(
        '<div class="body-copy">This screen turns state changes into a commercial playbook: what to scale, repair, or watch.</div>',
        unsafe_allow_html=True,
    )

    latest_month = transitions["year_month_dt"].max()
    latest = transitions[transitions["year_month_dt"] == latest_month]
    upgrades = int(latest["rfm_improved"].sum())
    downgrades = int(latest["rfm_declined"].sum())
    net_delta = float(latest["delta_monthly_revenue"].sum())
    vulnerable_value = float(customers.loc[customers["rfm_label"].isin(FRAGILE_SEGMENTS), "value_12m_proxy"].sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Latest-month upgrades", f"{upgrades:,}")
    c2.metric("Latest-month downgrades", f"{downgrades:,}")
    c3.metric("Net monthly revenue delta", _fmt_eur(net_delta))
    c4.metric("Value sitting in fragile states", _fmt_eur(vulnerable_value))

    top_damage = playbook[playbook["transition_type"] == "downgrade"].head(1)
    top_winner = playbook[playbook["transition_type"] == "upgrade"].head(1)
    summary_cols = st.columns(2)
    if not top_winner.empty:
        row = top_winner.iloc[0]
        _decision_card(
            summary_cols[0],
            "Transition to industrialize",
            f"{row['transition']} affects {int(row['customers']):,} customers. Action: {row['recommended_action']}",
        )
    if not top_damage.empty:
        row = top_damage.iloc[0]
        _decision_card(
            summary_cols[1],
            "Transition to stop",
            f"{row['transition']} is the sharpest downgrade pattern in scope. Action: {row['recommended_action']}",
        )

    left, right = st.columns([1.05, 0.95])
    with left:
        st.subheader("RFM migration heatmap")
        st.plotly_chart(_rfm_heatmap(matrix_rfm), use_container_width=True, config=PLOTLY_CONFIG)

    with right:
        transition_volume = (
            latest.groupby(["transition", "transition_type"])
            .size()
            .reset_index(name="customers")
            .sort_values("customers", ascending=False)
            .head(15)
            .sort_values("customers", ascending=True)
        )
        tech_tabs = st.tabs(["Volume", "Revenue bridge"])
        with tech_tabs[0]:
            st.subheader("Transitions shaping the latest month")
            st.plotly_chart(
                _bar_chart(transition_volume, x="customers", y="transition", color="transition_type", horizontal=True, height=480),
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )
        with tech_tabs[1]:
            st.subheader("Economic bridge of top transitions")
            st.plotly_chart(_transition_waterfall(playbook), use_container_width=True, config=PLOTLY_CONFIG)

    lower_left, lower_right = st.columns(2)
    with lower_left:
        st.subheader("Winning transitions to scale")
        winning = playbook[playbook["transition_type"] == "upgrade"].head(10).copy()
        winning["avg_delta_revenue"] = winning["avg_delta_revenue"].map(_fmt_eur)
        st.dataframe(
            winning[[
                "transition",
                "customers",
                "avg_delta_revenue",
                "focus_category",
                "driver_summary",
                "recommended_action",
                "owner",
            ]],
            use_container_width=True,
            hide_index=True,
        )

    with lower_right:
        st.subheader("Losing transitions to repair")
        losing = playbook[playbook["transition_type"] == "downgrade"].head(10).copy()
        losing["avg_delta_revenue"] = losing["avg_delta_revenue"].map(_fmt_eur)
        st.dataframe(
            losing[[
                "transition",
                "customers",
                "avg_delta_revenue",
                "focus_category",
                "driver_summary",
                "recommended_action",
                "owner",
            ]],
            use_container_width=True,
            hide_index=True,
        )

    st.divider()
    c1, c2 = st.columns([1.15, 0.85])
    with c1:
        st.subheader("Full transition playbook")
        playbook_view = playbook.copy()
        playbook_view["impact_eur"] = playbook_view["impact_eur"].map(_fmt_eur)
        playbook_view["avg_delta_revenue"] = playbook_view["avg_delta_revenue"].map(_fmt_eur)
        playbook_view["avg_delta_discount"] = playbook_view["avg_delta_discount"].round(3)
        st.dataframe(
            playbook_view[[
                "transition",
                "play_type",
                "customers",
                "impact_eur",
                "avg_delta_revenue",
                "driver_summary",
                "recommended_action",
                "owner",
                "kpi",
                "next_14_days",
            ]],
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "Download transition playbook",
            data=_to_csv_download(playbook),
            file_name="RD_transition_playbook.csv",
            mime="text/csv",
        )

    with c2:
        st.subheader("Category moves that support transition repair")
        if category_moves.empty:
            st.info("No large category transitions available.")
        else:
            move_view = category_moves.head(10).copy()
            move_view["avg_12m_value"] = move_view["avg_12m_value"].map(_fmt_eur)
            move_view["repeat_rate"] = move_view["repeat_rate"].map(_fmt_pct)
            st.dataframe(
                move_view[[
                    "from_category",
                    "to_category",
                    "customers",
                    "avg_12m_value",
                    "repeat_rate",
                    "commercial_play",
                ]],
                use_container_width=True,
                hide_index=True,
            )


def render_first_purchase_lab(data: dict[str, object]) -> None:
    cohorts: pd.DataFrame = data["cohort_actions"]  # type: ignore[assignment]
    customers: pd.DataFrame = data["customers"]  # type: ignore[assignment]

    st.title("First Purchase Lab")
    st.markdown(
        '<div class="body-copy">Choose the acquisition starts worth scaling, and separate them from the starts that create fake value or slow maturation.</div>',
        unsafe_allow_html=True,
    )

    min_customers = st.slider("Minimum cohort size", min_value=25, max_value=500, value=100, step=25)
    filtered = cohorts[cohorts["customers"] >= min_customers].copy()
    if filtered.empty:
        st.warning("No cohorts above the selected size threshold.")
        return

    decision_counts = filtered["decision"].value_counts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cohorts in scope", f"{len(filtered):,}")
    c2.metric("Scale now", int(decision_counts.get("Scale", 0)))
    c3.metric("Fix before scale", int(decision_counts.get("Fix economics", 0) + decision_counts.get("Fix speed", 0)))
    c4.metric("Stop scaling", int(decision_counts.get("Stop scaling", 0)))

    left, right = st.columns([1.05, 0.95])
    with left:
        bubble = px.scatter(
            filtered.head(80),
            x="avg_first_basket",
            y="avg_12m_value",
            size="customers",
            color="decision",
            hover_name="cohort_label",
            hover_data={"avg_margin_12m": True, "high_value_rate": True, "repeat_rate": True},
            color_discrete_map={
                "Scale": GREEN,
                "Fix economics": GOLD,
                "Fix speed": CHAMPAGNE,
                "Stop scaling": RED,
                "Monitor": TAUPE,
            },
        )
        bubble.update_layout(**PLOTLY_LAYOUT, height=520)
        st.subheader("Cohort economics map")
        st.plotly_chart(bubble, use_container_width=True, config=PLOTLY_CONFIG)

    with right:
        channel_perf = (
            customers.groupby("first_channel_display", dropna=False)
            .agg(
                customers=("customer_id", "nunique"),
                avg_12m_value=("value_12m_proxy", "mean"),
                repeat_rate=("repeat_customer", "mean"),
                high_value_rate=("high_value", "mean"),
            )
            .reset_index()
        )
        channel_perf = channel_perf[channel_perf["customers"] >= 200].sort_values("avg_12m_value", ascending=False).head(10)
        channel_perf["avg_12m_value"] = channel_perf["avg_12m_value"].map(_fmt_eur)
        channel_perf["repeat_rate"] = channel_perf["repeat_rate"].map(_fmt_pct)
        channel_perf["high_value_rate"] = channel_perf["high_value_rate"].map(_fmt_pct)
        st.subheader("First-channel benchmark")
        st.dataframe(channel_perf, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Acquisition decision table")
    view = filtered.copy()
    view["avg_first_basket"] = view["avg_first_basket"].map(_fmt_eur)
    view["avg_90d_value"] = view["avg_90d_value"].map(_fmt_eur)
    view["avg_12m_value"] = view["avg_12m_value"].map(_fmt_eur)
    view["avg_margin_12m"] = view["avg_margin_12m"].map(_fmt_eur)
    view["repeat_rate"] = view["repeat_rate"].map(_fmt_pct)
    view["high_value_rate"] = view["high_value_rate"].map(_fmt_pct)
    st.dataframe(
        view[[
            "cohort_label",
            "decision",
            "customers",
            "avg_first_basket",
            "avg_90d_value",
            "avg_12m_value",
            "avg_margin_12m",
            "high_value_rate",
            "commercial_play",
            "owner",
            "kpi",
        ]].head(25),
        use_container_width=True,
        hide_index=True,
    )

    top_scale = filtered[filtered["decision"] == "Scale"].head(1)
    if not top_scale.empty:
        row = top_scale.iloc[0]
        st.success(
            f"Best cohort to scale now: {row['cohort_label']} with {_fmt_eur(row['avg_12m_value'])} average 12m value. "
            f"Play: {row['commercial_play']}"
        )


def render_action_center(data: dict[str, object]) -> None:
    audiences: dict[str, pd.DataFrame] = data["audiences"]  # type: ignore[assignment]
    priority_actions: pd.DataFrame = data["priority_actions"]  # type: ignore[assignment]
    crm_briefs: pd.DataFrame = data["crm_briefs"]  # type: ignore[assignment]
    operating_rules: pd.DataFrame = data["operating_rules"]  # type: ignore[assignment]

    st.title("Action Center")
    st.markdown(
        '<div class="body-copy">This is the operating layer: who to target, what to say, what to offer, and how to measure success.</div>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs(["Prioritized plays", "CRM briefs", "Audience samples", "Operating rules"])

    with tab1:
        view = priority_actions.copy()
        view["value_pool_eur"] = view["value_pool_eur"].map(_fmt_eur)
        st.dataframe(
            view[[
                "play",
                "audience",
                "customers",
                "value_pool_eur",
                "commercial_case",
                "recommended_move",
                "owner",
                "kpi",
                "time_window",
            ]].rename(columns={"value_pool_eur": "Value pool"}),
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "Download action center plan",
            data=_to_csv_download(priority_actions),
            file_name="RD_action_center.csv",
            mime="text/csv",
        )

    with tab2:
        st.dataframe(crm_briefs, use_container_width=True, hide_index=True)
        st.download_button(
            "Download CRM briefs",
            data=_to_csv_download(crm_briefs),
            file_name="RD_crm_briefs.csv",
            mime="text/csv",
        )

    with tab3:
        audience_configs = [
            ("Protect premium drifters", ["customer_id", "country_display", "first_category_display", "value_12m_proxy", "rfm_label", "days_since_last"]),
            ("Reactivate warm lapsed", ["customer_id", "first_category_display", "winning_path_score", "value_12m_proxy", "risk_band", "days_since_last"]),
            ("Accelerate omnichannel growth", ["customer_id", "first_channel_display", "first_category_display", "value_12m_proxy", "days_to_second", "rfm_label"]),
            ("Recover margin leakage", ["customer_id", "first_category_display", "discount_ratio", "margin_12m_proxy", "winning_path_score", "rfm_label"]),
        ]
        inner_tabs = st.tabs([config[0] for config in audience_configs])
        for tab, (name, columns) in zip(inner_tabs, audience_configs):
            with tab:
                audience = audiences[name].sort_values(
                    ["value_12m_proxy", "margin_12m_proxy"] if "margin_12m_proxy" in audiences[name].columns else ["value_12m_proxy"],
                    ascending=False,
                ).head(50)
                st.metric("Audience size", f"{len(audience):,}")
                st.dataframe(audience[columns], use_container_width=True, hide_index=True)

    with tab4:
        st.dataframe(operating_rules, use_container_width=True, hide_index=True)
        st.download_button(
            "Download operating rules",
            data=_to_csv_download(operating_rules),
            file_name="RD_operating_rules.csv",
            mime="text/csv",
        )


def main() -> None:
    st.set_page_config(
        page_title="Winning Paths",
        page_icon="W",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _apply_base_style()
    data_store = load_store()
    if not data_store.is_ready:
        st.error("Data not prepared. Run `py -3 RD\\prepare_data.py` first.")
        return

    customers = _prepare_customers(data_store.customers, data_store.path_scores, data_store.anomalies)
    cohorts = _prepare_cohort_summary(data_store.first_purchase_cohort_summary)
    journey_paths = data_store.journey_paths.copy()
    journey_paths["anonymized_card_code"] = journey_paths["anonymized_card_code"].astype(str)

    variant_actions = _variant_actions(data_store.journey_variants)
    cohort_actions = _cohort_actions(cohorts)
    category_moves = _category_opportunities(data_store.transitions_category, customers)
    transition_playbook = _transition_playbook(data_store.transitions_rfm, customers)
    audiences = _action_audiences(customers)
    priority_actions = _priority_actions(customers, cohort_actions, audiences)
    crm_briefs = _crm_briefs(priority_actions)
    operating_rules = _operating_rules(variant_actions, transition_playbook, cohort_actions)
    evidence_points = _evidence_points(
        customers,
        data_store.feature_importance,
        data_store.cox_summary,
        data_store.km_by_channel,
    )
    executive_story = _executive_story(priority_actions, transition_playbook, variant_actions)
    metric_audit = _metric_audit_table(customers, audiences, data_store.transitions_rfm)

    data = {
        "customers": customers,
        "cohort_actions": cohort_actions,
        "journey_paths": journey_paths,
        "variant_actions": variant_actions,
        "event_log": data_store.event_log,
        "transitions_rfm": data_store.transitions_rfm,
        "transitions_loyalty": data_store.transitions_loyalty,
        "transitions_category": data_store.transitions_category,
        "matrix_rfm": data_store.matrix_rfm,
        "retention_curves": data_store.retention_curves,
        "transition_playbook": transition_playbook,
        "priority_actions": priority_actions,
        "crm_briefs": crm_briefs,
        "operating_rules": operating_rules,
        "audiences": audiences,
        "category_moves": category_moves,
        "evidence_points": evidence_points,
        "executive_story": executive_story,
        "metric_audit": metric_audit,
    }

    st.sidebar.title("Winning Paths")
    st.sidebar.caption("Native Streamlit cockpit for journey intelligence")
    page = st.sidebar.radio(
        "Navigation",
        [
            "Executive Overview",
            "Journey Explorer",
            "Transition Engine",
            "First Purchase Lab",
            "Action Center",
        ],
    )
    st.sidebar.markdown("---")
    st.sidebar.metric("Customers loaded", f"{len(customers):,}")
    st.sidebar.metric("Journey variants", f"{len(variant_actions):,}")
    st.sidebar.metric("RFM transitions", f"{len(data_store.transitions_rfm):,}")
    st.sidebar.metric("Priority plays", f"{len(priority_actions):,}")
    st.sidebar.caption("No custom front-end components. Only Streamlit-native layout and charts.")
    with st.sidebar.expander("Output pack", expanded=False):
        st.caption("Generate the figure, table, and deep-dive bundle under output/RD_product_pack.")
        if st.button("Generate product pack", use_container_width=True):
            from export_pack import export_product_pack

            exported = export_product_pack(data_store, data)
            st.success(
                f"Exported {len(exported['figures'])} figures, {len(exported['tables'])} tables, "
                f"and {len(exported['deepdives'])} deep-dive files to output/RD_product_pack."
            )

    if page == "Executive Overview":
        render_executive(data)
    elif page == "Journey Explorer":
        render_journey_explorer(data)
    elif page == "Transition Engine":
        render_transition_engine(data)
    elif page == "First Purchase Lab":
        render_first_purchase_lab(data)
    else:
        render_action_center(data)


if __name__ == "__main__":
    main()

