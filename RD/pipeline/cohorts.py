"""Build first-purchase cohort tables."""

import pandas as pd


def build_first_purchase_cohorts(customers: pd.DataFrame) -> pd.DataFrame:
    """Customer-level first-purchase cohort table."""

    cohorts = customers[[
        "anonymized_card_code",
        "first_date",
        "first_purchase_dt",
        "countryIsoCode",
        "customer_city",
        "age_category",
        "age_generation",
        "gender",
        "Axe_Desc_first_purchase",
        "Market_Desc_first_purchase",
        "brand_first_purchase",
        "channel_recruitment",
        "salesVatEUR_first_purchase",
        "discountEUR_first_purchase",
        "quantity_first_purchase",
        "first_purchase_discounted",
        "revenue_90d",
        "value_12m_proxy",
        "margin_12m_proxy",
        "total_revenue",
        "repeat_customer",
        "days_to_second",
        "high_value",
        "is_omnichannel",
        "loyalty_label",
        "rfm_label",
    ]].copy()

    cohorts["first_purchase_month"] = cohorts["first_date"].dt.to_period("M").astype(str)
    cohorts["first_basket_band"] = pd.cut(
        cohorts["salesVatEUR_first_purchase"].fillna(0),
        bins=[-1, 25, 50, 100, 200, 500, float("inf")],
        labels=["0-25", "25-50", "50-100", "100-200", "200-500", "500+"],
    ).astype(str)
    cohorts["first_discount_band"] = pd.cut(
        cohorts["discountEUR_first_purchase"].fillna(0),
        bins=[-1, 0, 5, 15, 30, float("inf")],
        labels=["0", "0-5", "5-15", "15-30", "30+"],
    ).astype(str)
    cohorts["cohort_key"] = (
        cohorts["Axe_Desc_first_purchase"].fillna("Unknown") + " | " +
        cohorts["channel_recruitment"].fillna("Unknown") + " | " +
        cohorts["first_purchase_discounted"].map({0: "Full Price", 1: "Discounted"})
    )

    return cohorts


def summarize_first_purchase_cohorts(cohorts: pd.DataFrame) -> pd.DataFrame:
    """Aggregated first-purchase cohort performance table."""

    summary = (
        cohorts.groupby([
            "Axe_Desc_first_purchase",
            "channel_recruitment",
            "first_purchase_discounted",
        ], dropna=False)
        .agg(
            customers=("anonymized_card_code", "count"),
            avg_first_basket=("salesVatEUR_first_purchase", "mean"),
            avg_90d_value=("revenue_90d", "mean"),
            avg_12m_value=("value_12m_proxy", "mean"),
            avg_margin_12m=("margin_12m_proxy", "mean"),
            repeat_rate=("repeat_customer", "mean"),
            high_value_rate=("high_value", "mean"),
            omnichannel_rate=("is_omnichannel", "mean"),
            median_days_to_second=("days_to_second", "median"),
        )
        .reset_index()
        .sort_values(["avg_12m_value", "customers"], ascending=[False, False])
    )

    summary["discount_label"] = summary["first_purchase_discounted"].map({0: "Full Price", 1: "Discounted"})
    return summary
