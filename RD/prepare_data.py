"""
Run once to process raw CSV into all analytical tables.
Usage: py -3 RD/prepare_data.py
"""

import sys
import time
from pathlib import Path

import pandas as pd

# Ensure the project root is on the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ml.anomaly import detect_anomalies
from ml.clustering import build_journey_features, run_advanced_clustering, run_clustering_suite
from ml.scoring import compute_winning_path_score, train_high_value_model
from ml.survival import compute_survival_data
from ml.timeseries import build_time_series_forecasts
from ml.process_mining import run_pm4py_process_mining
from pipeline.cohorts import build_first_purchase_cohorts, summarize_first_purchase_cohorts
from pipeline.customers import build_customer_profiles
from pipeline.events import build_event_log
from pipeline.loader import load_raw
from pipeline.monthly import build_customer_month
from pipeline.paths import build_journey_paths, summarize_journey_variants
from pipeline.transitions import (
    build_category_transitions,
    build_loyalty_transitions,
    build_rfm_transitions,
    build_transition_matrix,
    compute_transition_value,
)

OUT = Path(__file__).resolve().parent / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

CSV_PATH = Path(__file__).resolve().parent.parent / "BDD#7_Database_Albert_School_Sephora.csv"


def save(df: pd.DataFrame, name: str, index: bool = False) -> None:
    path = OUT / f"{name}.parquet"
    df.to_parquet(path, index=index)
    print(f"  saved {name}.parquet ({len(df):,} rows)")


def main() -> None:
    t0 = time.time()

    print("\n[1/8] Loading raw data ...")
    df = load_raw(CSV_PATH)
    print(f"  {df.shape[0]:,} rows x {df.shape[1]} columns loaded in {time.time() - t0:.1f}s")

    print("\n[2/8] Building customer profiles ...")
    customers, tickets = build_customer_profiles(df)
    save(customers, "customers")
    save(tickets, "tickets")
    print(f"  {customers.shape[0]:,} customers, {tickets.shape[0]:,} tickets")

    print("\n[3/8] Building monthly snapshots and cohort tables ...")
    customer_month = build_customer_month(df, customers)
    first_purchase_cohorts = build_first_purchase_cohorts(customers)
    first_purchase_summary = summarize_first_purchase_cohorts(first_purchase_cohorts)
    save(customer_month, "customer_month")
    save(first_purchase_cohorts, "first_purchase_cohorts")
    save(first_purchase_summary, "first_purchase_cohort_summary")

    print("\n[4/10] Building event log and journey paths ...")
    event_log = build_event_log(df, customers, tickets)
    journey_paths = build_journey_paths(event_log, customers)
    journey_variants = summarize_journey_variants(journey_paths)
    save(event_log, "event_log")
    save(journey_paths, "journey_paths")
    save(journey_variants, "journey_variants")

    print("\n[5/10] Running PM4Py process mining ...")
    pm4py_outputs = run_pm4py_process_mining(event_log)
    for name, frame in pm4py_outputs.items():
        if frame is not None and not frame.empty:
            save(frame, name)

    print("\n[6/10] Building transitions ...")
    transitions_rfm = build_rfm_transitions(customer_month)
    transitions_loyalty = build_loyalty_transitions(customer_month)
    transitions_category = build_category_transitions(tickets)
    matrix_rfm = build_transition_matrix(transitions_rfm, "prev_rfm", "rfm_label")
    transition_values = compute_transition_value(transitions_category, customers)

    save(transitions_rfm, "transitions_rfm")
    save(transitions_loyalty, "transitions_loyalty")
    save(transitions_category, "transitions_category")
    save(transition_values, "transition_values")
    save(matrix_rfm.reset_index(), "matrix_rfm")

    print("\n[7/10] Running journey clustering ...")
    journey_features = build_journey_features(customers, tickets)
    journey_features, cluster_profiles, cluster_diagnostics = run_advanced_clustering(
        journey_features,
        cluster_range=(4, 9),
        algorithm="kmeans",
    )
    save(journey_features, "journey_features")
    save(cluster_profiles, "cluster_profiles")
    save(cluster_diagnostics, "cluster_diagnostics")

    selected_k = int(cluster_diagnostics["selected_k"].dropna().max()) if not cluster_diagnostics.empty else 5
    cluster_assignments, cluster_profiles_multi, cluster_benchmark = run_clustering_suite(
        journey_features,
        kmeans_k=max(selected_k, 2),
        dbscan_min_samples=35,
    )
    save(cluster_assignments, "cluster_assignments_multi")
    save(cluster_profiles_multi, "cluster_profiles_multi")
    save(cluster_benchmark, "cluster_benchmark")

    print("\n[8/10] Computing scores, model artifacts, and anomalies ...")
    path_scores = compute_winning_path_score(journey_features, customers)
    save(path_scores, "path_scores")

    _, feature_importance, metrics = train_high_value_model(
        journey_features,
        customers,
        save_path=str(OUT / "model_hv.pkl"),
        preferred_model="catboost",
    )
    if feature_importance is not None:
        save(feature_importance, "feature_importance")
        print(f"  {metrics['model']} AUC = {metrics['auc']:.4f}")
    if metrics is not None:
        save(pd.DataFrame([{"model": metrics["model"], "auc": metrics["auc"]}]), "model_metrics")

    anomalies = detect_anomalies(journey_features, customers)
    save(anomalies, "anomalies")

    print("\n[9/10] Building time-series AI forecasts ...")
    ts_monthly, ts_forecast, ts_signals = build_time_series_forecasts(customer_month, periods=3)
    save(ts_monthly, "time_series_monthly")
    save(ts_forecast, "time_series_forecast")
    save(ts_signals, "time_series_signals")

    print("\n[10/10] Running survival analysis ...")
    survival = compute_survival_data(customers)

    if "km_second_purchase" in survival:
        save(survival["km_second_purchase"], "survival_km")
    if "retention_curves" in survival:
        save(survival["retention_curves"], "retention_curves")
    if "cox_summary" in survival and len(survival.get("cox_summary", [])) > 0:
        save(survival["cox_summary"], "cox_summary")

    for key in ["km_by_channel", "km_by_category"]:
        if key in survival:
            combined = []
            for label, curve in survival[key].items():
                curve = curve.copy()
                curve["group"] = label
                combined.append(curve)
            if combined:
                save(pd.concat(combined, ignore_index=True), key)

    elapsed = time.time() - t0
    print(f"\n{'=' * 60}")
    print(f"Data preparation complete in {elapsed:.0f}s")
    print(f"Output directory: {OUT}")
    files = sorted(OUT.glob('*.parquet'))
    print(f"Artifacts: {len(files)} parquet files plus optional model artifacts")
    for file in files:
        print(f"  {file.name}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

