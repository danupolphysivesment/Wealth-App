"""Portfolio analytics: risk profiling, Monte Carlo simulation, stress tests,
and historical performance metrics."""
import numpy as np
import pandas as pd

import market

RF = 0.02  # risk-free rate used for Sharpe

HORIZONS = {"1M": 1, "3M": 3, "6M": 6, "1Y": 12, "3Y": 36, "5Y": 60, "10Y": 120}

RISK_PROFILES = {
    "Capital Preservation": {"Equity": 0.15, "Fixed Income": 0.70, "Alternatives": 0.15},
    "Conservative":         {"Equity": 0.30, "Fixed Income": 0.55, "Alternatives": 0.15},
    "Balanced":             {"Equity": 0.50, "Fixed Income": 0.35, "Alternatives": 0.15},
    "Growth":               {"Equity": 0.65, "Fixed Income": 0.20, "Alternatives": 0.15},
    "Aggressive Growth":    {"Equity": 0.80, "Fixed Income": 0.08, "Alternatives": 0.12},
}

PROFILE_BLURBS = {
    "Capital Preservation": "Priority #1 is protecting what you have. Most of the portfolio sits in high-quality bonds; equities are a small growth kicker.",
    "Conservative": "Steady income with modest growth. Bonds anchor the portfolio while a measured equity sleeve fights inflation.",
    "Balanced": "The classic middle path — enough equity to grow meaningfully, enough bonds to soften the bumps.",
    "Growth": "Long-term growth is the goal. Equities lead, with bonds and alternatives as shock absorbers.",
    "Aggressive Growth": "Maximum long-term growth. You accept large swings along the way in exchange for the highest expected outcome.",
}


# ---------------------------------------------------------------- profiling
def risk_score(age: int, horizon_years: int, tolerance: int, liquidity_need: str) -> int:
    """Composite 0-100 risk capacity score from the questionnaire."""
    age_pts = float(np.clip((65 - age) * 0.75, 0, 30))          # up to 30
    horizon_pts = min(25.0, horizon_years * 2.5)                # up to 25
    tol_pts = tolerance * 3.5                                   # up to 35
    liq_pts = {"Low": 10.0, "Medium": 5.0, "High": 0.0}[liquidity_need]
    return int(round(age_pts + horizon_pts + tol_pts + liq_pts))


def profile_for_score(score: int) -> str:
    if score < 30:
        return "Capital Preservation"
    if score < 45:
        return "Conservative"
    if score < 62:
        return "Balanced"
    if score < 78:
        return "Growth"
    return "Aggressive Growth"


def stats(weights: dict) -> tuple:
    """(expected annual return, annual volatility) for a weights dict."""
    w = np.array([weights[a] for a in market.ASSETS])
    return float(w @ market.MU), float(np.sqrt(w @ market.COV @ w))


# ---------------------------------------------------------------- simulation
def simulate_unit_paths(weights: dict, months: int = 120, n_sims: int = 2500,
                        seed: int = 42) -> np.ndarray:
    """Monte Carlo growth paths of $1, monthly rebalanced. Shape (n_sims, months+1)."""
    rng = np.random.default_rng(seed)
    w = np.array([weights[a] for a in market.ASSETS])
    rets = rng.multivariate_normal(market.MU / 12, market.COV / 12,
                                   size=(n_sims, months))
    port = rets @ w
    paths = np.cumprod(1.0 + port, axis=1)
    return np.concatenate([np.ones((n_sims, 1)), paths], axis=1)


def horizon_summary(paths: np.ndarray, value: float) -> pd.DataFrame:
    rows = []
    for label, m in HORIZONS.items():
        v = paths[:, m] * value
        rows.append({
            "Horizon": label,
            "Pessimistic (5th)": float(np.percentile(v, 5)),
            "Cautious (25th)": float(np.percentile(v, 25)),
            "Median (50th)": float(np.percentile(v, 50)),
            "Optimistic (75th)": float(np.percentile(v, 75)),
            "Best case (95th)": float(np.percentile(v, 95)),
            "Chance of loss": float((v < value).mean()),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- stress
STRESS_SCENARIOS = {
    "2008 Global Financial Crisis": {
        "icon": "🏦",
        "shocks": {"Equity": -0.50, "Fixed Income": 0.07, "Alternatives": -0.28},
        "desc": "A severe banking crisis freezes credit markets. Equities roughly halve, while high-quality bonds rally as investors flee to safety.",
    },
    "2020 Pandemic Crash": {
        "icon": "🦠",
        "shocks": {"Equity": -0.34, "Fixed Income": 0.03, "Alternatives": -0.12},
        "desc": "A global shutdown triggers the fastest bear market in history. Sharp, deep — but historically followed by a rapid rebound.",
    },
    "2022 Inflation & Rate Shock": {
        "icon": "📈",
        "shocks": {"Equity": -0.25, "Fixed Income": -0.15, "Alternatives": -0.08},
        "desc": "Central banks hike aggressively to fight inflation. Unusually, stocks AND bonds fall together — diversification within them helps less.",
    },
    "Tech Bubble Burst": {
        "icon": "💻",
        "shocks": {"Equity": -0.45, "Fixed Income": 0.10, "Alternatives": -0.15},
        "desc": "Overvalued growth stocks correct sharply over an extended period while bonds provide strong shelter.",
    },
    "Stagflation": {
        "icon": "🛢️",
        "shocks": {"Equity": -0.30, "Fixed Income": -0.18, "Alternatives": 0.05},
        "desc": "Stagnant growth plus persistent inflation hurts stocks and bonds alike; real assets in the alternatives sleeve hold up best.",
    },
    "Geopolitical Shock": {
        "icon": "🌍",
        "shocks": {"Equity": -0.15, "Fixed Income": 0.05, "Alternatives": -0.05},
        "desc": "A sudden conflict or trade rupture knocks risk assets; the flight to safety lifts government bonds.",
    },
}


def stress_impact(weights: dict, shocks: dict) -> float:
    """Portfolio return under an instantaneous scenario shock."""
    return float(sum(weights[a] * shocks[a] for a in market.ASSETS))


def recovery_months(loss_pct: float, weights: dict) -> int:
    """Months to climb back to the pre-shock value at the expected return."""
    if loss_pct >= 0:
        return 0
    mu_m = stats(weights)[0] / 12
    return int(np.ceil(np.log(1.0 / (1.0 + loss_pct)) / np.log(1.0 + mu_m)))


# ---------------------------------------------------------------- history
def backtest(weights: dict, history: pd.DataFrame) -> pd.Series:
    """Monthly portfolio returns for fixed weights (monthly rebalanced)."""
    w = pd.Series(weights)[history.columns]
    return history.mul(w, axis=1).sum(axis=1)


def perf_metrics(port: pd.Series) -> dict:
    growth = (1 + port).cumprod()
    years = len(port) / 12
    cagr = float(growth.iloc[-1] ** (1 / years) - 1)
    vol = float(port.std() * np.sqrt(12))
    dd = growth / growth.cummax() - 1
    annual = (1 + port).resample("YE").prod() - 1
    return {
        "Annualised return": cagr,
        "Volatility": vol,
        "Sharpe ratio": (cagr - RF) / vol,
        "Max drawdown": float(dd.min()),
        "Best year": float(annual.max()),
        "Worst year": float(annual.min()),
    }
