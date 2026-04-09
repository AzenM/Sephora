"""PM4Py process-mining utilities for journey event logs."""

from __future__ import annotations

import pandas as pd

try:
    import pm4py
    HAS_PM4PY = True
except ImportError:
    HAS_PM4PY = False


REQUIRED_COLS = ["case:concept:name", "concept:name", "time:timestamp"]


def _empty_outputs() -> dict[str, pd.DataFrame]:
    return {
        "pm4py_variants": pd.DataFrame(),
        "pm4py_dfg": pd.DataFrame(),
        "pm4py_start_activities": pd.DataFrame(),
        "pm4py_end_activities": pd.DataFrame(),
        "pm4py_quality": pd.DataFrame(),
    }


def run_pm4py_process_mining(event_log: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build PM4Py process-mining artifacts from event log.

    Returns multiple dataframes to persist as analytical artifacts.
    """

    if not HAS_PM4PY or event_log is None or event_log.empty:
        if not HAS_PM4PY:
            print("pm4py not installed — skipping process-mining artifacts")
        return _empty_outputs()

    missing = [col for col in REQUIRED_COLS if col not in event_log.columns]
    if missing:
        print(f"pm4py skipped: missing columns {missing}")
        return _empty_outputs()

    work = event_log[REQUIRED_COLS].copy()
    work["case:concept:name"] = work["case:concept:name"].astype(str)
    work["concept:name"] = work["concept:name"].astype(str)
    work["time:timestamp"] = pd.to_datetime(work["time:timestamp"], errors="coerce")
    work = work.dropna(subset=["time:timestamp"]).sort_values(["case:concept:name", "time:timestamp"])  # noqa: PD002

    formatted = pm4py.format_dataframe(
        work,
        case_id="case:concept:name",
        activity_key="concept:name",
        timestamp_key="time:timestamp",
    )

    outputs = _empty_outputs()

    try:
        variants_count = pm4py.get_variants_as_tuples(formatted)
        variant_rows = []
        for variant, cnt in variants_count.items():
            variant_rows.append(
                {
                    "variant": " -> ".join(variant),
                    "variant_length": len(variant),
                    "cases": int(cnt),
                }
            )
        outputs["pm4py_variants"] = (
            pd.DataFrame(variant_rows).sort_values("cases", ascending=False).reset_index(drop=True)
            if variant_rows else pd.DataFrame()
        )
    except Exception as exc:
        print(f"pm4py variants failed: {exc}")

    try:
        dfg, starts, ends = pm4py.discover_dfg(formatted)
        dfg_rows = [
            {"source": edge[0], "target": edge[1], "frequency": int(freq)}
            for edge, freq in dfg.items()
        ]
        outputs["pm4py_dfg"] = (
            pd.DataFrame(dfg_rows).sort_values("frequency", ascending=False).reset_index(drop=True)
            if dfg_rows else pd.DataFrame()
        )

        outputs["pm4py_start_activities"] = (
            pd.DataFrame([
                {"activity": activity, "frequency": int(freq)}
                for activity, freq in starts.items()
            ]).sort_values("frequency", ascending=False).reset_index(drop=True)
            if starts else pd.DataFrame()
        )

        outputs["pm4py_end_activities"] = (
            pd.DataFrame([
                {"activity": activity, "frequency": int(freq)}
                for activity, freq in ends.items()
            ]).sort_values("frequency", ascending=False).reset_index(drop=True)
            if ends else pd.DataFrame()
        )
    except Exception as exc:
        print(f"pm4py dfg failed: {exc}")

    try:
        net, im, fm = pm4py.discover_petri_net_inductive(formatted)
        fitness = pm4py.fitness_token_based_replay(formatted, net, im, fm)
        precision = pm4py.precision_token_based_replay(formatted, net, im, fm)
        outputs["pm4py_quality"] = pd.DataFrame(
            [
                {
                    "metric": "log_fitness",
                    "value": float(fitness.get("log_fitness", 0.0)),
                },
                {
                    "metric": "average_trace_fitness",
                    "value": float(fitness.get("average_trace_fitness", 0.0)),
                },
                {
                    "metric": "precision",
                    "value": float(precision),
                },
                {
                    "metric": "traces_with_fit",
                    "value": float(fitness.get("perc_fit_traces", 0.0)),
                },
            ]
        )
    except Exception as exc:
        print(f"pm4py quality failed: {exc}")

    return outputs
