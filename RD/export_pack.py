from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import streamlit_app as app


def _slugify(text: str) -> str:
    slug: list[str] = []
    previous_sep = False
    for char in text.lower():
        if char.isalnum():
            slug.append(char)
            previous_sep = False
        elif not previous_sep:
            slug.append("_")
            previous_sep = True
    return "".join(slug).strip("_")


def _clean_title(text: str) -> str:
    return " ".join(text.replace("-", " ").replace("_", " ").split())


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_csv(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _write_figure_png(path: Path, figure: go.Figure) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.write_image(str(path), format="png", width=1600, height=900, scale=2)


def _write_figure_html(path: Path, figure: go.Figure) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.write_html(str(path), include_plotlyjs="cdn", full_html=True, config=app.PLOTLY_CONFIG)


def _preview_block(df: pd.DataFrame, rows: int = 12) -> str:
    if df is None or df.empty:
        return "No sample rows available."
    preview = df.head(rows).copy()
    return "```csv\n" + preview.to_csv(index=False).strip() + "\n```"


def _case_markdown(row: pd.Series, sample_file: str, sample_df: pd.DataFrame, questions: list[str]) -> str:
    question_lines = "\n".join(f"- {question}" for question in questions)
    return f"""# {row['play']}

## Snapshot

- Audience: {row['audience']}
- Customers: {int(row['customers']):,}
- Value pool: {app._fmt_eur(float(row['value_pool_eur']))}
- Owner: {row['owner']}
- KPI: {row['kpi']}
- Time window: {row['time_window']}
- Trigger: {row['trigger']}

## Why this matters

{row['commercial_case']}

## Recommended move

{row['recommended_move']}

## Message and channel design

- Channel: {row['channel']}
- Offer strategy: {row['offer_strategy']}
- Message angle: {row['message_angle']}

## Deep dive questions

{question_lines}

## Sample to inspect

Companion sample file: `{sample_file}`

{_preview_block(sample_df)}
"""


def _apply_human_layout(
    fig: go.Figure,
    title: str,
    x_title: str | None = None,
    y_title: str | None = None,
    height: int = 620,
) -> go.Figure:
    fig.update_layout(**app.PLOTLY_LAYOUT)
    fig.update_layout(
        title=_clean_title(title),
        height=height,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1.0),
    )
    if x_title is not None:
        fig.update_xaxes(title=x_title)
    if y_title is not None:
        fig.update_yaxes(title=y_title)
    return fig


def _metric_bar(
    df: pd.DataFrame,
    category_col: str,
    metric_col: str,
    title: str,
    color: str,
    top_n: int = 15,
) -> go.Figure:
    view = df[[category_col, metric_col]].dropna().copy()
    view = view.sort_values(metric_col, ascending=False).head(top_n).sort_values(metric_col, ascending=True)
    fig = px.bar(view, x=metric_col, y=category_col, orientation="h", color_discrete_sequence=[color])
    return _apply_human_layout(fig, title, x_title=metric_col.replace("_", " "), y_title=category_col.replace("_", " "))


def _line_monthly_transitions(transitions_rfm: pd.DataFrame) -> list[tuple[str, go.Figure]]:
    if transitions_rfm.empty:
        return []
    monthly = (
        transitions_rfm.groupby("year_month_dt")
        .agg(
            upgrades=("rfm_improved", "sum"),
            downgrades=("rfm_declined", "sum"),
            net_revenue_delta=("delta_monthly_revenue", "sum"),
            impacted_customers=("anonymized_card_code", "nunique"),
        )
        .reset_index()
        .sort_values("year_month_dt")
    )

    charts: list[tuple[str, go.Figure]] = []
    fig1 = px.line(monthly, x="year_month_dt", y=["upgrades", "downgrades"], markers=True, color_discrete_sequence=[app.GREEN, app.RED])
    charts.append(("transition_monthly_upgrades_vs_downgrades", _apply_human_layout(fig1, "Monthly upgrades and downgrades", "Month", "Customers")))

    fig2 = px.line(monthly, x="year_month_dt", y="net_revenue_delta", markers=True, color_discrete_sequence=[app.GOLD])
    charts.append(("transition_monthly_net_revenue_delta", _apply_human_layout(fig2, "Monthly net revenue delta", "Month", "Revenue delta")))

    fig3 = px.line(monthly, x="year_month_dt", y="impacted_customers", markers=True, color_discrete_sequence=[app.CHAMPAGNE])
    charts.append(("transition_monthly_impacted_customers", _apply_human_layout(fig3, "Monthly impacted customers", "Month", "Customers")))
    return charts


def _journey_full_sankey(flow: pd.DataFrame) -> go.Figure:
    if flow.empty:
        return go.Figure()

    full = flow.sort_values(["source_stage", "target_stage", "customers"], ascending=[True, True, False]).head(120).copy()
    labels = list(pd.unique(full[["source_label", "target_label"]].values.ravel("K")))
    index = {name: i for i, name in enumerate(labels)}

    fig = go.Figure(
        go.Sankey(
            arrangement="snap",
            node=dict(
                pad=14,
                thickness=14,
                line=dict(color="rgba(0,0,0,0.15)", width=0.7),
                label=labels,
                color=[app.GOLD if i % 2 == 0 else app.CHAMPAGNE for i in range(len(labels))],
            ),
            link=dict(
                source=[index[value] for value in full["source_label"]],
                target=[index[value] for value in full["target_label"]],
                value=full["customers"].tolist(),
                color=["rgba(182,138,58,0.30)"] * len(full),
                customdata=(full["transition_rate"] * 100).round(1),
                hovertemplate="%{source.label} to %{target.label}<br>Customers %{value:,.0f}<br>Rate %{customdata:.1f}%<extra></extra>",
            ),
        )
    )
    return _apply_human_layout(fig, "Journey flow full view", height=760)


