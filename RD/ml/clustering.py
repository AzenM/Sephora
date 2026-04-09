"""Journey clustering — data-driven customer archetypes."""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.mixture import GaussianMixture
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import silhouette_score


ARCHETYPE_NAMES = {
    0: "Premium Loyalists",
    1: "Discount Explorers",
    2: "One-and-Done",
    3: "Rising Stars",
    4: "Omnichannel Champions",
    5: "Quiet Regulars",
    6: "Category Specialists",
    7: "Sleeping Giants",
}


CLUSTER_FEATURE_COLS = [
    "total_revenue", "n_tickets", "avg_basket", "revenue_90d",
    "tenure_days", "avg_inter_purchase_days", "days_to_second",
    "n_unique_categories", "n_unique_channels", "is_omnichannel",
    "discount_ratio", "first_basket_value", "spending_volatility",
    "revenue_first_2_visits", "avg_basket_first_2_visits",
    "categories_first_2_visits", "channels_first_2_visits",
]


def _prepare_clustering_matrix(journey_features: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    X = journey_features[CLUSTER_FEATURE_COLS].fillna(0).copy()
    for col in X.columns:
        cap = X[col].quantile(0.99)
        X[col] = X[col].clip(upper=cap)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    return X, X_scaled


def _rank_and_name_clusters(df: pd.DataFrame, cluster_col: str) -> pd.DataFrame:
    work = df.copy()
    valid_clusters = work[work[cluster_col] >= 0]
    cluster_rev = valid_clusters.groupby(cluster_col)["total_revenue"].mean().sort_values(ascending=False)
    rank_map = {c: i for i, c in enumerate(cluster_rev.index)}
    work["cluster_rank"] = work[cluster_col].map(rank_map)
    work["cluster_rank"] = work["cluster_rank"].fillna(-1).astype(int)
    work["archetype"] = np.where(
        work["cluster_rank"] >= 0,
        work["cluster_rank"].map(lambda x: ARCHETYPE_NAMES.get(int(x), f"Segment {int(x)}")),
        "Noise / Outliers",
    )
    return work


def _cluster_profiles(df: pd.DataFrame, cluster_col: str) -> pd.DataFrame:
    prof = (
        df.groupby([cluster_col, "cluster_rank", "archetype"])
        .agg(
            size=("anonymized_card_code", "count"),
            avg_revenue=("total_revenue", "mean"),
            avg_tickets=("n_tickets", "mean"),
            avg_basket=("avg_basket", "mean"),
            avg_90d_rev=("revenue_90d", "mean"),
            avg_categories=("n_unique_categories", "mean"),
            omnichannel_pct=("is_omnichannel", "mean"),
            avg_discount_ratio=("discount_ratio", "mean"),
            avg_days_to_second=("days_to_second", "mean"),
            avg_tenure=("tenure_days", "mean"),
        )
        .reset_index()
        .sort_values("avg_revenue", ascending=False)
    )
    prof["pct_of_total"] = prof["size"] / prof["size"].sum()
    return prof


def _safe_silhouette(X_scaled: np.ndarray, labels: np.ndarray) -> float:
    unique = np.unique(labels)
    # For DBSCAN-like outputs, ignore noise label -1 for silhouette.
    valid_mask = labels >= 0
    if len(unique) < 2 or valid_mask.sum() < 20:
        return np.nan
    valid_labels = labels[valid_mask]
    if len(np.unique(valid_labels)) < 2:
        return np.nan
    return float(silhouette_score(X_scaled[valid_mask], valid_labels))


def _estimate_dbscan_eps(X_scaled: np.ndarray, min_samples: int) -> float:
    nn = NearestNeighbors(n_neighbors=min_samples)
    nn.fit(X_scaled)
    distances, _ = nn.kneighbors(X_scaled)
    kth = distances[:, -1]
    # Conservative percentile to limit noise while preserving density structure.
    return float(np.quantile(kth, 0.90))


def build_journey_features(customers: pd.DataFrame, ticket: pd.DataFrame) -> pd.DataFrame:
    """Feature matrix for clustering and scoring."""

    feats = customers[["anonymized_card_code"]].copy()

    # revenue & frequency
    feats["total_revenue"] = customers["total_revenue"]
    feats["n_tickets"] = customers["n_tickets"]
    feats["avg_basket"] = customers["avg_basket"]
    feats["revenue_90d"] = customers["revenue_90d"]

    # timing
    feats["tenure_days"] = customers["tenure_days"]
    feats["avg_inter_purchase_days"] = customers["avg_inter_purchase_days"].fillna(9999)
    feats["days_to_second"] = customers["days_to_second"].fillna(9999)

    # diversity
    feats["n_unique_categories"] = customers["n_unique_categories"]
    feats["n_unique_channels"] = customers["n_unique_channels"]
    feats["is_omnichannel"] = customers["is_omnichannel"]

    # discount dependency
    feats["discount_ratio"] = customers["discount_ratio"]

    # first purchase attributes
    feats["first_basket_value"] = customers["salesVatEUR_first_purchase"].fillna(0)
    feats["first_purchase_discounted"] = customers["first_purchase_discounted"].fillna(0)
    feats["first_purchase_discount_ratio"] = np.where(
        (customers["salesVatEUR_first_purchase"].fillna(0) + customers["discountEUR_first_purchase"].fillna(0)) > 0,
        customers["discountEUR_first_purchase"].fillna(0) /
        (customers["salesVatEUR_first_purchase"].fillna(0) + customers["discountEUR_first_purchase"].fillna(0)),
        0,
    )
    feats["second_purchase_within_30d"] = (customers["days_to_second"].fillna(9999) <= 30).astype(int)
    feats["second_purchase_within_60d"] = (customers["days_to_second"].fillna(9999) <= 60).astype(int)

    # visit-level features
    visit_stats = (
        ticket.groupby("anonymized_card_code")
        .agg(
            revenue_std=("revenue", "std"),
            max_basket=("revenue", "max"),
            min_basket=("revenue", "min"),
        )
        .reset_index()
    )
    visit_stats["revenue_std"] = visit_stats["revenue_std"].fillna(0)
    feats = feats.merge(visit_stats, on="anonymized_card_code", how="left")

    # spending volatility
    feats["spending_volatility"] = np.where(
        feats["avg_basket"] > 0,
        feats["revenue_std"] / feats["avg_basket"],
        0,
    )

    early_visit_stats = (
        ticket.loc[ticket["visit_rank"] <= 2]
        .groupby("anonymized_card_code")
        .agg(
            revenue_first_2_visits=("revenue", "sum"),
            avg_basket_first_2_visits=("revenue", "mean"),
            categories_first_2_visits=("main_cat", "nunique"),
            channels_first_2_visits=("channel", "nunique"),
        )
        .reset_index()
    )
    feats = feats.merge(early_visit_stats, on="anonymized_card_code", how="left")

    fill_zero_cols = [
        "revenue_first_2_visits",
        "avg_basket_first_2_visits",
        "categories_first_2_visits",
        "channels_first_2_visits",
    ]
    feats[fill_zero_cols] = feats[fill_zero_cols].fillna(0)

    return feats


def run_clustering(journey_features: pd.DataFrame, n_clusters: int = 5) -> tuple[pd.DataFrame, pd.DataFrame]:
    """K-Means clustering on journey features."""

    _, X_scaled = _prepare_clustering_matrix(journey_features)

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=20, max_iter=500)
    labels = km.fit_predict(X_scaled)

    journey_features = journey_features.copy()
    journey_features["cluster"] = labels
    journey_features = _rank_and_name_clusters(journey_features, "cluster")
    profiles = _cluster_profiles(journey_features, "cluster")

    return journey_features, profiles


