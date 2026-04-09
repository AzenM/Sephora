"""Time series forecasting helpers for revenue and demand signals."""

from __future__ import annotations

import numpy as np
import pandas as pd

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False


def _monthly_customer_kpis(customer_month: pd.DataFrame) -> pd.DataFrame:
    frame = customer_month.copy()
    frame["year_month_dt"] = pd.to_datetime(frame["year_month_dt"], errors="coerce")
    frame = frame.dropna(subset=["year_month_dt"]).copy()

    kpis = (
        frame.groupby("year_month_dt")
        .agg(
            revenue=("monthly_revenue", "sum"),
            tickets=("monthly_tickets", "sum"),
            active_customers=("anonymized_card_code", "nunique"),
            avg_discount_ratio=("monthly_discount_ratio", "mean"),
        )
        .reset_index()
        .sort_values("year_month_dt")
    )
    return kpis


def _linear_forecast(values: pd.Series, periods: int = 3) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    y = values.astype(float).to_numpy()
    x = np.arange(len(y), dtype=float)

    if len(y) < 2:
        pred = np.repeat(y[-1] if len(y) else 0.0, periods)
        lower = pred
        upper = pred
        return pred, lower, upper

    coeffs = np.polyfit(x, y, deg=1)
    x_future = np.arange(len(y), len(y) + periods, dtype=float)
    pred = np.polyval(coeffs, x_future)

    fitted = np.polyval(coeffs, x)
    residual_std = float(np.std(y - fitted)) if len(y) > 2 else float(np.std(y))
    lower = pred - 1.28 * residual_std
    upper = pred + 1.28 * residual_std
    return pred, lower, upper


def _hw_forecast(values: pd.Series, periods: int = 3) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    y = values.astype(float)
    if len(y) < 6:
        return _linear_forecast(values, periods)

    model = ExponentialSmoothing(y, trend="add", seasonal=None)
    fit = model.fit(optimized=True)
    pred = fit.forecast(periods).to_numpy()

    residual_std = float(np.std(fit.resid)) if len(fit.resid) > 2 else float(np.std(y))
    lower = pred - 1.28 * residual_std
    upper = pred + 1.28 * residual_std
    return pred, lower, upper


def _forecast_one_series(
    monthly: pd.DataFrame,
    value_col: str,
    series_name: str,
    periods: int = 3,
) -> pd.DataFrame:
    base = monthly[["year_month_dt", value_col]].dropna().copy()
    base = base.rename(columns={"year_month_dt": "ds", value_col: "y"})

    if base.empty:
        return pd.DataFrame(columns=["series", "ds", "y", "forecast", "lower", "upper", "model"])

    if HAS_STATSMODELS:
        pred, lower, upper = _hw_forecast(base["y"], periods=periods)
        model_name = "holt_winters"
    else:
        pred, lower, upper = _linear_forecast(base["y"], periods=periods)
        model_name = "linear_trend"

    future_dates = pd.date_range(base["ds"].max() + pd.offsets.MonthBegin(1), periods=periods, freq="MS")
    fcst = pd.DataFrame(
        {
            "series": series_name,
            "ds": future_dates,
            "y": np.nan,
            "forecast": pred,
            "lower": lower,
            "upper": upper,
            "model": model_name,
        }
    )

    hist = base.copy()
    hist["series"] = series_name
    hist["forecast"] = np.nan
    hist["lower"] = np.nan
    hist["upper"] = np.nan
    hist["model"] = model_name
    hist = hist[["series", "ds", "y", "forecast", "lower", "upper", "model"]]

    return pd.concat([hist, fcst], ignore_index=True)


def build_time_series_forecasts(
    customer_month: pd.DataFrame,
    periods: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create monthly KPI trends and short-term forecasts.

    Returns:
        monthly_kpis: historical monthly KPI table
        forecasts: long table including history + future forecasts
        signals: compact AI-oriented signal table for actioning
    """

    monthly = _monthly_customer_kpis(customer_month)

    forecast_frames = [
        _forecast_one_series(monthly, "revenue", "revenue", periods=periods),
        _forecast_one_series(monthly, "tickets", "tickets", periods=periods),
        _forecast_one_series(monthly, "active_customers", "active_customers", periods=periods),
    ]
    forecasts = pd.concat(forecast_frames, ignore_index=True)

    signal_rows = []
    for metric in ["revenue", "tickets", "active_customers"]:
        hist = monthly[metric].dropna()
        last_val = float(hist.iloc[-1]) if len(hist) else 0.0
        fcst_metric = forecasts[(forecasts["series"] == metric) & forecasts["forecast"].notna()]
        next_val = float(fcst_metric.iloc[0]["forecast"]) if not fcst_metric.empty else last_val
        uplift = (next_val - last_val) / last_val if last_val > 0 else 0.0
        signal_rows.append(
            {
                "metric": metric,
                "last_actual": last_val,
                "next_forecast": next_val,
                "forecast_uplift_rate": uplift,
                "signal": "up" if uplift > 0.02 else ("down" if uplift < -0.02 else "flat"),
            }
        )

    signals = pd.DataFrame(signal_rows)
    return monthly, forecasts, signals
