# 🧭 WealthLens

A private-wealth portfolio dashboard built in pure Python (Streamlit + Plotly).

## Features
- **🏠 Overview** — portfolio value, expected return/risk, drift monitoring alerts
- **🎯 Allocation Advisor** — risk questionnaire → score gauge → recommended
  Equity / Fixed Income / Alternatives mix, with a dollar-level rebalancing plan
- **🌪️ Stress Lab** — replay 2008, COVID, 2022 rate shock & more (plus a
  build-your-own scenario), with damage waterfall and recovery estimates
- **🔮 Future Paths** — 2,500 Monte Carlo simulations; fan chart and outcome
  table at 1M / 3M / 6M / 1Y / 3Y / 5Y / 10Y horizons
- **📜 Track Record** — 20-year backtest: growth, drawdowns, calendar-year
  returns, performance scorecard
- **🎓 Learn** — plain-English infographic cards and charts explaining every
  concept on the dashboard, plus a glossary

## Run it

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

## Notes
- Market data is **synthetic and seeded** (see `market.py`) so the app runs
  offline and reproducibly; crisis periods are injected for realism. Swap in a
  real data feed for production use.
- Analytics live in `engine.py` (profiling, Monte Carlo, stress, backtest);
  the UI lives in `app.py`.
- Illustrative tool only — not investment advice.