def run_advanced_clustering(
    journey_features: pd.DataFrame,
    cluster_range: tuple[int, int] = (4, 8),
    algorithm: str = "kmeans",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Advanced clustering with auto-k selection and diagnostics.

    Args:
        journey_features: Output of build_journey_features.
        cluster_range: Min and max number of clusters to test.
        algorithm: "kmeans" or "gmm".
    """

    base = journey_features.copy()
    _, X_scaled = _prepare_clustering_matrix(base)

    min_k, max_k = cluster_range
    if min_k < 2:
        min_k = 2
    if max_k < min_k:
        max_k = min_k

    diagnostics_rows: list[dict[str, float | int | str]] = []
    best_score = -1.0
    best_labels: np.ndarray | None = None
    best_k = min_k

    for k in range(min_k, max_k + 1):
        if algorithm == "gmm":
            model = GaussianMixture(n_components=k, covariance_type="full", random_state=42)
            labels = model.fit_predict(X_scaled)
        else:
            model = KMeans(n_clusters=k, random_state=42, n_init=20, max_iter=500)
            labels = model.fit_predict(X_scaled)

        if len(np.unique(labels)) < 2:
            continue

        sil = _safe_silhouette(X_scaled, labels)
        inertia = float(getattr(model, "inertia_", np.nan))
        bic = float(getattr(model, "bic", lambda x: np.nan)(X_scaled)) if algorithm == "gmm" else np.nan
        diagnostics_rows.append(
            {
                "algorithm": algorithm,
                "k": k,
                "silhouette": sil,
                "inertia": inertia,
                "bic": bic,
            }
        )

        if sil > best_score:
            best_score = sil
            best_labels = labels
            best_k = k

    if best_labels is None:
        # fallback to original deterministic setup
        clustered, profiles = run_clustering(base, n_clusters=5)
        diagnostics = pd.DataFrame(
            [{"algorithm": "fallback_kmeans", "k": 5, "silhouette": np.nan, "inertia": np.nan, "bic": np.nan}]
        )
        return clustered, profiles, diagnostics

    base["cluster"] = best_labels
    base = _rank_and_name_clusters(base, "cluster")
    profiles = _cluster_profiles(base, "cluster")

    diagnostics = pd.DataFrame(diagnostics_rows)
    diagnostics["selected_k"] = best_k
    diagnostics["selected_silhouette"] = best_score

    return base, profiles, diagnostics


def run_clustering_suite(
    journey_features: pd.DataFrame,
    kmeans_k: int,
    dbscan_min_samples: int = 35,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run KMeans, DBSCAN, and Agglomerative clustering and compare outputs."""

    base = journey_features.copy()
    _, X_scaled = _prepare_clustering_matrix(base)

    km = KMeans(n_clusters=kmeans_k, random_state=42, n_init=20, max_iter=500)
    labels_km = km.fit_predict(X_scaled)

    agg = AgglomerativeClustering(n_clusters=kmeans_k, linkage="ward")
    labels_agg = agg.fit_predict(X_scaled)

    eps = _estimate_dbscan_eps(X_scaled, min_samples=dbscan_min_samples)
    dbs = DBSCAN(eps=eps, min_samples=dbscan_min_samples)
    labels_dbs = dbs.fit_predict(X_scaled)

    assign = base[["anonymized_card_code", "total_revenue", "n_tickets", "avg_basket", "discount_ratio"]].copy()
    assign["cluster_kmeans"] = labels_km
    assign["cluster_agglomerative"] = labels_agg
    assign["cluster_dbscan"] = labels_dbs

    profiles_frames: list[pd.DataFrame] = []
    for method_col, method in [
        ("cluster_kmeans", "kmeans"),
        ("cluster_agglomerative", "agglomerative"),
        ("cluster_dbscan", "dbscan"),
    ]:
        tmp = base.copy()
        tmp["cluster_method"] = method
        tmp["cluster"] = assign[method_col].values
        tmp = _rank_and_name_clusters(tmp, "cluster")
        prof = _cluster_profiles(tmp, "cluster")
        prof["method"] = method
        profiles_frames.append(prof)

    profiles = pd.concat(profiles_frames, ignore_index=True)

    diagnostics = pd.DataFrame(
        [
            {
                "method": "kmeans",
                "n_clusters_ex_noise": int(len(np.unique(labels_km))),
                "noise_pct": 0.0,
                "silhouette": _safe_silhouette(X_scaled, labels_km),
                "selected_k": int(kmeans_k),
                "dbscan_eps": np.nan,
                "dbscan_min_samples": np.nan,
            },
            {
                "method": "agglomerative",
                "n_clusters_ex_noise": int(len(np.unique(labels_agg))),
                "noise_pct": 0.0,
                "silhouette": _safe_silhouette(X_scaled, labels_agg),
                "selected_k": int(kmeans_k),
                "dbscan_eps": np.nan,
                "dbscan_min_samples": np.nan,
            },
            {
                "method": "dbscan",
                "n_clusters_ex_noise": int(len(set(labels_dbs)) - (1 if -1 in labels_dbs else 0)),
                "noise_pct": float((labels_dbs == -1).mean()),
                "silhouette": _safe_silhouette(X_scaled, labels_dbs),
                "selected_k": np.nan,
                "dbscan_eps": float(eps),
                "dbscan_min_samples": int(dbscan_min_samples),
            },
        ]
    )

    return assign, profiles, diagnostics
