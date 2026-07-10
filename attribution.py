"""Performance & risk attribution vs a traditional 60/40 benchmark
(60% MSCI ACWI world equity + 40% global aggregate bonds, monthly rebalanced).

The Brinson-style decomposition here is exactly additive every month:

    portfolio return − benchmark return = Σ allocation effects + Σ selection effects

Conventions per attribution class:
- Equity          : allocation = (w − 60%) × (ACWI − 60/40);  selection = w × (class − ACWI)
- Fixed Income    : allocation = (w − 40%) × (GlobalAgg − 60/40); selection = w × (class − GlobalAgg)
- Alternatives    : off-benchmark bet → everything is allocation: w × (class − 60/40)
- Multi-Asset     : balanced funds are benchmarked to the 60/40 itself →
                    everything is selection: w × (class − 60/40)
(Selection includes the interaction term, i.e. it uses portfolio weights.)
"""
import os

import numpy as np
import pandas as pd

import funds

_BENCH_FILE = os.path.join(os.path.dirname(__file__), "data", "benchmark_returns.csv")

EQ_COL = "World Equity (ACWI)"
FI_COL = "Global Bonds (Global Agg)"
BENCH_W = {"Equity": 0.60, "Fixed Income": 0.40}

CLASS_OF_CATEGORY = {
    "Equity": "Equity",
    "Fixed Income & Term": "Fixed Income",
    "Real Assets": "Alternatives",
    "Private Assets": "Alternatives",
    "Multi-Asset": "Multi-Asset",
}
CLASSES = ["Equity", "Fixed Income", "Alternatives", "Multi-Asset"]
CLASS_COLORS = {"Equity": "#2F62F0", "Fixed Income": "#5E8CA8",
                "Alternatives": "#E09F3E", "Multi-Asset": "#8A5CC7"}


def load_benchmark() -> pd.DataFrame:
    return pd.read_csv(_BENCH_FILE, index_col=0, parse_dates=True).sort_index()


def class_breakdown(fund_rets: pd.DataFrame, eff_w: dict):
    """Monthly return series and total weight per attribution class."""
    groups = {}
    for t, w in eff_w.items():
        if w <= 0:
            continue
        cls = CLASS_OF_CATEGORY[funds.categorize(t)]
        groups.setdefault(cls, {})[t] = w
    rets, weights = {}, {}
    for cls, sub in groups.items():
        daily = funds.sleeve_returns(fund_rets, sub)
        rets[cls] = (1 + daily).resample("ME").prod() - 1
        weights[cls] = sum(sub.values())
    df = pd.DataFrame(rets).dropna()
    if len(df) > 2:
        df = df.iloc[:-1]  # drop the partial current month
    total = sum(weights.values())
    weights = {c: w / total for c, w in weights.items()}
    return df, weights


def attribute(class_rets: pd.DataFrame, class_w: dict,
              bench: pd.DataFrame) -> dict:
    """Monthly Brinson-style effects vs the 60/40 (exactly additive)."""
    idx = class_rets.index.intersection(bench.index)
    cr, b = class_rets.loc[idx], bench.loc[idx]
    r_eq, r_fi = b[EQ_COL], b[FI_COL]
    r_b = BENCH_W["Equity"] * r_eq + BENCH_W["Fixed Income"] * r_fi
    port = sum(class_w[c] * cr[c] for c in cr.columns)

    alloc, sel = {}, {}
    zero = pd.Series(0.0, index=idx)
    for c in cr.columns:
        w = class_w[c]
        if c == "Equity":
            alloc[c] = (w - BENCH_W["Equity"]) * (r_eq - r_b)
            sel[c] = w * (cr[c] - r_eq)
        elif c == "Fixed Income":
            alloc[c] = (w - BENCH_W["Fixed Income"]) * (r_fi - r_b)
            sel[c] = w * (cr[c] - r_fi)
        elif c == "Alternatives":
            alloc[c] = w * (cr[c] - r_b)
            sel[c] = zero
        else:  # Multi-Asset
            alloc[c] = zero
            sel[c] = w * (cr[c] - r_b)
    # benchmark classes the portfolio doesn't hold at all: pure underweight
    for c, wb in BENCH_W.items():
        if c not in cr.columns:
            rb_c = r_eq if c == "Equity" else r_fi
            alloc[c] = (0.0 - wb) * (rb_c - r_b)
            sel[c] = zero
    return {
        "port": port, "bench": r_b, "eq": r_eq, "fi": r_fi,
        "alloc": pd.DataFrame(alloc), "sel": pd.DataFrame(sel),
        "class_rets": cr,
    }


def beta_stats(port: pd.Series, bench: pd.Series) -> dict:
    """Regression of portfolio on benchmark (monthly), annualised figures."""
    beta = float(np.cov(port, bench)[0, 1] / np.var(bench, ddof=1))
    alpha_ann = float((port.mean() - beta * bench.mean()) * 12)
    r2 = float(np.corrcoef(port, bench)[0, 1] ** 2)
    active = port - bench
    te = float(active.std() * np.sqrt(12))
    ir = float(active.mean() * 12 / te) if te > 0 else np.nan
    return {"beta": beta, "alpha_ann": alpha_ann, "r2": r2,
            "tracking_error": te, "info_ratio": ir}


def risk_contribution(class_rets: pd.DataFrame, class_w: dict,
                      port: pd.Series, bench: pd.Series) -> dict:
    """% of portfolio variance from each class, plus systematic vs specific."""
    var_p = float(port.var(ddof=1))
    contrib = {}
    for c in class_rets.columns:
        cov = float(np.cov(class_rets[c], port)[0, 1])
        contrib[c] = class_w[c] * cov / var_p
    beta = float(np.cov(port, bench)[0, 1] / np.var(bench, ddof=1))
    systematic = beta ** 2 * float(bench.var(ddof=1)) / var_p
    return {"by_class": contrib,
            "systematic": min(systematic, 1.0),
            "specific": max(1.0 - systematic, 0.0)}