def _build_regain_comparison(transitions_rfm: pd.DataFrame) -> dict[str, object] | None:
    if transitions_rfm.empty:
        return None

    frame = transitions_rfm.copy()
    frame["year_month_dt"] = pd.to_datetime(frame["year_month_dt"], errors="coerce")
    frame = frame.dropna(subset=["year_month_dt", "prev_rfm_id", "RFM_Segment_ID"])  # noqa: PD002
    if frame.empty:
        return None

    frame["prev_rfm_id"] = pd.to_numeric(frame["prev_rfm_id"], errors="coerce")
    frame["RFM_Segment_ID"] = pd.to_numeric(frame["RFM_Segment_ID"], errors="coerce")
    frame = frame.dropna(subset=["prev_rfm_id", "RFM_Segment_ID"])  # noqa: PD002
    frame = frame[(frame["prev_rfm_id"] > 0) & (frame["prev_rfm_id"] < 99999) & (frame["RFM_Segment_ID"] > 0) & (frame["RFM_Segment_ID"] < 99999)]
    if frame.empty:
        return None

    # Regain definition: customers coming from vulnerable states into healthy states.
    frame["eligible_regain"] = frame["prev_rfm_id"].between(6, 9)
    frame["regained"] = frame["eligible_regain"] & (frame["RFM_Segment_ID"] <= 4)

    monthly = (
        frame.groupby("year_month_dt")
        .agg(
            eligible_customers=("eligible_regain", "sum"),
            regained_customers=("regained", "sum"),
        )
        .reset_index()
        .sort_values("year_month_dt")
    )
    monthly = monthly[monthly["eligible_customers"] > 0].copy()
    if monthly.empty:
        return None
    monthly["regain_rate"] = monthly["regained_customers"] / monthly["eligible_customers"]

    noel_candidates = monthly[monthly["year_month_dt"].dt.month == 12]
    noel_row = noel_candidates.sort_values("year_month_dt").tail(1)
    if noel_row.empty:
        return None
    noel_month = pd.Timestamp(noel_row.iloc[0]["year_month_dt"])

    nearby_pool = monthly[monthly["year_month_dt"] != noel_month].copy()
    if nearby_pool.empty:
        return None
    nearby_pool["distance_days"] = (nearby_pool["year_month_dt"] - noel_month).abs().dt.days
    nearby_row = nearby_pool.sort_values(["distance_days", "year_month_dt"]).head(1)
    nearby_month = pd.Timestamp(nearby_row.iloc[0]["year_month_dt"])

    comparison = pd.DataFrame(
        {
            "period": ["Noel", "Periode proche"],
            "month": [noel_month.strftime("%Y-%m"), nearby_month.strftime("%Y-%m")],
            "eligible_customers": [
                int(noel_row.iloc[0]["eligible_customers"]),
                int(nearby_row.iloc[0]["eligible_customers"]),
            ],
            "regained_customers": [
                int(noel_row.iloc[0]["regained_customers"]),
                int(nearby_row.iloc[0]["regained_customers"]),
            ],
            "regain_rate": [
                float(noel_row.iloc[0]["regain_rate"]),
                float(nearby_row.iloc[0]["regain_rate"]),
            ],
        }
    )

    selected = frame[frame["year_month_dt"].isin([noel_month, nearby_month])].copy()
    selected = selected[selected["eligible_regain"]]
    selected["period"] = np.where(selected["year_month_dt"] == noel_month, "Noel", "Periode proche")

    segment_breakdown = (
        selected.groupby(["period", "prev_rfm"], dropna=False)
        .agg(
            eligible_customers=("eligible_regain", "sum"),
            regained_customers=("regained", "sum"),
        )
        .reset_index()
    )
    segment_breakdown["regain_rate"] = np.where(
        segment_breakdown["eligible_customers"] > 0,
        segment_breakdown["regained_customers"] / segment_breakdown["eligible_customers"],
        0.0,
    )

    target_breakdown = (
        selected[selected["regained"]]
        .groupby(["period", "rfm_label"], dropna=False)
        .size()
        .reset_index(name="customers")
    )

    return {
        "monthly": monthly,
        "comparison": comparison,
        "segment_breakdown": segment_breakdown,
        "target_breakdown": target_breakdown,
        "noel_month": noel_month,
        "nearby_month": nearby_month,
    }


def _build_winning_path_conversion(
    customers: pd.DataFrame,
    journey_paths: pd.DataFrame,
    journey_variants: pd.DataFrame,
) -> dict[str, object] | None:
    if customers.empty or journey_paths.empty or journey_variants.empty:
        return None

    ranking_cols = ["customers"]
    if "value_pool_eur" in journey_variants.columns:
        ranking_cols.append("value_pool_eur")
    biggest_path = journey_variants.sort_values(ranking_cols, ascending=[False] * len(ranking_cols)).head(1)
    if biggest_path.empty:
        return None

    top_path_label = str(biggest_path.iloc[0].get("path_label", ""))
    if not top_path_label:
        return None

    journey_copy = journey_paths.copy()
    journey_copy["anonymized_card_code"] = journey_copy["anonymized_card_code"].astype(str)
    top_ids = set(
        journey_copy[journey_copy["path_label"] == top_path_label]["anonymized_card_code"].astype(str).tolist()
    )
    if not top_ids:
        return None

    customer_copy = customers.copy()
    customer_copy["anonymized_card_code"] = customer_copy["anonymized_card_code"].astype(str)
    customer_copy["on_top_winning_path"] = customer_copy["anonymized_card_code"].isin(top_ids)
    customer_copy["potential_to_convert"] = (
        (~customer_copy["on_top_winning_path"])
        & customer_copy["wp_tier"].isin(["Strong", "Elite"])
    )
    customer_copy["prime_potential"] = (
        customer_copy["potential_to_convert"]
        & customer_copy["rfm_label"].isin(["Loyal", "Potential Loyalist", "Recent", "Need Attention"])
    )

    top_base = customer_copy[customer_copy["on_top_winning_path"]]
    rest_base = customer_copy[~customer_copy["on_top_winning_path"]]
    if top_base.empty or rest_base.empty:
        return None

    profile_metrics = [
        ("value_12m_proxy", "Average 12M Value"),
        ("margin_12m_proxy", "Average 12M Margin"),
        ("repeat_customer", "Repeat Rate"),
        ("high_value", "High Value Rate"),
        ("is_omnichannel", "Omnichannel Rate"),
        ("winning_path_score", "Winning Path Score"),
    ]
    profile_rows: list[dict[str, object]] = []
    for metric_key, metric_label in profile_metrics:
        profile_rows.append(
            {
                "metric": metric_label,
                "group": "Biggest winning path",
                "value": float(top_base[metric_key].mean()),
            }
        )
        profile_rows.append(
            {
                "metric": metric_label,
                "group": "Other customers",
                "value": float(rest_base[metric_key].mean()),
            }
        )
    profile_df = pd.DataFrame(profile_rows)

    dominant_category = (
        top_base["first_category_display"].dropna().mode().iloc[0]
        if not top_base["first_category_display"].dropna().empty
        else "Unknown"
    )
    dominant_channel = (
        top_base["first_channel_display"].dropna().mode().iloc[0]
        if not top_base["first_channel_display"].dropna().empty
        else "Unknown"
    )

    potentials = customer_copy[customer_copy["potential_to_convert"]].copy()
    if potentials.empty:
        return None

    category_aligned = potentials["first_category_display"].fillna("Unknown") == dominant_category
    channel_aligned = potentials["first_channel_display"].fillna("Unknown") == dominant_channel
    potentials["conversion_alignment"] = np.select(
        [category_aligned & channel_aligned, category_aligned, channel_aligned],
        [
            "Category and channel aligned",
            "Category aligned",
            "Channel aligned",
        ],
        default="New pattern to test",
    )

    conversion_segments = (
        potentials.groupby("conversion_alignment", dropna=False)
        .agg(
            customers=("customer_id", "nunique"),
            avg_score=("winning_path_score", "mean"),
            avg_value=("value_12m_proxy", "mean"),
            avg_days_since_last=("days_since_last", "mean"),
            repeat_rate=("repeat_customer", "mean"),
        )
        .reset_index()
    )

    conversion_rfm = (
        potentials.groupby("rfm_label", dropna=False)
        .agg(
            customers=("customer_id", "nunique"),
            avg_score=("winning_path_score", "mean"),
            avg_value=("value_12m_proxy", "mean"),
        )
        .reset_index()
        .sort_values("customers", ascending=False)
    )

    conversion_funnel = pd.DataFrame(
        {
            "stage": [
                "Total base",
                "Off winning path",
                "High potential off path",
                "Prime targets now",
            ],
            "customers": [
                int(customer_copy["customer_id"].nunique()),
                int((~customer_copy["on_top_winning_path"]).sum()),
                int(customer_copy["potential_to_convert"].sum()),
                int(customer_copy["prime_potential"].sum()),
            ],
        }
    )

    target_columns = [
        "customer_id",
        "rfm_label",
        "first_category_display",
        "first_channel_display",
        "winning_path_score",
        "value_12m_proxy",
        "margin_12m_proxy",
        "days_since_last",
        "conversion_alignment",
    ]
    top_targets = potentials[target_columns].sort_values(
        ["winning_path_score", "value_12m_proxy"],
        ascending=[False, False],
    ).head(1500)

    return {
        "top_path_label": top_path_label,
        "dominant_category": dominant_category,
        "dominant_channel": dominant_channel,
        "profile_df": profile_df,
        "funnel_df": conversion_funnel,
        "potentials_df": potentials,
        "conversion_segments": conversion_segments,
        "conversion_rfm": conversion_rfm,
        "top_targets": top_targets,
    }


