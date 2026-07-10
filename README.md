# 🧭 WealthLens

A private-wealth portfolio dashboard built in pure Python (Streamlit + Plotly).

## Features
- **🏠 Overview** — portfolio value, expected return/risk, drift monitoring alerts
- **🎯 Allocation Advisor** — risk questionnaire → score gauge → recommended
  Equity / Fixed Income / Alternatives mix, with a dollar-level rebalancing plan
- **🧱 Fund Lab · Core–Satellite** — build a portfolio from a 100-fund universe
  (daily returns since 2002), split it into a Core sleeve and Satellite sleeve,
  and compare performance of core, satellite, and the whole portfolio:
  growth, drawdowns, sunburst composition, scorecard, return contribution
- **🌪️ Stress Lab** — replay 2008, COVID, 2022 rate shock & more (plus a
  build-your-own scenario), with damage waterfall and recovery estimates
- **🔮 Future Paths** — 2,500 Monte Carlo simulations; fan chart and outcome
  table at 1M / 3M / 6M / 1Y / 3Y / 5Y / 10Y horizons
- **📜 Track Record** — 20-year backtest: growth, drawdowns, calendar-year
  returns, performance scorecard
- **🧮 Attribution** — source of risk and return vs a traditional 60/40
  benchmark (60% MSCI ACWI + 40% global aggregate bonds): beta / alpha /
  tracking error, exactly-additive allocation & selection effects (waterfall,
  by asset class, cumulative), and risk contribution by class with the
  market-driven vs portfolio-specific split
- **📡 Market Pulse** — what the financial world is searching for right now
  (Google Trends): a "running hot" momentum chart, 12-month search-interest
  series per theme, and advisor-curated cards explaining each theme and what
  it means for the client's portfolio
- **🎓 Learn** — plain-English infographic cards and charts explaining every
  concept on the dashboard, plus a glossary

## Run it locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

## Deploy to Streamlit Community Cloud (free)

This folder is self-contained and ready to deploy. Make **this folder** the root
of a GitHub repo (so `app.py` and `requirements.txt` sit at the repo root):

```bash
cd wealthlens
git init && git add -A && git commit -m "WealthLens Streamlit app"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

Then:
1. Go to **https://share.streamlit.io** and sign in with GitHub.
2. **Create app** → pick your repo + branch `main`.
3. Set **Main file path** to `app.py`.
4. **Deploy**. Streamlit installs `requirements.txt` and gives you a public URL.

No secrets or API keys are required.

## Notes
- **Everything runs on one universe**: 100 KAsset Thai mutual funds (daily
  returns since 2002) shipped in `data/fund_returns.csv`, converted from the
  advisor's `Fund Data.xlsx`. The client portfolio is built in the sidebar
  (Core / Satellite funds + weights + split) and drives every tab.
- **The recommended portfolio is a fund portfolio too**, and adjustable
  separately from the client's: the risk questionnaire picks a per-profile
  model portfolio (`MODEL_PORTFOLIOS` in `funds.py`) as the default, and the
  sidebar's "Recommended portfolio" section lets the advisor swap funds,
  weights, and the core share. It resets when the profile changes.
- The Equity / Fixed Income / Alternatives series are **composites of that
  same universe** (category averages; Multi-Asset funds are excluded from
  composites and split 50/40/10 in look-through). See `market.py`. A seeded
  synthetic series is the fallback if the fund file is missing.
- Fund loading, categorisation, and sleeve analytics live in `funds.py`;
  categories are indicative, inferred from ticker naming conventions.
- The attribution benchmark ships in `data/benchmark_returns.csv`: monthly USD
  total returns of ACWI (world equity) and a global aggregate bond series
  (AGGG.L spliced with AGG before 2018), fetched once via yfinance — no
  runtime network needed. Attribution math lives in `attribution.py`.
- Market Pulse is a snapshot: search-interest series in
  `data/market_pulse_trends.csv` (refresh with
  `scripts/refresh_market_pulse.py`, needs `pytrends`) and advisor-curated
  theme cards in `data/market_pulse.json` (edit by hand, update `as_of`).
- Analytics live in `engine.py` (profiling, Monte Carlo, stress, backtest);
  the UI lives in `app.py`.
- Illustrative / educational tool only — not investment advice.
