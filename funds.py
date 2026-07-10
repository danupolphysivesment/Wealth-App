"""Fund universe for the Core–Satellite builder.

Daily returns for 100 KAsset (Thai) mutual funds, shipped in
data/fund_returns.csv (converted from the advisor's "Fund Data.xlsx").
Categories are indicative, inferred from ticker naming conventions.
"""
import os
import re

import numpy as np
import pandas as pd

_DATA = os.path.join(os.path.dirname(__file__), "data", "fund_returns.csv")

CORE_COLOR = "#2F62F0"    # cobalt — the anchor
SAT_COLOR = "#E09F3E"     # amber — the speedboats
TOTAL_COLOR = "#1C2233"   # graphite — the whole portfolio

# Advisor model portfolios per risk profile — the *default* recommendation,
# fully adjustable in the app. Weights are % within each sleeve.
MODEL_PORTFOLIOS = {
    "Capital Preservation": {
        "core": {"KFIPRO": 40, "KGB": 35, "KGA": 25},
        "sat": {"KGOLD": 100},
        "core_share": 0.90,
    },
    "Conservative": {
        "core": {"KFIPRO": 30, "KGB": 30, "KGA": 40},
        "sat": {"KGOLD": 50, "KGLOBE": 50},
        "core_share": 0.85,
    },
    "Balanced": {
        "core": {"KGB": 25, "KFIPRO": 15, "KGA": 35, "KGLOBE": 25},
        "sat": {"KGOLD": 40, "KUSNDQ": 60},
        "core_share": 0.80,
    },
    "Growth": {
        "core": {"KGA": 30, "KGLOBE": 40, "KGB": 30},
        "sat": {"KUSNDQ": 40, "KGOLD": 30, "KGHEAL": 30},
        "core_share": 0.75,
    },
    "Aggressive Growth": {
        "core": {"KGLOBE": 45, "KGA": 25, "KUSA": 30},
        "sat": {"KUSNDQ": 40, "KVIET": 30, "KGOLD": 30},
        "core_share": 0.70,
    },
}

_FIXED = {"KFIPRO", "KFIXPS", "KGB", "KGDBON", "KGDBUH", "KGDRMF", "KDBRMF",
          "KAPB", "KGSFUH"}
_MULTI = {"KSGM", "KGA", "KGARMF", "KGIN", "KGIRMF"}
_TERM_RE = re.compile(r"^K[CG]\d{2}[A-Z]U$|^KTR\d{2}[A-Z]$")  # buy-&-hold term funds


def categorize(ticker: str) -> str:
    if ticker in _FIXED or _TERM_RE.match(ticker):
        return "Fixed Income & Term"
    if any(k in ticker for k in ("GOLD", "OIL", "PROP", "INFR")):
        return "Real Assets"
    if ticker.startswith("KGP"):
        return "Private Assets"
    if ticker in _MULTI or ticker.startswith(("KAL", "KPLAN", "WP", "WSP")):
        return "Multi-Asset"
    return "Equity"


def load_returns() -> pd.DataFrame:
    df = pd.read_csv(_DATA, index_col=0, parse_dates=True)
    return df.sort_index()


def sleeve_returns(rets: pd.DataFrame, weights: dict) -> pd.Series:
    """Daily returns of a fixed-weight sleeve, from the youngest fund's
    inception onward (weights renormalised to sum to 1)."""
    cols = rets[list(weights)]
    start = max(cols[c].first_valid_index() for c in cols)
    window = cols.loc[start:].fillna(0.0)
    w = np.array([weights[c] for c in window.columns], dtype=float)
    w = w / w.sum()
    return pd.Series(window.to_numpy() @ w, index=window.index)


def perf(series: pd.Series) -> dict:
    """Performance metrics robust to mixed daily/weekly spacing."""
    growth = (1 + series).cumprod()
    years = max((series.index[-1] - series.index[0]).days / 365.25, 1e-9)
    cagr = float(growth.iloc[-1] ** (1 / years) - 1)
    monthly = (1 + series).resample("ME").prod() - 1
    vol = float(monthly.std() * np.sqrt(12))
    dd = growth / growth.cummax() - 1
    annual = (1 + series).resample("YE").prod() - 1
    return {
        "Annualised return": cagr,
        "Volatility": vol,
        "Sharpe ratio": (cagr - 0.02) / vol if vol > 0 else np.nan,
        "Max drawdown": float(dd.min()),
        "Best year": float(annual.max()),
        "Worst year": float(annual.min()),
    }


def universe_table(rets: pd.DataFrame) -> pd.DataFrame:
    """One row per fund: category, inception, annualised return / vol / max DD."""
    rows = []
    for t in rets.columns:
        s = rets[t].dropna()
        if len(s) < 30:
            continue
        m = perf(s)
        rows.append({
            "Fund": t,
            "Category": categorize(t),
            "Data since": str(s.index[0].date()),
            "Ann. return": m["Annualised return"],
            "Volatility": m["Volatility"],
            "Max drawdown": m["Max drawdown"],
        })
    return (pd.DataFrame(rows)
            .sort_values(["Category", "Fund"])
            .reset_index(drop=True))
