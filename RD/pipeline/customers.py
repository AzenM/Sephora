"""Build customer-level profile and ticket tables."""

import numpy as np
import pandas as pd


PATH_SEPARATOR = " -> "


def _safe_mode(series: pd.Series, default: str = "Unknown") -> str:
    values = series.dropna()
    if values.empty:
        return default
    modes = values.mode()
    return str(modes.iloc[0]) if not modes.empty else default


def build_customer_profiles(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build one row per customer plus a visit-level ticket table."""

    base = df.copy()

    ticket = (
        base.groupby(["anonymized_card_code", "anonymized_Ticket_ID"])
        .agg(
            date=("transactionDate", "min"),
            revenue=("salesVatEUR", "sum"),
            discount=("discountEUR", "sum"),
            items=("quantity", "sum"),
            n_categories=("Axe_Desc", "nunique"),
            n_brands=("brand", "nunique"),
            main_cat=("Axe_Desc", _safe_mode),
            main_brand=("brand", _safe_mode),
            main_market=("Market_Desc", _safe_mode),
            channel=("channel_clean", _safe_mode),
            city=("store_city", _safe_mode),
            rfm_id=("RFM_Segment_ID", "last"),
            rfm_label=("rfm_label", _safe_mode),
            status=("status", "last"),
            loyalty_label=("loyalty_label", _safe_mode),
        )
        .reset_index()
        .sort_values(["anonymized_card_code", "date", "anonymized_Ticket_ID"])
    )
    ticket["visit_rank"] = ticket.groupby("anonymized_card_code").cumcount() + 1

    customer_diversity = (
        base.groupby("anonymized_card_code")
        .agg(
            n_unique_categories=("Axe_Desc", "nunique"),
            n_unique_brands=("brand", "nunique"),
            n_unique_channels=("channel_clean", "nunique"),
            n_unique_markets=("Market_Desc", "nunique"),
            n_unique_cities=("store_city", "nunique"),
        )
        .reset_index()
    )

    customers = (
        ticket.groupby("anonymized_card_code")
        .agg(
            total_revenue=("revenue", "sum"),
            total_discount=("discount", "sum"),
            total_items=("items", "sum"),
            n_tickets=("anonymized_Ticket_ID", "nunique"),
            first_date=("date", "min"),
            last_date=("date", "max"),
            avg_basket=("revenue", "mean"),
            median_basket=("revenue", "median"),
            max_basket=("revenue", "max"),
        )
        .reset_index()
        .merge(customer_diversity, on="anonymized_card_code", how="left")
    )

    customers["tenure_days"] = (customers["last_date"] - customers["first_date"]).dt.days.clip(lower=0)
    customers["avg_inter_purchase_days"] = np.where(
        customers["n_tickets"] > 1,
        customers["tenure_days"] / (customers["n_tickets"] - 1),
        np.nan,
    )
    customers["repeat_customer"] = (customers["n_tickets"] >= 2).astype(int)
    customers["discount_ratio"] = np.where(
        (customers["total_revenue"] + customers["total_discount"]) > 0,
        customers["total_discount"] / (customers["total_revenue"] + customers["total_discount"]),
        0,
    )
    customers["is_omnichannel"] = (customers["n_unique_channels"] >= 2).astype(int)

    first_attrs = (
        base.sort_values(["anonymized_card_code", "first_purchase_dt", "transactionDate"])
        .drop_duplicates("anonymized_card_code")
        [[
            "anonymized_card_code",
            "Axe_Desc_first_purchase",
            "Market_Desc_first_purchase",
            "brand_first_purchase",
            "channel_recruitment",
            "salesVatEUR_first_purchase",
            "discountEUR_first_purchase",
            "quantity_first_purchase",
            "first_purchase_dt",
            "countryIsoCode",
            "age_category",
            "age_generation",
            "gender",
            "customer_city",
        ]]
    )

    latest_state = (
        base.sort_values(["anonymized_card_code", "transactionDate", "anonymized_Ticket_ID"])
        .groupby("anonymized_card_code")
        .tail(1)[[
            "anonymized_card_code",
            "status",
            "RFM_Segment_ID",
            "loyalty_label",
            "rfm_label",
        ]]
    )

    customers = customers.merge(first_attrs, on="anonymized_card_code", how="left")
    customers = customers.merge(latest_state, on="anonymized_card_code", how="left")

    second_visit = ticket.loc[ticket["visit_rank"] == 2, ["anonymized_card_code", "date"]].rename(
        columns={"date": "second_date"}
    )
    customers = customers.merge(second_visit, on="anonymized_card_code", how="left")
    customers["days_to_second"] = (customers["second_date"] - customers["first_date"]).dt.days

    ticket_with_first = ticket.merge(
        customers[["anonymized_card_code", "first_date"]],
        on="anonymized_card_code",
        how="left",
    )
    ticket_with_first["day_offset"] = (
        ticket_with_first["date"] - ticket_with_first["first_date"]
    ).dt.days

    revenue_90d = (
        ticket_with_first.loc[ticket_with_first["day_offset"] <= 90]
        .groupby("anonymized_card_code")["revenue"]
        .sum()
        .rename("revenue_90d")
    )
    revenue_365d = (
        ticket_with_first.loc[ticket_with_first["day_offset"] <= 365]
        .groupby("anonymized_card_code")["revenue"]
        .sum()
        .rename("revenue_365d")
    )
    discount_365d = (
        ticket_with_first.loc[ticket_with_first["day_offset"] <= 365]
        .groupby("anonymized_card_code")["discount"]
        .sum()
        .rename("discount_365d")
    )
    customers = customers.merge(revenue_90d, on="anonymized_card_code", how="left")
    customers = customers.merge(revenue_365d, on="anonymized_card_code", how="left")
    customers = customers.merge(discount_365d, on="anonymized_card_code", how="left")
    for column in ["revenue_90d", "revenue_365d", "discount_365d"]:
        customers[column] = customers[column].fillna(0)

    repeat = customers[customers["repeat_customer"] == 1]
    threshold = repeat["total_revenue"].quantile(0.80) if not repeat.empty else customers["total_revenue"].quantile(0.80)
    customers["high_value"] = (
        (customers["repeat_customer"] == 1) &
        (customers["total_revenue"] >= threshold)
    ).astype(int)

    category_path = (
        ticket.loc[ticket["visit_rank"] <= 5]
        .groupby("anonymized_card_code")["main_cat"]
        .apply(lambda x: PATH_SEPARATOR.join(x.astype(str)))
        .rename("category_path")
    )
    channel_path = (
        ticket.loc[ticket["visit_rank"] <= 5]
        .groupby("anonymized_card_code")["channel"]
        .apply(lambda x: PATH_SEPARATOR.join(x.astype(str)))
        .rename("channel_path")
    )
    brand_path = (
        ticket.loc[ticket["visit_rank"] <= 5]
        .groupby("anonymized_card_code")["main_brand"]
        .apply(lambda x: PATH_SEPARATOR.join(x.astype(str)))
        .rename("brand_path")
    )

    customers = customers.merge(category_path, on="anonymized_card_code", how="left")
    customers = customers.merge(channel_path, on="anonymized_card_code", how="left")
    customers = customers.merge(brand_path, on="anonymized_card_code", how="left")
    customers["value_12m_proxy"] = customers["revenue_365d"]
    customers["margin_12m_proxy"] = (customers["revenue_365d"] - customers["discount_365d"]).clip(lower=0)
    customers["first_purchase_discounted"] = (customers["discountEUR_first_purchase"].fillna(0) > 0).astype(int)

    return customers, ticket
