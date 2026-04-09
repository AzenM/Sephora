"""Survival analysis — time-to-event modeling."""

import pandas as pd
import numpy as np

try:
    from lifelines import KaplanMeierFitter, CoxPHFitter
    HAS_LIFELINES = True
except ImportError:
    HAS_LIFELINES = False


def compute_survival_data(customers: pd.DataFrame) -> dict:
    """Compute survival curves and hazard ratios."""

    results = {}

    if not HAS_LIFELINES:
        print("lifelines not installed — using basic survival estimates")
        return _basic_survival(customers)

    # ================================================================
    # 1. Time to second purchase
    # ================================================================
    repeat = customers[customers["repeat_customer"] == 1].copy()
    non_repeat = customers[customers["repeat_customer"] == 0].copy()

    surv_df = pd.concat([
        repeat.assign(duration=repeat["days_to_second"], event=1),
        non_repeat.assign(duration=non_repeat["tenure_days"].clip(lower=1), event=0),
    ])
    surv_df = surv_df[surv_df["duration"] > 0]

    kmf = KaplanMeierFitter()
    kmf.fit(surv_df["duration"], surv_df["event"], label="All Customers")
    results["km_second_purchase"] = kmf.survival_function_.reset_index()
    results["median_time_to_second"] = kmf.median_survival_time_

    # By first channel
    km_by_channel = {}
    for ch in surv_df["channel_recruitment"].dropna().unique():
        mask = surv_df["channel_recruitment"] == ch
        if mask.sum() >= 30:
            kmf_ch = KaplanMeierFitter()
            kmf_ch.fit(surv_df.loc[mask, "duration"], surv_df.loc[mask, "event"], label=ch)
            km_by_channel[ch] = kmf_ch.survival_function_.reset_index()
    results["km_by_channel"] = km_by_channel

    # By first category
    km_by_cat = {}
    for cat in surv_df["Axe_Desc_first_purchase"].dropna().unique():
        mask = surv_df["Axe_Desc_first_purchase"] == cat
        if mask.sum() >= 30:
            kmf_cat = KaplanMeierFitter()
            kmf_cat.fit(surv_df.loc[mask, "duration"], surv_df.loc[mask, "event"], label=cat)
            km_by_cat[cat] = kmf_cat.survival_function_.reset_index()
    results["km_by_category"] = km_by_cat

    # ================================================================
    # 2. Cox PH model for second purchase hazard
    # ================================================================
    cox_df = surv_df[["duration", "event"]].copy()
    cox_df["is_omnichannel"] = customers.loc[surv_df.index, "is_omnichannel"].values
    cox_df["discount_ratio"] = customers.loc[surv_df.index, "discount_ratio"].values
    cox_df["first_basket_value"] = customers.loc[surv_df.index, "salesVatEUR_first_purchase"].fillna(0).values
    cox_df["n_categories"] = customers.loc[surv_df.index, "n_unique_categories"].values
    cox_df = cox_df.dropna()

    if len(cox_df) > 100:
        try:
            cph = CoxPHFitter()
            cph.fit(cox_df, duration_col="duration", event_col="event")
            results["cox_summary"] = cph.summary.reset_index()
            results["cox_concordance"] = cph.concordance_index_
        except Exception as e:
            print(f"Cox model failed: {e}")
            results["cox_summary"] = pd.DataFrame()

    # ================================================================
    # 3. Retention curves by cohort month
    # ================================================================
    cust = customers.copy()
    cust["cohort_month"] = cust["first_date"].dt.to_period("M")
    retention_data = []
    for cm, grp in cust.groupby("cohort_month"):
        total = len(grp)
        for days_cutoff in [30, 60, 90, 120, 180, 360]:
            survived = (grp["tenure_days"] >= days_cutoff).sum()
            retention_data.append({
                "cohort": str(cm),
                "days": days_cutoff,
                "retained": survived,
                "total": total,
                "retention_rate": survived / total if total > 0 else 0,
            })
    results["retention_curves"] = pd.DataFrame(retention_data)

    return results


def _basic_survival(customers: pd.DataFrame) -> dict:
    """Fallback survival estimates without lifelines."""
    results = {}

    repeat = customers[customers["repeat_customer"] == 1]
    results["median_time_to_second"] = repeat["days_to_second"].median()

    # retention curves
    cust = customers.copy()
    cust["cohort_month"] = cust["first_date"].dt.to_period("M")
    retention_data = []
    for cm, grp in cust.groupby("cohort_month"):
        total = len(grp)
        for days_cutoff in [30, 60, 90, 120, 180, 360]:
            survived = (grp["tenure_days"] >= days_cutoff).sum()
            retention_data.append({
                "cohort": str(cm),
                "days": days_cutoff,
                "retained": survived,
                "total": total,
                "retention_rate": survived / total if total > 0 else 0,
            })
    results["retention_curves"] = pd.DataFrame(retention_data)

    return results
