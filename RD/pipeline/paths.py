"""Build journey path tables from milestone events."""

import pandas as pd


PATH_SEPARATOR = " -> "

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
]


def _title_case_path(path: str) -> str:
    if not path:
        return "Unclassified Path"
    return PATH_SEPARATOR.join(part.replace("_", " ").title() for part in path.split(PATH_SEPARATOR))


def _recommended_action(row: pd.Series) -> str:
    path = row.get("milestone_path", "")

    if "second_purchase" not in path:
        return "Drive a fast second purchase with a timed welcome journey."
    if "omnichannel_adoption" not in path:
        return "Nudge a second channel adoption while intent is still warm."
    if "category_expansion" not in path:
        return "Recommend an adjacent category to widen the habit loop."
    if row.get("high_value_rate", 0) >= 0.30:
        return "Scale this journey with lookalike CRM targeting."
    if row.get("discount_reliance", 0) >= 0.25:
        return "Reduce promo pressure and test value-led creative."
    return "Protect the journey with replenishment and loyalty nudges."


def build_journey_paths(event_log: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    """Create one path record per customer from milestone events."""

    milestones = (
        event_log[event_log["concept:name"].isin(MILESTONE_EVENTS)]
        .sort_values(["case:concept:name", "time:timestamp", "concept:name"])
        .drop_duplicates(["case:concept:name", "concept:name"], keep="first")
        .copy()
    )

    path_table = (
        milestones.groupby("case:concept:name")
        .agg(
            milestone_path=("concept:name", lambda s: PATH_SEPARATOR.join(s.astype(str))),
            milestone_count=("concept:name", "size"),
            path_start=("time:timestamp", "min"),
            path_end=("time:timestamp", "max"),
        )
        .reset_index()
        .rename(columns={"case:concept:name": "anonymized_card_code"})
    )

    path_table["path_label"] = path_table["milestone_path"].map(_title_case_path)
    path_table["path_duration_days"] = (path_table["path_end"] - path_table["path_start"]).dt.days.fillna(0)

    customer_columns = customers[[
            "anonymized_card_code",
            "category_path",
            "channel_path",
            "brand_path",
            "revenue_90d",
            "value_12m_proxy",
            "margin_12m_proxy",
            "total_revenue",
            "discount_ratio",
            "repeat_customer",
            "high_value",
            "is_omnichannel",
            "days_to_second",
            "loyalty_label",
            "rfm_label",
            "n_tickets",
        ]].copy()
    customer_columns["anonymized_card_code"] = customer_columns["anonymized_card_code"].astype(str)

    return path_table.merge(
        customer_columns,
        on="anonymized_card_code",
        how="left",
    )


def summarize_journey_variants(journey_paths: pd.DataFrame) -> pd.DataFrame:
    """Aggregate customers into reusable path variants."""

    variants = (
        journey_paths.groupby(["milestone_path", "path_label"], dropna=False)
        .agg(
            customers=("anonymized_card_code", "count"),
            avg_milestones=("milestone_count", "mean"),
            avg_path_days=("path_duration_days", "mean"),
            avg_90d_value=("revenue_90d", "mean"),
            avg_12m_value=("value_12m_proxy", "mean"),
            avg_margin_12m=("margin_12m_proxy", "mean"),
            avg_total_revenue=("total_revenue", "mean"),
            repeat_rate=("repeat_customer", "mean"),
            high_value_rate=("high_value", "mean"),
            omnichannel_rate=("is_omnichannel", "mean"),
            avg_days_to_second=("days_to_second", "mean"),
            discount_reliance=("discount_ratio", "mean"),
        )
        .reset_index()
        .sort_values(["avg_12m_value", "customers"], ascending=[False, False])
    )

    variants["share_of_base"] = (
        variants["customers"] / variants["customers"].sum()
        if not variants.empty else 0.0
    )

    variants["recommended_action"] = variants.apply(_recommended_action, axis=1)
    variants["journey_archetype"] = variants["milestone_path"].apply(
        lambda path: (
            "Accelerated Winners" if "moved_to_rfm_1" in path else
            "Loyalty Climbers" if "gold_reached" in path or "silver_reached" in path else
            "Omnichannel Expanders" if "omnichannel_adoption" in path else
            "Single-Category Repeaters" if "category_expansion" not in path else
            "Developing Journeys"
        )
    )

    return variants