def _build_runtime_data() -> tuple[object, dict[str, object]]:
    data_store = app.load_store()
    if not data_store.is_ready:
        raise RuntimeError("Data not prepared. Run prepare_data.py first.")

    customers = app._prepare_customers(data_store.customers, data_store.path_scores, data_store.anomalies)
    cohorts = app._prepare_cohort_summary(data_store.first_purchase_cohort_summary)
    journey_paths = data_store.journey_paths.copy()
    journey_paths["anonymized_card_code"] = journey_paths["anonymized_card_code"].astype(str)

    variant_actions = app._variant_actions(data_store.journey_variants)
    cohort_actions = app._cohort_actions(cohorts)
    category_moves = app._category_opportunities(data_store.transitions_category, customers)
    transition_playbook = app._transition_playbook(data_store.transitions_rfm, customers)
    audiences = app._action_audiences(customers)
    priority_actions = app._priority_actions(customers, cohort_actions, audiences)
    crm_briefs = app._crm_briefs(priority_actions)
    operating_rules = app._operating_rules(variant_actions, transition_playbook, cohort_actions)
    evidence_points = app._evidence_points(customers, data_store.feature_importance, data_store.cox_summary, data_store.km_by_channel)
    executive_story = app._executive_story(priority_actions, transition_playbook, variant_actions)
    metric_audit = app._metric_audit_table(customers, audiences, data_store.transitions_rfm)

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
        "feature_importance": data_store.feature_importance,
        "model_metrics": data_store.model_metrics,
        "time_series_monthly": data_store.time_series_monthly,
        "time_series_forecast": data_store.time_series_forecast,
        "time_series_signals": data_store.time_series_signals,
        "cluster_profiles_multi": data_store.cluster_profiles_multi,
        "cluster_benchmark": data_store.cluster_benchmark,
        "pm4py_variants": data_store.pm4py_variants,
        "pm4py_dfg": data_store.pm4py_dfg,
        "pm4py_start_activities": data_store.pm4py_start_activities,
        "pm4py_end_activities": data_store.pm4py_end_activities,
        "pm4py_quality": data_store.pm4py_quality,
    }
    return data_store, data


