"""Build state transition tables (RFM, loyalty, category)."""

import numpy as np
import pandas as pd


LOYALTY_RANK = {"No Loyalty": 0, "Bronze": 1, "Silver": 2, "Gold": 3}
PATH_SEPARATOR = " -> "


def _describe_transition(row: pd.Series) -> str:
    drivers = []

    if row.get("delta_monthly_categories", 0) > 0:
        drivers.append("category expansion")
    if row.get("delta_monthly_channels", 0) > 0:
        drivers.append("channel expansion")
    if row.get("delta_monthly_revenue", 0) > 0:
        drivers.append("revenue lift")
    if row.get("delta_monthly_tickets", 0) > 0:
        drivers.append("visit frequency lift")
    if row.get("delta_monthly_discount_ratio", 0) >= 0.10:
        drivers.append("promo intensity up")
    if row.get("delta_monthly_discount_ratio", 0) <= -0.10:
        drivers.append("promo reliance down")

    if not drivers:
        return "state changed with limited observable behavioral shift"
    return ", ".join(drivers[:3])


def build_rfm_transitions(monthly: pd.DataFrame) -> pd.DataFrame:
    """Month-over-month RFM segment transitions from temporal monthly states."""

    base = monthly.sort_values(["anonymized_card_code", "year_month_dt"]).copy()
    shift_columns = [
        "rfm_label",
        "RFM_Segment_ID",
        "monthly_revenue",
        "monthly_tickets",
        "monthly_categories",
        "monthly_channels",
        "monthly_discount_ratio",
        "main_channel",
        "main_category",
    ]
    shifted = base.groupby("anonymized_card_code")[shift_columns].shift(1)
    shifted.columns = [
        "prev_rfm",
        "prev_rfm_id",
        "prev_monthly_revenue",
        "prev_monthly_tickets",
        "prev_monthly_categories",
        "prev_monthly_channels",
        "prev_monthly_discount_ratio",
        "prev_main_channel",
        "prev_main_category",
    ]
    base = pd.concat([base, shifted], axis=1)

    trans = base.dropna(subset=["prev_rfm", "rfm_label"]).copy()
    trans["transition"] = trans["prev_rfm"].astype(str) + PATH_SEPARATOR + trans["rfm_label"].astype(str)
    trans["rfm_improved"] = (trans["RFM_Segment_ID"] < trans["prev_rfm_id"]).astype(int)
    trans["rfm_declined"] = (trans["RFM_Segment_ID"] > trans["prev_rfm_id"]).astype(int)
    trans["movement_size"] = (trans["prev_rfm_id"] - trans["RFM_Segment_ID"]).abs()
    trans["transition_type"] = np.select(
        [trans["rfm_improved"] == 1, trans["rfm_declined"] == 1],
        ["upgrade", "downgrade"],
        default="stable",
    )
    trans["delta_monthly_revenue"] = trans["monthly_revenue"] - trans["prev_monthly_revenue"]
    trans["delta_monthly_tickets"] = trans["monthly_tickets"] - trans["prev_monthly_tickets"]
    trans["delta_monthly_categories"] = trans["monthly_categories"] - trans["prev_monthly_categories"]
    trans["delta_monthly_channels"] = trans["monthly_channels"] - trans["prev_monthly_channels"]
    trans["delta_monthly_discount_ratio"] = (
        trans["monthly_discount_ratio"] - trans["prev_monthly_discount_ratio"]
    )
    trans["driver_summary"] = trans.apply(_describe_transition, axis=1)

    return trans[[
        "anonymized_card_code",
        "year_month_dt",
        "prev_rfm",
        "rfm_label",
        "prev_rfm_id",
        "RFM_Segment_ID",
        "transition",
        "transition_type",
        "movement_size",
        "rfm_improved",
        "rfm_declined",
        "monthly_revenue",
        "prev_monthly_revenue",
        "delta_monthly_revenue",
        "monthly_tickets",
        "delta_monthly_tickets",
        "delta_monthly_categories",
        "delta_monthly_channels",
        "delta_monthly_discount_ratio",
        "main_channel",
        "main_category",
        "prev_main_channel",
        "prev_main_category",
        "driver_summary",
    ]]


