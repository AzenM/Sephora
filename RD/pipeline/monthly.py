"""Build customer-month snapshot table."""

import numpy as np
import pandas as pd


def _safe_mode(series: pd.Series, default: str = "Unknown") -> str:
    values = series.dropna()
    if values.empty:
        return default
    modes = values.mode()
    return str(modes.iloc[0]) if not modes.empty else default


def build_customer_month(df: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    """Build one monthly snapshot per customer with temporal state labels."""

    base = df.copy()
    base["year_month"] = base["transactionDate"].dt.to_period("M")

    monthly = (
        base.groupby(["anonymized_card_code", "year_month"])
        .agg(
            monthly_revenue=("salesVatEUR", "sum"),
            monthly_discount=("discountEUR", "sum"),
            monthly_items=("quantity", "sum"),
            monthly_tickets=("anonymized_Ticket_ID", "nunique"),
            monthly_categories=("Axe_Desc", "nunique"),
            monthly_brands=("brand", "nunique"),
            monthly_channels=("channel_clean", "nunique"),
            main_channel=("channel_clean", _safe_mode),
            main_category=("Axe_Desc", _safe_mode),
            main_brand=("brand", _safe_mode),
            last_purchase_date=("transactionDate", "max"),
        )
        .reset_index()
    )

    latest_state = (
        base.sort_values(["anonymized_card_code", "year_month", "transactionDate", "anonymized_Ticket_ID"])
        .groupby(["anonymized_card_code", "year_month"])
        .tail(1)[[
            "anonymized_card_code",
            "year_month",
            "status",
            "loyalty_label",
            "RFM_Segment_ID",
            "rfm_label",
            "countryIsoCode",
            "age_category",
            "gender",
            "customer_city",
        ]]
    )

    monthly = monthly.merge(
        latest_state,
        on=["anonymized_card_code", "year_month"],
        how="left",
    )

    static_columns = [
        "anonymized_card_code",
        "Axe_Desc_first_purchase",
        "Market_Desc_first_purchase",
        "brand_first_purchase",
        "channel_recruitment",
        "first_date",
        "first_purchase_dt",
        "customer_city",
        "high_value",
    ]
    available = [column for column in static_columns if column in customers.columns]
    monthly = monthly.merge(
        customers[available].drop_duplicates("anonymized_card_code"),
        on="anonymized_card_code",
        how="left",
        suffixes=("", "_customer"),
    )

    if "customer_city_customer" in monthly.columns:
        monthly["customer_city"] = monthly["customer_city"].fillna(monthly["customer_city_customer"])
        monthly = monthly.drop(columns=["customer_city_customer"])

    monthly["monthly_discount_ratio"] = np.where(
        (monthly["monthly_revenue"] + monthly["monthly_discount"]) > 0,
        monthly["monthly_discount"] / (monthly["monthly_revenue"] + monthly["monthly_discount"]),
        0,
    )

    monthly["year_month_dt"] = monthly["year_month"].dt.to_timestamp()
    monthly = monthly.sort_values(["anonymized_card_code", "year_month_dt"]).reset_index(drop=True)

    for column in ["status", "loyalty_label", "RFM_Segment_ID", "rfm_label"]:
        monthly[column] = monthly.groupby("anonymized_card_code")[column].ffill().bfill()

    monthly["cum_revenue"] = monthly.groupby("anonymized_card_code")["monthly_revenue"].cumsum()
    monthly["cum_discount"] = monthly.groupby("anonymized_card_code")["monthly_discount"].cumsum()
    monthly["cum_tickets"] = monthly.groupby("anonymized_card_code")["monthly_tickets"].cumsum()
    monthly["month_number"] = monthly.groupby("anonymized_card_code").cumcount() + 1
    monthly["active_months"] = monthly.groupby("anonymized_card_code")["year_month"].transform("size")

    monthly["prev_month_purchase_date"] = monthly.groupby("anonymized_card_code")["last_purchase_date"].shift(1)
    monthly["days_since_prev_purchase"] = (
        monthly["last_purchase_date"] - monthly["prev_month_purchase_date"]
    ).dt.days
    monthly["days_since_first_purchase"] = (
        monthly["last_purchase_date"] - monthly["first_date"]
    ).dt.days

    return monthly
