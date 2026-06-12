"""Capital-market assumptions and synthetic historical data.

The app ships with seeded, reproducible synthetic monthly returns for the
three asset classes so it runs fully offline. Crisis-period shocks are
injected so the history exhibits realistic drawdowns (2008, 2020, 2022...).
Swap `monthly_history` for a real data feed in production.
"""
import numpy as np
import pandas as pd

ASSETS = ["Equity", "Fixed Income", "Alternatives"]

COLORS = {
    "Equity": "#6C5CE7",
    "Fixed Income": "#00B894",
    "Alternatives": "#F39C12",
    "Portfolio": "#0984E3",
    "Recommended": "#E84393",
}

# Annualised expected return / volatility per asset class
MU = np.array([0.085, 0.038, 0.062])
VOL = np.array([0.16, 0.05, 0.10])
CORR = np.array([
    [1.00, -0.10, 0.60],
    [-0.10, 1.00, 0.10],
    [0.60, 0.10, 1.00],
])
COV = np.outer(VOL, VOL) * CORR

# (start month, end month) -> additive monthly shock for (Equity, FI, Alt)
CRISES = {
    ("2008-06", "2009-02"): (-0.065, 0.004, -0.035),   # Global Financial Crisis
    ("2009-03", "2009-12"): (0.035, 0.001, 0.015),     # GFC rebound
    ("2011-07", "2011-09"): (-0.045, 0.006, -0.020),   # Euro debt crisis
    ("2015-08", "2016-01"): (-0.020, 0.001, -0.010),   # China slowdown
    ("2018-10", "2018-12"): (-0.045, 0.002, -0.020),   # Rate-hike selloff
    ("2020-02", "2020-03"): (-0.160, 0.005, -0.070),   # COVID crash
    ("2020-04", "2020-08"): (0.050, 0.002, 0.025),     # COVID rebound
    ("2022-01", "2022-09"): (-0.028, -0.018, -0.008),  # Inflation / rate shock
}


def monthly_history(seed: int = 11) -> pd.DataFrame:
    """~20 years of monthly asset-class returns ending last month."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2006-01-31", "2026-05-31", freq="ME")
    rets = rng.multivariate_normal(MU / 12, COV / 12, size=len(dates))
    df = pd.DataFrame(rets, index=dates, columns=ASSETS)
    for (start, end), shock in CRISES.items():
        end_ts = pd.Timestamp(end) + pd.offsets.MonthEnd(0)
        mask = (df.index >= pd.Timestamp(start)) & (df.index <= end_ts)
        # damp the random component and overlay the regime shock
        df.loc[mask] = df.loc[mask] * 0.6 + np.array(shock)
    # re-center so long-run means match the capital-market assumptions
    # (crisis months keep their relative depth, but the sample isn't biased bearish)
    df = df + (MU / 12 - df.mean(axis=0).to_numpy())
    return df
