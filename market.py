"""Asset-class capital-market data built from the app's own fund universe.

The three asset-class series are cross-sectional composites of the 100-fund
universe in data/fund_returns.csv (see funds.py):

    Equity        -> average of all Equity-category funds
    Fixed Income  -> average of Fixed Income & Term funds
    Alternatives  -> average of Real Assets + Private Assets funds

Multi-Asset funds are excluded from the composites (they are already blends);
in look-through calculations they are split via MULTI_ASSET_SPLIT.

If the fund file is unavailable, a seeded synthetic generator keeps the app
running. `MU`, `VOL`, `CORR`, `COV` are estimated from whichever history is
used.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

ASSETS = ["Equity", "Fixed Income", "Alternatives"]

BUCKET_OF_CATEGORY = {
    "Equity": "Equity",
    "Fixed Income & Term": "Fixed Income",
    "Real Assets": "Alternatives",
    "Private Assets": "Alternatives",
}
# assumed look-through split (Equity / FI / Alternatives) for Multi-Asset funds
MULTI_ASSET_SPLIT = (0.50, 0.40, 0.10)

COLORS = {
    "Equity": "#2F62F0",        # cobalt — the growth signal
    "Fixed Income": "#5E8CA8",  # cool steel-blue
    "Alternatives": "#8A93A8",  # slate grey-blue
    "Portfolio": "#1C2233",     # graphite ink — current mix
    "Recommended": "#2F62F0",   # cobalt — recommended mix
}

# --- synthetic fallback (seeded, reproducible) -----------------------------
_SYNTH_MU = np.array([0.085, 0.038, 0.062])
_SYNTH_VOL = np.array([0.16, 0.05, 0.10])
_SYNTH_CORR = np.array([
    [1.00, -0.10, 0.60],
    [-0.10, 1.00, 0.10],
    [0.60, 0.10, 1.00],
])
_SYNTH_COV = np.outer(_SYNTH_VOL, _SYNTH_VOL) * _SYNTH_CORR
_CRISES = {
    ("2008-06", "2009-02"): (-0.065, 0.004, -0.035),
    ("2009-03", "2009-12"): (0.035, 0.001, 0.015),
    ("2011-07", "2011-09"): (-0.045, 0.006, -0.020),
    ("2015-08", "2016-01"): (-0.020, 0.001, -0.010),
    ("2018-10", "2018-12"): (-0.045, 0.002, -0.020),
    ("2020-02", "2020-03"): (-0.160, 0.005, -0.070),
    ("2020-04", "2020-08"): (0.050, 0.002, 0.025),
    ("2022-01", "2022-09"): (-0.028, -0.018, -0.008),
}


def _synthetic_history(seed: int = 11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2006-01-31", "2026-05-31", freq="ME")
    rets = rng.multivariate_normal(_SYNTH_MU / 12, _SYNTH_COV / 12, size=len(dates))
    df = pd.DataFrame(rets, index=dates, columns=ASSETS)
    for (start, end), shock in _CRISES.items():
        end_ts = pd.Timestamp(end) + pd.offsets.MonthEnd(0)
        mask = (df.index >= pd.Timestamp(start)) & (df.index <= end_ts)
        df.loc[mask] = df.loc[mask] * 0.6 + np.array(shock)
    df = df + (_SYNTH_MU / 12 - df.mean(axis=0).to_numpy())
    return df


# --- composites from the fund universe --------------------------------------
def _composite_history() -> pd.DataFrame:
    import funds

    daily = funds.load_returns()
    counts = daily.notna().resample("ME").sum()
    monthly = (1 + daily.fillna(0)).resample("ME").prod() - 1
    monthly = monthly.where(counts > 0)  # months before a fund existed stay NaN

    cats = {t: funds.categorize(t) for t in monthly.columns}
    out = {}
    for asset in ASSETS:
        cols = [t for t, c in cats.items()
                if BUCKET_OF_CATEGORY.get(c) == asset]
        out[asset] = monthly[cols].mean(axis=1)
    df = pd.DataFrame(out).dropna()  # start when all three composites exist
    if len(df) > 2:
        df = df.iloc[:-1]  # drop the latest (partial) month
    return df


def _load_history() -> "tuple[pd.DataFrame, str]":
    try:
        df = _composite_history()
        if len(df) >= 36:
            return df, "fund-universe composites"
    except Exception:
        pass
    return _synthetic_history(), "synthetic (fallback)"


_HISTORY, DATA_SOURCE = _load_history()
AS_OF = str(_HISTORY.index[-1].date())
DATA_START = str(_HISTORY.index[0].date())

MU = (_HISTORY.mean(axis=0) * 12).to_numpy()
COV = (_HISTORY.cov() * 12).to_numpy()
VOL = np.sqrt(np.diag(COV))
CORR = COV / np.outer(VOL, VOL)


def monthly_history(seed: int = 11) -> pd.DataFrame:
    """Monthly asset-class returns backing the app (fund-universe composites)."""
    return _HISTORY.copy()
