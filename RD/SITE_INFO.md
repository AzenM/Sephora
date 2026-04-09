
```powershell
py -3 -m streamlit run RD\streamlit_app.py
```

Local URL:

```text
http://127.0.0.1:8501
```

## Main screens

- `Executive Overview`
- `Journey Explorer`
- `Transition Engine`
- `First Purchase Lab`
- `Action Center`

## Business outputs now available

- Priority action plan with owners, KPIs, time window, and value pool
- Journey-level decisions: scale / fix / stop / monitor
- Transition playbook with recommended commercial response
- KPI audit table with explicit formulas and samples
- Acquisition cohort decisions for first-purchase strategy
- CRM briefs with trigger, channel, offer strategy, and message angle
- Audience samples for protect / reactivate / accelerate / recover-margin actions
- Export pack generation to `output/RD_product_pack/` with HTML figures, CSV tables, and deep dives

## Data dependencies

The Streamlit app reads the precomputed artifacts in:

```text
RD/data/processed/
```

Key inputs loaded by `data_loader.py`:

- `customers.parquet`
- `first_purchase_cohort_summary.parquet`
- `journey_paths.parquet`
- `journey_variants.parquet`
- `event_log.parquet`
- `transitions_rfm.parquet`
- `transitions_category.parquet`
- `matrix_rfm.parquet`
- `retention_curves.parquet`
- `path_scores.parquet`
- `anomalies.parquet`
- `feature_importance.parquet`
- `cox_summary.parquet`
- `km_by_channel.parquet`

## Refreshing the data

If the app says data is not ready:

```powershell
py -3 RD\prepare_data.py
```

## Output pack

Use the sidebar button in Streamlit to generate the product pack, or run the export script directly:

```powershell
py -3 RD\export_pack.py
```