def export_product_pack(
    data_store,
    data: dict[str, object],
    export_root: Path | None = None,
) -> dict[str, list[Path]]:
    export_root = export_root or app.OUTPUT_PACK_ROOT
    export_root.mkdir(parents=True, exist_ok=True)
    figures_png_dir = export_root / "figures" / "png"
    figures_html_dir = export_root / "figures" / "html"
    tables_dir = export_root / "tables"
    deepdives_dir = export_root / "deepdives"
    cases_dir = deepdives_dir / "cases"
    samples_dir = deepdives_dir / "samples"

    for directory in [figures_png_dir, figures_html_dir, tables_dir, cases_dir, samples_dir]:
        if directory.exists():
            for file_path in directory.glob("*"):
                if file_path.is_file():
                    file_path.unlink()

    figures: list[Path] = []
    tables: list[Path] = []
    deepdives: list[Path] = []

    customers: pd.DataFrame = data["customers"]  # type: ignore[assignment]
    cohorts: pd.DataFrame = data["cohort_actions"]  # type: ignore[assignment]
    journey_paths: pd.DataFrame = data["journey_paths"]  # type: ignore[assignment]
    transitions_rfm: pd.DataFrame = data["transitions_rfm"]  # type: ignore[assignment]
    transitions_loyalty: pd.DataFrame = data["transitions_loyalty"]  # type: ignore[assignment]
    transition_playbook: pd.DataFrame = data["transition_playbook"]  # type: ignore[assignment]
    priority_actions: pd.DataFrame = data["priority_actions"]  # type: ignore[assignment]
    crm_briefs: pd.DataFrame = data["crm_briefs"]  # type: ignore[assignment]
    operating_rules: pd.DataFrame = data["operating_rules"]  # type: ignore[assignment]
    audiences: dict[str, pd.DataFrame] = data["audiences"]  # type: ignore[assignment]
    category_moves: pd.DataFrame = data["category_moves"]  # type: ignore[assignment]
    metric_audit: pd.DataFrame = data["metric_audit"]  # type: ignore[assignment]
    journey_variants: pd.DataFrame = data["variant_actions"]  # type: ignore[assignment]
    executive_story: dict[str, str] = data["executive_story"]  # type: ignore[assignment]
    feature_importance: pd.DataFrame | None = data.get("feature_importance")  # type: ignore[assignment]
    model_metrics: pd.DataFrame | None = data.get("model_metrics")  # type: ignore[assignment]
    ts_monthly: pd.DataFrame | None = data.get("time_series_monthly")  # type: ignore[assignment]
    ts_forecast: pd.DataFrame | None = data.get("time_series_forecast")  # type: ignore[assignment]
    ts_signals: pd.DataFrame | None = data.get("time_series_signals")  # type: ignore[assignment]
    cluster_profiles_multi: pd.DataFrame | None = data.get("cluster_profiles_multi")  # type: ignore[assignment]
    cluster_benchmark: pd.DataFrame | None = data.get("cluster_benchmark")  # type: ignore[assignment]
    pm4py_variants: pd.DataFrame | None = data.get("pm4py_variants")  # type: ignore[assignment]
    pm4py_dfg: pd.DataFrame | None = data.get("pm4py_dfg")  # type: ignore[assignment]
    pm4py_start_activities: pd.DataFrame | None = data.get("pm4py_start_activities")  # type: ignore[assignment]
    pm4py_end_activities: pd.DataFrame | None = data.get("pm4py_end_activities")  # type: ignore[assignment]
    pm4py_quality: pd.DataFrame | None = data.get("pm4py_quality")  # type: ignore[assignment]

    flow, nodes = app._milestone_transition_tables(data_store.event_log, customers)
    journey_paths = journey_paths.copy()
    journey_paths["anonymized_card_code"] = journey_paths["anonymized_card_code"].astype(str)
    variants = app._variant_actions(app.summarize_journey_variants(journey_paths))
    latest_month = transitions_rfm["year_month_dt"].max()
    latest = transitions_rfm[transitions_rfm["year_month_dt"] == latest_month]
    transition_volume = (
        latest.groupby(["transition", "transition_type"])
        .size()
        .reset_index(name="customers")
        .sort_values("customers", ascending=False)
        .head(20)
        .sort_values("customers", ascending=True)
    )

    def add_figure(name: str, figure: go.Figure) -> None:
        png_path = figures_png_dir / f"{_slugify(name)}.png"
        html_path = figures_html_dir / f"{_slugify(name)}.html"
        _write_figure_png(png_path, figure)
        _write_figure_html(html_path, figure)
        figures.append(png_path)

    executive_focus = pd.DataFrame(
        {
            "play": [
                "Protect premium drifters",
                "Reactivate warm lapsed",
                "Accelerate omnichannel growth",
                "Recover margin leakage",
            ],
            "value_pool": [
                float(audiences["Protect premium drifters"]["value_12m_proxy"].sum()),
                float(audiences["Reactivate warm lapsed"]["value_12m_proxy"].sum()),
                float(audiences["Accelerate omnichannel growth"]["value_12m_proxy"].sum()),
                float(audiences["Recover margin leakage"]["margin_12m_proxy"].sum()),
            ],
        }
    ).sort_values("value_pool", ascending=True)

    scale_paths = journey_variants[journey_variants["motion"] == "Scale"].copy()
    if scale_paths.empty:
        scale_paths = journey_variants.head(10).copy()
    scale_paths = scale_paths.sort_values(["value_pool_eur", "customers"], ascending=[False, False]).head(15)
    scale_paths = scale_paths.sort_values("avg_12m_value", ascending=True)

    add_figure(
        "Executive value pools",
        _apply_human_layout(
            px.bar(executive_focus, x="value_pool", y="play", orientation="h", color="play", color_discrete_sequence=[app.RED, app.GOLD, app.GREEN, app.CHAMPAGNE]),
            "Value pools you can influence now",
            "Value pool",
            "Play",
        ),
    )
    add_figure("Executive transition bridge", _apply_human_layout(app._transition_waterfall(transition_playbook), "Transition impact bridge"))
    add_figure(
        "Executive journey scaling",
        _apply_human_layout(
            px.bar(scale_paths, x="avg_12m_value", y="journey_archetype", orientation="h", color="high_value_rate", color_continuous_scale=["#E7D7B4", app.CHAMPAGNE, app.GOLD]),
            "Journey archetypes to scale",
            "Average twelve month value",
            "Journey archetype",
        ),
    )
    add_figure("Executive retention curve", _apply_human_layout(app._retention_chart(data["retention_curves"]), "Retention after first purchase", "Days", "Retention rate"))
    add_figure("Journey topology", _apply_human_layout(app._journey_landscape_figure(flow, nodes), "Journey landscape topology"))
    add_figure("Journey transition matrix", _apply_human_layout(app._transition_matrix_figure(flow), "Journey transition matrix"))
    add_figure("Journey flow full", _journey_full_sankey(flow))
    add_figure("Journey variant economics", _apply_human_layout(px.scatter(variants.head(60), x="avg_90d_value", y="avg_12m_value", size="customers", color="motion", hover_name="journey_archetype", color_discrete_map={"Scale": app.GREEN, "Fix": app.GOLD, "Stop": app.RED, "Monitor": app.CHAMPAGNE}), "Variant economics map", "Average ninety day value", "Average twelve month value"))
    add_figure("Transition heatmap", _apply_human_layout(app._rfm_heatmap(data["matrix_rfm"]), "RFM transition map"))
    add_figure("Transition volume", _apply_human_layout(app._bar_chart(transition_volume, x="customers", y="transition", color="transition_type", horizontal=True, height=620), "Top transitions this month", "Customers", "Transition"))
    add_figure("Transition revenue bridge", _apply_human_layout(app._transition_waterfall(transition_playbook), "Revenue bridge by transition"))
    add_figure("First purchase cohort economics", _apply_human_layout(px.scatter(cohorts.head(100), x="avg_first_basket", y="avg_12m_value", size="customers", color="decision", hover_name="cohort_label", color_discrete_map={"Scale": app.GREEN, "Fix economics": app.GOLD, "Fix speed": app.CHAMPAGNE, "Stop scaling": app.RED, "Monitor": app.TAUPE}), "Acquisition cohort economics map", "Average first basket", "Average twelve month value"))
    add_figure("Action center priority pool", _apply_human_layout(px.bar(priority_actions.sort_values("value_pool_eur", ascending=True), x="value_pool_eur", y="play", orientation="h", color="play", color_discrete_sequence=[app.GREEN, app.GOLD, app.CHAMPAGNE, app.RED, app.TAUPE]), "Priority actions by value pool", "Value pool", "Action"))

    regain_block = _build_regain_comparison(transitions_rfm)
    if regain_block is not None:
        comparison_df: pd.DataFrame = regain_block["comparison"]  # type: ignore[assignment]
        monthly_regain_df: pd.DataFrame = regain_block["monthly"]  # type: ignore[assignment]
        segment_regain_df: pd.DataFrame = regain_block["segment_breakdown"]  # type: ignore[assignment]
        target_regain_df: pd.DataFrame = regain_block["target_breakdown"]  # type: ignore[assignment]

        fig_regain_rate = px.bar(
            comparison_df,
            x="period",
            y="regain_rate",
            color="period",
            text=(comparison_df["regain_rate"] * 100).round(1).astype(str) + "%",
            color_discrete_map={"Noel": app.GOLD, "Periode proche": app.CHAMPAGNE},
        )
        fig_regain_rate.update_traces(textposition="outside")
        add_figure(
            "Noel vs periode proche taux de regain",
            _apply_human_layout(fig_regain_rate, "Noel vs periode proche taux de regain", "Periode", "Taux de regain"),
        )

        volume_long = comparison_df.melt(
            id_vars=["period", "month"],
            value_vars=["eligible_customers", "regained_customers"],
            var_name="metric",
            value_name="customers",
        )
        add_figure(
            "Noel vs periode proche volumes regain",
            _apply_human_layout(
                px.bar(
                    volume_long,
                    x="period",
                    y="customers",
                    color="metric",
                    barmode="group",
                    color_discrete_sequence=[app.CHAMPAGNE, app.GOLD],
                ),
                "Noel vs periode proche volumes de regain",
                "Periode",
                "Customers",
            ),
        )

        monthly_fig = px.line(
            monthly_regain_df,
            x="year_month_dt",
            y="regain_rate",
            markers=True,
            color_discrete_sequence=[app.GOLD],
        )
        add_figure(
            "Trend mensuel taux de regain",
            _apply_human_layout(monthly_fig, "Trend mensuel du taux de regain", "Mois", "Taux de regain"),
        )

        if not segment_regain_df.empty:
            segment_fig = px.bar(
                segment_regain_df,
                x="prev_rfm",
                y="regain_rate",
                color="period",
                barmode="group",
                color_discrete_map={"Noel": app.GOLD, "Periode proche": app.CHAMPAGNE},
            )
            add_figure(
                "Regain par segment fragile Noel vs proche",
                _apply_human_layout(segment_fig, "Regain par segment fragile Noel vs proche", "Segment d origine", "Taux de regain"),
            )

        if not target_regain_df.empty:
            target_fig = px.bar(
                target_regain_df,
                x="rfm_label",
                y="customers",
                color="period",
                barmode="group",
                color_discrete_map={"Noel": app.GOLD, "Periode proche": app.CHAMPAGNE},
            )
            add_figure(
                "Destinations du regain Noel vs proche",
                _apply_human_layout(target_fig, "Destinations du regain Noel vs proche", "Segment cible", "Customers regagnes"),
            )

    winning_block = _build_winning_path_conversion(customers, journey_paths, journey_variants)
    if winning_block is not None:
        top_path_label = str(winning_block["top_path_label"])
        profile_df: pd.DataFrame = winning_block["profile_df"]  # type: ignore[assignment]
        funnel_df: pd.DataFrame = winning_block["funnel_df"]  # type: ignore[assignment]
        potentials_df: pd.DataFrame = winning_block["potentials_df"]  # type: ignore[assignment]
        conversion_segments_df: pd.DataFrame = winning_block["conversion_segments"]  # type: ignore[assignment]
        conversion_rfm_df: pd.DataFrame = winning_block["conversion_rfm"]  # type: ignore[assignment]

        profile_fig = px.bar(
            profile_df,
            x="metric",
            y="value",
            color="group",
            barmode="group",
            color_discrete_map={"Biggest winning path": app.GOLD, "Other customers": app.CHAMPAGNE},
        )
        add_figure(
            "Plus gros winning path profil vs reste",
            _apply_human_layout(
                profile_fig,
                f"Profil du plus gros winning path vs reste base {top_path_label}",
                "Metric",
                "Value",
            ),
        )

        funnel_fig = px.funnel(
            funnel_df,
            x="customers",
            y="stage",
            color_discrete_sequence=[app.GOLD],
        )
        add_figure(
            "Funnel conversion vers winning path",
            _apply_human_layout(
                funnel_fig,
                f"Funnel conversion vers winning path {top_path_label}",
                "Customers",
                "Stage",
            ),
        )

        if not conversion_rfm_df.empty:
            rfm_fig = px.bar(
                conversion_rfm_df.sort_values("customers", ascending=True),
                x="customers",
                y="rfm_label",
                orientation="h",
                color="avg_score",
                color_continuous_scale=["#F0E5CC", app.CHAMPAGNE, app.GOLD],
            )
            add_figure(
                "Segments potentiels pour convertir",
                _apply_human_layout(
                    rfm_fig,
                    f"Segments RFM potentiels vers {top_path_label}",
                    "Customers",
                    "Segment",
                ),
            )

        if not conversion_segments_df.empty:
            alignment_fig = px.bar(
                conversion_segments_df.sort_values("customers", ascending=True),
                x="customers",
                y="conversion_alignment",
                orientation="h",
                color="avg_score",
                color_continuous_scale=["#F0E5CC", app.CHAMPAGNE, app.GOLD],
            )
            add_figure(
                "Alignement de conversion vers winning path",
                _apply_human_layout(
                    alignment_fig,
                    f"Alignement des potentiels vers {top_path_label}",
                    "Customers",
                    "Alignement",
                ),
            )

        if not potentials_df.empty:
            scatter_source = potentials_df.head(5000).copy()
            scatter_source["bubble_size"] = scatter_source["value_12m_proxy"].fillna(0).clip(lower=0) + 1
            scatter_fig = px.scatter(
                scatter_source,
                x="days_since_last",
                y="winning_path_score",
                size="bubble_size",
                color="conversion_alignment",
                hover_data=["rfm_label", "first_category_display", "first_channel_display"],
                color_discrete_sequence=[app.GOLD, app.CHAMPAGNE, app.GREEN, app.RED],
            )
            add_figure(
                "Map priorisation conversion winning path",
                _apply_human_layout(
                    scatter_fig,
                    f"Map de priorisation conversion vers {top_path_label}",
                    "Days since last purchase",
                    "Winning path score",
                ),
            )

    for name, fig in _line_monthly_transitions(transitions_rfm):
        add_figure(name, fig)

    category_perf = (
        customers.groupby("first_category_display", dropna=False)
        .agg(
            customers=("customer_id", "nunique"),
            avg_value=("value_12m_proxy", "mean"),
            avg_margin=("margin_12m_proxy", "mean"),
            repeat_rate=("repeat_customer", "mean"),
            high_value_rate=("high_value", "mean"),
            avg_path_score=("winning_path_score", "mean"),
        )
        .reset_index()
    )
    category_perf = category_perf[category_perf["customers"] >= 50]

    channel_perf = (
        customers.groupby("first_channel_display", dropna=False)
        .agg(
            customers=("customer_id", "nunique"),
            avg_value=("value_12m_proxy", "mean"),
            avg_margin=("margin_12m_proxy", "mean"),
            repeat_rate=("repeat_customer", "mean"),
            high_value_rate=("high_value", "mean"),
            avg_path_score=("winning_path_score", "mean"),
        )
        .reset_index()
    )
    channel_perf = channel_perf[channel_perf["customers"] >= 50]

    rfm_perf = (
        customers.groupby("rfm_label", dropna=False)
        .agg(
            customers=("customer_id", "nunique"),
            avg_value=("value_12m_proxy", "mean"),
            avg_margin=("margin_12m_proxy", "mean"),
            repeat_rate=("repeat_customer", "mean"),
            high_value_rate=("high_value", "mean"),
            avg_path_score=("winning_path_score", "mean"),
        )
        .reset_index()
    )

    country_perf = (
        customers.groupby("country_display", dropna=False)
        .agg(
            customers=("customer_id", "nunique"),
            avg_value=("value_12m_proxy", "mean"),
            high_value_rate=("high_value", "mean"),
            avg_path_score=("winning_path_score", "mean"),
        )
        .reset_index()
    )

    risk_perf = (
        customers.groupby("risk_band", dropna=False)
        .agg(
            customers=("customer_id", "nunique"),
            avg_value=("value_12m_proxy", "mean"),
            repeat_rate=("repeat_customer", "mean"),
            avg_path_score=("winning_path_score", "mean"),
        )
        .reset_index()
    )

    phase_perf = (
        customers.groupby("phase_proxy", dropna=False)
        .agg(
            customers=("customer_id", "nunique"),
            avg_value=("value_12m_proxy", "mean"),
            high_value_rate=("high_value", "mean"),
        )
        .reset_index()
    )

    cohort_decision_perf = (
        cohorts.groupby("decision", dropna=False)
        .agg(
            customers=("customers", "sum"),
            avg_12m_value=("avg_12m_value", "mean"),
            avg_margin_12m=("avg_margin_12m", "mean"),
            high_value_rate=("high_value_rate", "mean"),
        )
        .reset_index()
    )

    category_specs = [
        ("Category customers", "customers", app.GOLD),
        ("Category average value", "avg_value", app.GREEN),
        ("Category average margin", "avg_margin", app.CHAMPAGNE),
        ("Category repeat rate", "repeat_rate", app.GOLD),
        ("Category high value rate", "high_value_rate", app.GREEN),
        ("Category path score", "avg_path_score", app.RED),
    ]
    for title, metric, color in category_specs:
        if not category_perf.empty:
            add_figure(title, _metric_bar(category_perf, "first_category_display", metric, title, color, top_n=18))

    channel_specs = [
        ("Channel customers", "customers", app.GOLD),
        ("Channel average value", "avg_value", app.GREEN),
        ("Channel average margin", "avg_margin", app.CHAMPAGNE),
        ("Channel repeat rate", "repeat_rate", app.GOLD),
        ("Channel high value rate", "high_value_rate", app.GREEN),
        ("Channel path score", "avg_path_score", app.RED),
    ]
    for title, metric, color in channel_specs:
        if not channel_perf.empty:
            add_figure(title, _metric_bar(channel_perf, "first_channel_display", metric, title, color, top_n=18))

    rfm_specs = [
        ("RFM customers", "customers", app.GOLD),
        ("RFM average value", "avg_value", app.GREEN),
        ("RFM average margin", "avg_margin", app.CHAMPAGNE),
        ("RFM repeat rate", "repeat_rate", app.GOLD),
        ("RFM high value rate", "high_value_rate", app.GREEN),
        ("RFM path score", "avg_path_score", app.RED),
    ]
    for title, metric, color in rfm_specs:
        add_figure(title, _metric_bar(rfm_perf, "rfm_label", metric, title, color, top_n=20))

    country_specs = [
        ("Country customers", "customers", app.GOLD),
        ("Country average value", "avg_value", app.GREEN),
        ("Country high value rate", "high_value_rate", app.CHAMPAGNE),
        ("Country path score", "avg_path_score", app.RED),
    ]
    for title, metric, color in country_specs:
        add_figure(title, _metric_bar(country_perf, "country_display", metric, title, color, top_n=15))

    risk_specs = [
        ("Risk band customers", "customers", app.GOLD),
        ("Risk band average value", "avg_value", app.GREEN),
        ("Risk band repeat rate", "repeat_rate", app.CHAMPAGNE),
        ("Risk band path score", "avg_path_score", app.RED),
    ]
    for title, metric, color in risk_specs:
        add_figure(title, _metric_bar(risk_perf, "risk_band", metric, title, color, top_n=10))

    phase_specs = [
        ("Journey phase customers", "customers", app.GOLD),
        ("Journey phase average value", "avg_value", app.GREEN),
        ("Journey phase high value rate", "high_value_rate", app.RED),
    ]
    for title, metric, color in phase_specs:
        add_figure(title, _metric_bar(phase_perf, "phase_proxy", metric, title, color, top_n=10))

    cohort_specs = [
        ("Cohort decision customers", "customers", app.GOLD),
        ("Cohort decision value", "avg_12m_value", app.GREEN),
        ("Cohort decision margin", "avg_margin_12m", app.CHAMPAGNE),
        ("Cohort decision high value rate", "high_value_rate", app.RED),
    ]
    for title, metric, color in cohort_specs:
        add_figure(title, _metric_bar(cohort_decision_perf, "decision", metric, title, color, top_n=8))

    playbook_up = transition_playbook[transition_playbook["transition_type"] == "upgrade"].copy()
    playbook_down = transition_playbook[transition_playbook["transition_type"] == "downgrade"].copy()
    if not playbook_up.empty:
        add_figure("Top upgrade impact", _metric_bar(playbook_up, "transition", "impact_eur", "Top upgrade impact", app.GREEN, top_n=18))
        add_figure("Top upgrade customers", _metric_bar(playbook_up, "transition", "customers", "Top upgrade customers", app.GOLD, top_n=18))
    if not playbook_down.empty:
        add_figure("Top downgrade impact", _metric_bar(playbook_down, "transition", "impact_eur", "Top downgrade impact", app.RED, top_n=18))
        add_figure("Top downgrade customers", _metric_bar(playbook_down, "transition", "customers", "Top downgrade customers", app.CHAMPAGNE, top_n=18))

    transition_driver = transition_playbook.groupby("driver_summary").agg(impact=("impact_eur", "sum")).reset_index()
    add_figure("Transition drivers by impact", _metric_bar(transition_driver, "driver_summary", "impact", "Transition drivers by impact", app.GOLD, top_n=12))

    journey_motion = journey_variants.groupby("motion").agg(customers=("customers", "sum"), value_pool=("value_pool_eur", "sum")).reset_index()
    add_figure("Journey motions by customers", _metric_bar(journey_motion, "motion", "customers", "Journey motions by customers", app.GOLD, top_n=8))
    add_figure("Journey motions by value pool", _metric_bar(journey_motion, "motion", "value_pool", "Journey motions by value pool", app.GREEN, top_n=8))

    archetype_perf = journey_variants.groupby("journey_archetype").agg(customers=("customers", "sum"), avg_value=("avg_12m_value", "mean"), high_value_rate=("high_value_rate", "mean")).reset_index()
    add_figure("Archetype customers", _metric_bar(archetype_perf, "journey_archetype", "customers", "Journey archetype customers", app.GOLD, top_n=12))
    add_figure("Archetype average value", _metric_bar(archetype_perf, "journey_archetype", "avg_value", "Journey archetype average value", app.GREEN, top_n=12))
    add_figure("Archetype high value rate", _metric_bar(archetype_perf, "journey_archetype", "high_value_rate", "Journey archetype high value rate", app.RED, top_n=12))

    audience_order = [
        "Protect premium drifters",
        "Reactivate warm lapsed",
        "Accelerate omnichannel growth",
        "Recover margin leakage",
    ]
    audience_sizes = pd.DataFrame({
        "audience": audience_order,
        "customers": [len(audiences[name]) for name in audience_order],
    })
    add_figure("Audience sizes", _metric_bar(audience_sizes, "audience", "customers", "Audience sizes", app.GOLD, top_n=10))

    for audience_name in audience_order:
        audience_df = audiences[audience_name]
        if audience_df is None or audience_df.empty:
            continue
        hist = px.histogram(audience_df.head(5000), x="value_12m_proxy", nbins=30, color_discrete_sequence=[app.GOLD])
        add_figure(f"{audience_name} value distribution", _apply_human_layout(hist, f"{audience_name} value distribution", "Value twelve month proxy", "Customers"))

    if model_metrics is not None and not model_metrics.empty:
        model_bar = px.bar(
            model_metrics,
            x="model",
            y="auc",
            text=model_metrics["auc"].round(3),
            color="model",
            color_discrete_sequence=[app.GOLD, app.CHAMPAGNE, app.GREEN],
        )
        model_bar.update_traces(textposition="outside")
        add_figure("AI model performance auc", _apply_human_layout(model_bar, "AI model performance AUC", "Model", "AUC"))

    if feature_importance is not None and not feature_importance.empty:
        fi = feature_importance.sort_values("importance", ascending=False).head(15).copy()
        fi = fi.sort_values("importance", ascending=True)
        fi_fig = px.bar(fi, x="importance", y="feature", orientation="h", color_discrete_sequence=[app.GOLD])
        add_figure("AI feature importance top drivers", _apply_human_layout(fi_fig, "AI feature importance top drivers", "Importance", "Feature"))

    if ts_forecast is not None and not ts_forecast.empty:
        for series_name in ["revenue", "tickets", "active_customers"]:
            series_df = ts_forecast[ts_forecast["series"] == series_name].copy()
            if series_df.empty:
                continue
            series_df = series_df.sort_values("ds")
            fig_ts = go.Figure()
            hist = series_df[series_df["y"].notna()]
            fcst = series_df[series_df["forecast"].notna()]
            if not hist.empty:
                fig_ts.add_trace(go.Scatter(x=hist["ds"], y=hist["y"], mode="lines+markers", name="Actual", line=dict(color=app.GOLD, width=3)))
            if not fcst.empty:
                fig_ts.add_trace(go.Scatter(x=fcst["ds"], y=fcst["forecast"], mode="lines+markers", name="Forecast", line=dict(color=app.GREEN, dash="dash", width=3)))
                if "lower" in fcst.columns and "upper" in fcst.columns:
                    fig_ts.add_trace(go.Scatter(x=fcst["ds"], y=fcst["upper"], mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
                    fig_ts.add_trace(go.Scatter(x=fcst["ds"], y=fcst["lower"], mode="lines", fill="tonexty", line=dict(width=0), name="Forecast band", fillcolor="rgba(31, 132, 90, 0.18)"))
            add_figure(f"Time series forecast {series_name}", _apply_human_layout(fig_ts, f"Time series forecast {series_name}", "Month", "Value"))

    if ts_signals is not None and not ts_signals.empty:
        signal_fig = px.bar(
            ts_signals,
            x="metric",
            y="forecast_uplift_rate",
            color="signal",
            text=(ts_signals["forecast_uplift_rate"] * 100).round(1).astype(str) + "%",
            color_discrete_map={"up": app.GREEN, "flat": app.CHAMPAGNE, "down": app.RED},
        )
        signal_fig.update_traces(textposition="outside")
        add_figure("Time series forecast signals", _apply_human_layout(signal_fig, "Time series forecast signals", "Metric", "Forecast uplift rate"))

    if cluster_benchmark is not None and not cluster_benchmark.empty:
        sil_df = cluster_benchmark.dropna(subset=["silhouette"]).copy()
        if not sil_df.empty:
            sil_fig = px.bar(
                sil_df,
                x="method",
                y="silhouette",
                text=sil_df["silhouette"].round(3),
                color="method",
                color_discrete_sequence=[app.GOLD, app.CHAMPAGNE, app.GREEN],
            )
            sil_fig.update_traces(textposition="outside")
            add_figure("Clustering benchmark silhouette", _apply_human_layout(sil_fig, "Clustering benchmark silhouette", "Method", "Silhouette"))

        if "noise_pct" in cluster_benchmark.columns:
            noise_fig = px.bar(
                cluster_benchmark,
                x="method",
                y="noise_pct",
                text=(cluster_benchmark["noise_pct"].fillna(0) * 100).round(1).astype(str) + "%",
                color="method",
                color_discrete_sequence=[app.GOLD, app.CHAMPAGNE, app.GREEN],
            )
            noise_fig.update_traces(textposition="outside")
            add_figure("Clustering benchmark noise share", _apply_human_layout(noise_fig, "Clustering benchmark noise share", "Method", "Noise share"))

    if cluster_profiles_multi is not None and not cluster_profiles_multi.empty:
        cp = cluster_profiles_multi.copy()
        cp = cp[cp["size"] > 0]
        if not cp.empty:
            size_fig = px.bar(
                cp.sort_values("size", ascending=False).head(24),
                x="size",
                y="archetype",
                color="method",
                orientation="h",
                barmode="group",
            )
            add_figure("Clustering profiles by method and size", _apply_human_layout(size_fig, "Clustering profiles by method and size", "Customers", "Archetype"))

            rev_fig = px.scatter(
                cp,
                x="avg_discount_ratio",
                y="avg_revenue",
                size="size",
                color="method",
                hover_name="archetype",
            )
            add_figure("Clustering profiles revenue vs discount", _apply_human_layout(rev_fig, "Clustering profiles revenue vs discount", "Average discount ratio", "Average revenue"))

    if pm4py_variants is not None and not pm4py_variants.empty:
        variants_top = pm4py_variants.head(15).copy().sort_values("cases", ascending=True)
        var_fig = px.bar(variants_top, x="cases", y="variant", orientation="h", color_discrete_sequence=[app.GOLD])
        add_figure("PM4Py top journey variants", _apply_human_layout(var_fig, "PM4Py top journey variants", "Cases", "Variant"))

    if pm4py_dfg is not None and not pm4py_dfg.empty:
        dfg_top = pm4py_dfg.head(20).copy()
        dfg_top["edge"] = dfg_top["source"].astype(str) + " -> " + dfg_top["target"].astype(str)
        dfg_top = dfg_top.sort_values("frequency", ascending=True)
        dfg_fig = px.bar(dfg_top, x="frequency", y="edge", orientation="h", color_discrete_sequence=[app.CHAMPAGNE])
        add_figure("PM4Py top directly follows edges", _apply_human_layout(dfg_fig, "PM4Py top directly follows edges", "Frequency", "Edge"))

    if pm4py_start_activities is not None and not pm4py_start_activities.empty:
        start_fig = px.bar(pm4py_start_activities, x="activity", y="frequency", color_discrete_sequence=[app.GOLD])
        add_figure("PM4Py start activities", _apply_human_layout(start_fig, "PM4Py start activities", "Activity", "Frequency"))

    if pm4py_end_activities is not None and not pm4py_end_activities.empty:
        end_fig = px.bar(pm4py_end_activities, x="activity", y="frequency", color_discrete_sequence=[app.CHAMPAGNE])
        add_figure("PM4Py end activities", _apply_human_layout(end_fig, "PM4Py end activities", "Activity", "Frequency"))

    if pm4py_quality is not None and not pm4py_quality.empty:
        quality_fig = px.bar(pm4py_quality, x="metric", y="value", color_discrete_sequence=[app.GREEN])
        add_figure("PM4Py process quality metrics", _apply_human_layout(quality_fig, "PM4Py process quality metrics", "Metric", "Value"))

    tables_to_export = {
        "executive_priority_actions.csv": priority_actions,
        "executive_metric_audit.csv": metric_audit,
        "executive_evidence_points.csv": pd.DataFrame(data["evidence_points"]),
        "journey_variants.csv": journey_variants,
        "journey_category_moves.csv": category_moves,
        "transition_playbook.csv": transition_playbook,
        "transition_rfm.csv": transitions_rfm,
        "transition_loyalty.csv": transitions_loyalty,
        "first_purchase_cohort_actions.csv": cohorts,
        "action_center_priority_actions.csv": priority_actions,
        "action_center_crm_briefs.csv": crm_briefs,
        "action_center_operating_rules.csv": operating_rules,
    }

    if feature_importance is not None and not feature_importance.empty:
        tables_to_export["ai_feature_importance.csv"] = feature_importance
    if model_metrics is not None and not model_metrics.empty:
        tables_to_export["ai_model_metrics.csv"] = model_metrics
    if ts_monthly is not None and not ts_monthly.empty:
        tables_to_export["ai_time_series_monthly.csv"] = ts_monthly
    if ts_forecast is not None and not ts_forecast.empty:
        tables_to_export["ai_time_series_forecast.csv"] = ts_forecast
    if ts_signals is not None and not ts_signals.empty:
        tables_to_export["ai_time_series_signals.csv"] = ts_signals
    if cluster_profiles_multi is not None and not cluster_profiles_multi.empty:
        tables_to_export["ai_cluster_profiles_multi.csv"] = cluster_profiles_multi
    if cluster_benchmark is not None and not cluster_benchmark.empty:
        tables_to_export["ai_cluster_benchmark.csv"] = cluster_benchmark
    if pm4py_variants is not None and not pm4py_variants.empty:
        tables_to_export["pm4py_variants.csv"] = pm4py_variants
    if pm4py_dfg is not None and not pm4py_dfg.empty:
        tables_to_export["pm4py_dfg.csv"] = pm4py_dfg
    if pm4py_start_activities is not None and not pm4py_start_activities.empty:
        tables_to_export["pm4py_start_activities.csv"] = pm4py_start_activities
    if pm4py_end_activities is not None and not pm4py_end_activities.empty:
        tables_to_export["pm4py_end_activities.csv"] = pm4py_end_activities
    if pm4py_quality is not None and not pm4py_quality.empty:
        tables_to_export["pm4py_quality.csv"] = pm4py_quality

    if regain_block is not None:
        tables_to_export["seasonal_regain_monthly.csv"] = regain_block["monthly"]  # type: ignore[index]
        tables_to_export["seasonal_regain_noel_vs_proche.csv"] = regain_block["comparison"]  # type: ignore[index]
        tables_to_export["seasonal_regain_by_source_segment.csv"] = regain_block["segment_breakdown"]  # type: ignore[index]

    if winning_block is not None:
        tables_to_export["winning_path_conversion_targets.csv"] = winning_block["top_targets"]  # type: ignore[index]
        tables_to_export["winning_path_conversion_segments.csv"] = winning_block["conversion_segments"]  # type: ignore[index]
        tables_to_export["winning_path_conversion_rfm_segments.csv"] = winning_block["conversion_rfm"]  # type: ignore[index]
    for filename, frame in tables_to_export.items():
        if frame is not None and not frame.empty:
            path = tables_dir / filename
            _write_csv(path, frame)
            tables.append(path)

    index_lines = [
        "# Winning Paths Product Pack",
        "",
        "This folder contains a human friendly graph library for screens and presentations.",
        "",
        f"- Executive story: {executive_story['What changed']}",
        f"- Why now: {executive_story['Why']}",
        f"- Who is affected: {executive_story['Who is affected']}",
        f"- What to do now: {executive_story['What we should do now']}",
        "",
        f"- Total PNG figures: {len(figures)}",
        "",
        "## New focus",
    ]

    if regain_block is not None:
        noel_month = pd.Timestamp(regain_block["noel_month"]).strftime("%Y-%m")  # type: ignore[arg-type]
        nearby_month = pd.Timestamp(regain_block["nearby_month"]).strftime("%Y-%m")  # type: ignore[arg-type]
        index_lines.extend(
            [
                f"- Seasonal regain benchmark: Noel {noel_month} vs periode proche {nearby_month}",
            ]
        )

    if winning_block is not None:
        index_lines.extend(
            [
                f"- Biggest winning path tracked: {winning_block['top_path_label']}",
            ]
        )

    index_lines.extend([
        "",
        "## Figures PNG",
    ])
    index_lines.extend(f"- {path.relative_to(export_root).as_posix()}" for path in figures)
    index_lines.extend(["", "## Tables"])
    index_lines.extend(f"- {path.relative_to(export_root).as_posix()}" for path in tables)
    index_lines.extend(["", "## Deep dives"])

    case_configs: dict[str, dict[str, object]] = {
        "Protect premium drifters": {
            "questions": [
                "Which fragile RFM states hold the most value and should be saved first?",
                "Where is discount reliance highest and can service nudges replace it?",
                "Which category and channel combination should receive the first save sequence?",
            ],
            "sample": audiences["Protect premium drifters"].sort_values(["value_12m_proxy", "days_since_last"], ascending=[False, False]),
        },
        "Reactivate warm lapsed": {
            "questions": [
                "Which customers are still warm enough for a low cost win back?",
                "What trigger should be tested before the customer slips into lost territory?",
                "Which editorial message can reopen the routine without blanket discounting?",
            ],
            "sample": audiences["Reactivate warm lapsed"].sort_values(["winning_path_score", "days_since_last"], ascending=[False, False]),
        },
        "Accelerate omnichannel growth": {
            "questions": [
                "Which mono channel repeaters are closest to a second channel conversion?",
                "What is the observed value gap between mono channel and omnichannel peers?",
                "Which channel to channel move should be tested first?",
            ],
            "sample": audiences["Accelerate omnichannel growth"].sort_values(["value_12m_proxy", "days_to_second"], ascending=[False, True]),
        },
        "Recover margin leakage": {
            "questions": [
                "Where is discount intensity above thirty percent while retention remains salvageable?",
                "Which bundles or exclusives can replace blanket discounting?",
                "What KPI will prove margin recovery without suppressing repeat rate?",
            ],
            "sample": audiences["Recover margin leakage"].sort_values(["margin_12m_proxy", "winning_path_score"], ascending=[False, False]),
        },
        "Scale the best acquisition seed": {
            "questions": [
                "Which acquisition cohorts create the strongest twelve month value and margin profile?",
                "Where should budget be shifted to get more customers starting the right routine?",
                "Which first basket mix and welcome sequence should be replicated first?",
            ],
            "sample": cohorts[cohorts["decision"].isin(["Scale", "Fix economics", "Fix speed"])].sort_values(["avg_12m_value", "customers"], ascending=[False, False]),
        },
    }

    for row in priority_actions.itertuples(index=False):
        if row.play not in case_configs:
            continue
        sample_df = case_configs[row.play]["sample"]  # type: ignore[index]
        sample_df = sample_df.head(50).copy()
        sample_file = samples_dir / f"{_slugify(row.play)}_sample.csv"
        _write_csv(sample_file, sample_df)
        case_md = _case_markdown(pd.Series(row._asdict()), sample_file.relative_to(export_root).as_posix(), sample_df, case_configs[row.play]["questions"])  # type: ignore[index]
        case_path = cases_dir / f"{_slugify(row.play)}.md"
        _write_text(case_path, case_md)
        deepdives.extend([sample_file, case_path])
        index_lines.append(f"- {case_path.relative_to(export_root).as_posix()}")

    index_lines.extend([
        "",
        "## Notes",
        "- PNG is the primary export format for impactful screen usage.",
        "- HTML mirrors are also generated for interactive review.",
        "- Deep dives pair markdown briefs with sample CSV files.",
    ])
    index_path = export_root / "index.md"
    _write_text(index_path, "\n".join(index_lines) + "\n")

    deepdives.append(index_path)
    return {"figures": figures, "tables": tables, "deepdives": deepdives}


if __name__ == "__main__":
    store, runtime_data = _build_runtime_data()
    summary = export_product_pack(store, runtime_data)
    print(
        f"Exported {len(summary['figures'])} PNG figures, {len(summary['tables'])} tables, "
        f"and {len(summary['deepdives'])} deep dive files to {app.OUTPUT_PACK_ROOT}"
    )
