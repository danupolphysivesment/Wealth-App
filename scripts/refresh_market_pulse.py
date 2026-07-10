"""Refresh the Market Pulse search-interest data (data/market_pulse_trends.csv).

Usage:  .venv/bin/pip install pytrends
        .venv/bin/python scripts/refresh_market_pulse.py

Pulls each term separately so every series is on its own 0-100 scale.
The editorial cards in data/market_pulse.json are curated by the advisor —
update the text (and "as_of") by hand when refreshing.
"""
import json
import os
import time

import pandas as pd
from pytrends.request import TrendReq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PULSE_JSON = os.path.join(ROOT, "data", "market_pulse.json")
OUT_CSV = os.path.join(ROOT, "data", "market_pulse_trends.csv")

with open(PULSE_JSON) as f:
    terms = [t["term"] for t in json.load(f)["topics"]]

pt = TrendReq(hl="en-US", tz=0)
out = {}
for term in terms:
    for attempt in range(4):
        try:
            pt.build_payload([term], timeframe="today 12-m", geo="")
            out[term] = pt.interest_over_time()[term]
            print(f"{term}: ok")
            break
        except Exception as exc:
            print(f"{term}: retry ({exc})")
            time.sleep(8)
    time.sleep(2)

df = pd.DataFrame(out).iloc[:-1]  # drop the partial current week
df.index.name = "Week"
df.to_csv(OUT_CSV)
print(f"saved {df.shape} -> {OUT_CSV}")
