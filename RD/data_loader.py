"""Load precomputed data for the Winning Paths runtime."""

import pandas as pd
import pickle
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data" / "processed"


def _load(name: str) -> pd.DataFrame | None:
    path = DATA_DIR / f"{name}.parquet"
    if path.exists():
        return pd.read_parquet(path)
    return None


class DataStore:
    """Singleton that holds all precomputed tables."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def load(self):
        if self._loaded:
            return self
        print("Loading precomputed data ...")
        self.customers = _load("customers")
        self.tickets = _load("tickets")
        self.customer_month = _load("customer_month")
        self.first_purchase_cohorts = _load("first_purchase_cohorts")
        self.first_purchase_cohort_summary = _load("first_purchase_cohort_summary")
        self.event_log = _load("event_log")
        self.pm4py_variants = _load("pm4py_variants")
        self.pm4py_dfg = _load("pm4py_dfg")
        self.pm4py_start_activities = _load("pm4py_start_activities")
        self.pm4py_end_activities = _load("pm4py_end_activities")
        self.pm4py_quality = _load("pm4py_quality")
        self.journey_paths = _load("journey_paths")
        self.journey_variants = _load("journey_variants")
        self.transitions_rfm = _load("transitions_rfm")
        self.transitions_loyalty = _load("transitions_loyalty")
        self.transitions_category = _load("transitions_category")
        self.matrix_rfm = _load("matrix_rfm")
        if self.matrix_rfm is not None and "prev_rfm" in self.matrix_rfm.columns:
            self.matrix_rfm = self.matrix_rfm.set_index("prev_rfm")
        self.transition_values = _load("transition_values")
        self.journey_features = _load("journey_features")
        self.cluster_profiles = _load("cluster_profiles")
        self.cluster_diagnostics = _load("cluster_diagnostics")
        self.cluster_assignments_multi = _load("cluster_assignments_multi")
        self.cluster_profiles_multi = _load("cluster_profiles_multi")
        self.cluster_benchmark = _load("cluster_benchmark")
        self.path_scores = _load("path_scores")
        self.feature_importance = _load("feature_importance")
        self.model_metrics = _load("model_metrics")
        self.anomalies = _load("anomalies")
        self.time_series_monthly = _load("time_series_monthly")
        self.time_series_forecast = _load("time_series_forecast")
        self.time_series_signals = _load("time_series_signals")
        self.survival_km = _load("survival_km")
        self.retention_curves = _load("retention_curves")
        self.cox_summary = _load("cox_summary")
        self.km_by_channel = _load("km_by_channel")
        self.km_by_category = _load("km_by_category")

        # load model
        self.model = None
        for model_name in ["model_hv.pkl", "model_catboost.pkl", "model_xgb.pkl"]:
            model_path = DATA_DIR / model_name
            if model_path.exists():
                with open(model_path, "rb") as f:
                    self.model = pickle.load(f)
                break

        self._loaded = True
        available = sum(
            1 for key, value in vars(self).items()
            if not key.startswith("_") and value is not None
        )
        print(f"  {available} datasets loaded.")
        return self

    @property
    def is_ready(self):
        return self._loaded and self.customers is not None


# module-level convenience
store = DataStore()