def build_loyalty_transitions(monthly: pd.DataFrame) -> pd.DataFrame:
    """Month-over-month loyalty transitions from temporal monthly states."""

    base = monthly.sort_values(["anonymized_card_code", "year_month_dt"]).copy()
    shifted = base.groupby("anonymized_card_code")[[
        "loyalty_label",
        "monthly_revenue",
        "monthly_tickets",
        "monthly_discount_ratio",
    ]].shift(1)
    shifted.columns = [
        "prev_loyalty",
        "prev_monthly_revenue",
        "prev_monthly_tickets",
        "prev_monthly_discount_ratio",
    ]
    base = pd.concat([base, shifted], axis=1)

    trans = base.dropna(subset=["prev_loyalty", "loyalty_label"]).copy()
    trans["loyalty_transition"] = trans["prev_loyalty"].astype(str) + PATH_SEPARATOR + trans["loyalty_label"].astype(str)
    trans["prev_loyalty_rank"] = trans["prev_loyalty"].map(LOYALTY_RANK).fillna(0)
    trans["loyalty_rank"] = trans["loyalty_label"].map(LOYALTY_RANK).fillna(0)
    trans["loyalty_improved"] = (trans["loyalty_rank"] > trans["prev_loyalty_rank"]).astype(int)
    trans["loyalty_declined"] = (trans["loyalty_rank"] < trans["prev_loyalty_rank"]).astype(int)
    trans["transition_type"] = np.select(
        [trans["loyalty_improved"] == 1, trans["loyalty_declined"] == 1],
        ["upgrade", "downgrade"],
        default="stable",
    )
    trans["delta_monthly_revenue"] = trans["monthly_revenue"] - trans["prev_monthly_revenue"]
    trans["delta_monthly_tickets"] = trans["monthly_tickets"] - trans["prev_monthly_tickets"]
    trans["delta_monthly_discount_ratio"] = (
        trans["monthly_discount_ratio"] - trans["prev_monthly_discount_ratio"]
    )

    return trans[[
        "anonymized_card_code",
        "year_month_dt",
        "prev_loyalty",
        "loyalty_label",
        "loyalty_transition",
        "transition_type",
        "loyalty_improved",
        "loyalty_declined",
        "monthly_revenue",
        "delta_monthly_revenue",
        "delta_monthly_tickets",
        "delta_monthly_discount_ratio",
    ]]


def build_category_transitions(ticket: pd.DataFrame) -> pd.DataFrame:
    """Visit-over-visit category and channel transitions."""

    base = ticket.sort_values(["anonymized_card_code", "date", "visit_rank"]).copy()
    shifted = base.groupby("anonymized_card_code")[["main_cat", "channel", "date"]].shift(1)
    shifted.columns = ["prev_cat", "prev_channel", "prev_date"]
    base = pd.concat([base, shifted], axis=1)

    trans = base.dropna(subset=["prev_cat"]).copy()
    trans["cat_transition"] = trans["prev_cat"].astype(str) + PATH_SEPARATOR + trans["main_cat"].astype(str)
    trans["cat_changed"] = (trans["prev_cat"] != trans["main_cat"]).astype(int)
    trans["channel_changed"] = (trans["prev_channel"] != trans["channel"]).astype(int)
    trans["days_between_visits"] = (trans["date"] - trans["prev_date"]).dt.days

    return trans[[
        "anonymized_card_code",
        "date",
        "prev_date",
        "prev_cat",
        "main_cat",
        "cat_transition",
        "cat_changed",
        "prev_channel",
        "channel",
        "channel_changed",
        "days_between_visits",
        "revenue",
        "visit_rank",
    ]]


def build_transition_matrix(transitions: pd.DataFrame, from_col: str, to_col: str) -> pd.DataFrame:
    """Pivot a transition table into a matrix."""

    matrix = transitions.groupby([from_col, to_col]).size().reset_index(name="count")
    return matrix.pivot_table(index=from_col, columns=to_col, values="count", fill_value=0)


def compute_transition_value(cat_transitions: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    """Compute value outcomes by category transition pair."""

    merged = cat_transitions.merge(
        customers[[
            "anonymized_card_code",
            "total_revenue",
            "revenue_90d",
            "value_12m_proxy",
            "high_value",
            "repeat_customer",
        ]],
        on="anonymized_card_code",
        how="left",
    )

    return (
        merged.groupby("cat_transition")
        .agg(
            count=("anonymized_card_code", "size"),
            avg_ltv=("total_revenue", "mean"),
            avg_90d_value=("revenue_90d", "mean"),
            avg_12m_value=("value_12m_proxy", "mean"),
            hv_rate=("high_value", "mean"),
            repeat_rate=("repeat_customer", "mean"),
            avg_basket=("revenue", "mean"),
            avg_days_between=("days_between_visits", "mean"),
        )
        .reset_index()
        .sort_values(["avg_12m_value", "count"], ascending=[False, False])
    )
