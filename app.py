"""WealthLens — private-wealth portfolio advisor, monitor & educator."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import engine
import funds
import market

st.set_page_config(page_title="WealthLens", page_icon="🧭", layout="wide")

# ------------------------------------------------------------------ styling
st.markdown("""
<style>
/* Hallmark · genre: modern-minimal · macrostructure: Workbench · theme: Cobalt · enrichment: none
 * tone: precise / engineered / fintech-instrument · anchor hue: electric cobalt (oklch 58% 0.20 256)
 * redesign of the warm-cream + navy original · every colour + font references a token below */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --color-paper:       oklch(98% 0.006 256);
  --color-paper-2:     oklch(100% 0 0);
  --color-ink:         oklch(24% 0.02 258);
  --color-ink-2:       oklch(34% 0.018 257);
  --color-muted:       oklch(56% 0.012 257);
  --color-rule:        oklch(90% 0.008 256);
  --color-rule-2:      oklch(32% 0.014 260);
  --color-accent:      oklch(58% 0.20 256);
  --color-accent-ink:  oklch(99% 0.01 256);
  --color-accent-weak: oklch(58% 0.20 256 / 0.10);
  --color-focus:       oklch(58% 0.20 256);
  --color-graphite:    oklch(22% 0.016 260);
  --color-rule-graph:  oklch(32% 0.014 260 / 0.7);

  --font-display: "Space Grotesk", system-ui, sans-serif;
  --font-body:    "Inter", system-ui, sans-serif;
  --font-mono:    "JetBrains Mono", ui-monospace, monospace;

  --radius-card: 10px;
  --radius-ctl:  6px;
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
}

/* ---------- base ---------- */
html, body, .stApp, [class*="css"] { font-family: var(--font-body); }
.stApp { background: var(--color-paper); color: var(--color-ink-2); }
.block-container { padding-top: 2.2rem; max-width: 1360px; }
h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
  font-family: var(--font-display); color: var(--color-ink);
  font-weight: 600; letter-spacing: -0.02em; font-style: normal;
}
.stMarkdown p, .stMarkdown li { color: var(--color-ink-2); }
a, a:visited { color: var(--color-accent); }

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] {
  background: var(--color-paper-2); border-right: 1px solid var(--color-rule);
}
section[data-testid="stSidebar"] h2 { font-family: var(--font-display); letter-spacing: -0.02em; }
section[data-testid="stSidebar"] h3 {
  font-family: var(--font-mono); font-size: 0.72rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.08em; color: var(--color-muted);
  margin-top: 1.4rem;
}

/* ---------- hero: the one graphite band ---------- */
.hero {
  background: var(--color-graphite); border: 1px solid var(--color-rule-graph);
  border-radius: var(--radius-card); padding: 1.5rem 1.8rem; margin-bottom: 1rem;
  color: oklch(96% 0.01 256);
}
.hero .eyebrow {
  font-family: var(--font-mono); font-size: 0.72rem; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--color-accent); margin: 0 0 0.5rem;
}
.hero h1 {
  color: oklch(98% 0.01 256); font-family: var(--font-display); margin: 0;
  font-size: 1.95rem; font-weight: 600; letter-spacing: -0.025em;
}
.hero p { color: oklch(80% 0.012 256); margin: 0.45rem 0 0; font-size: 1rem; }
.hero p b { color: oklch(96% 0.01 256); font-weight: 600; }
.hero .pill {
  display: inline-block; margin-top: 0.9rem; padding: 0.3rem 0.7rem;
  font-family: var(--font-mono); font-size: 0.74rem; letter-spacing: 0.04em;
  color: var(--color-accent); background: var(--color-accent-weak);
  border: 1px solid color-mix(in oklch, var(--color-accent) 45%, transparent);
  border-radius: var(--radius-ctl);
}

/* ---------- metrics: hairline, no shadow, mono label, grotesk value ---------- */
div[data-testid="stMetric"] {
  background: var(--color-paper-2); border: 1px solid var(--color-rule);
  border-radius: var(--radius-card); padding: 0.9rem 1.05rem; box-shadow: none;
}
div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] p {
  font-family: var(--font-mono); font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.06em; color: var(--color-muted);
}
div[data-testid="stMetricValue"] {
  font-family: var(--font-display); font-weight: 600;
  letter-spacing: -0.02em; color: var(--color-ink);
  font-size: clamp(1.25rem, 1.1vw + 0.85rem, 1.6rem);
}
div[data-testid="stMetricValue"] > div { overflow: visible; }
div[data-testid="stMetricDelta"] { font-family: var(--font-mono); font-size: 0.78rem; }

/* ---------- cards: hairline + cobalt tick (no top-bar, no shadow) ---------- */
.edu-card {
  background: var(--color-paper-2); border: 1px solid var(--color-rule);
  border-left: 2px solid var(--color-accent); border-radius: var(--radius-card);
  padding: 1.1rem 1.25rem; height: 100%; box-shadow: none; margin-bottom: 1rem;
}
.edu-card .icon { font-size: 1.4rem; }
.edu-card .title {
  font-family: var(--font-display); font-weight: 600; font-size: 1.02rem;
  margin: 0.4rem 0; color: var(--color-ink); letter-spacing: -0.01em;
}
.edu-card .body { color: var(--color-ink-2); font-size: 0.92rem; line-height: 1.55; }
.edu-card .body b { color: var(--color-ink); }

/* ---------- tabs: clean strip, cobalt active ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 0.25rem; border-bottom: 1px solid var(--color-rule); }
.stTabs [data-baseweb="tab"] {
  font-family: var(--font-body); font-weight: 500; color: var(--color-muted);
  border-radius: var(--radius-ctl) var(--radius-ctl) 0 0; padding: 0.5rem 0.9rem;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] { color: var(--color-accent); }
.stTabs [data-baseweb="tab-highlight"] { background: var(--color-accent); height: 2px; }
.stTabs [data-baseweb="tab-border"] { background: transparent; }

/* ---------- buttons ---------- */
.stButton > button, .stDownloadButton > button {
  font-family: var(--font-body); font-weight: 600; border-radius: var(--radius-ctl);
  background: var(--color-accent); color: var(--color-accent-ink);
  border: 1px solid var(--color-accent);
  transition: transform 0.12s var(--ease-out), filter 0.12s var(--ease-out);
}
.stButton > button:hover { filter: brightness(1.06); transform: translateY(-1px); }
.stButton > button:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px; }

/* ---------- inputs / selects: tight radii ---------- */
input, textarea,
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="base-input"] {
  border-radius: var(--radius-ctl) !important; font-family: var(--font-body) !important;
}

/* ---------- dataframe / table: hairline ---------- */
[data-testid="stDataFrame"], [data-testid="stTable"] {
  border: 1px solid var(--color-rule); border-radius: var(--radius-card);
}

/* ---------- alerts: hairline + semantic left rule, no fill flood ---------- */
[data-testid="stAlert"] {
  border-radius: var(--radius-ctl); border: 1px solid var(--color-rule);
  border-left: 3px solid var(--color-accent); background: var(--color-paper-2);
  font-family: var(--font-body);
}

/* ---------- expander ---------- */
[data-testid="stExpander"] {
  border: 1px solid var(--color-rule); border-radius: var(--radius-card);
  background: var(--color-paper-2);
}
[data-testid="stExpander"] summary {
  font-family: var(--font-body); font-weight: 600; color: var(--color-ink);
}

/* ---------- misc ---------- */
hr { border-color: var(--color-rule); }
[data-testid="stCaptionContainer"], .stCaption, .stCaption p { color: var(--color-muted); }
::selection { background: var(--color-accent-weak); }
</style>
""", unsafe_allow_html=True)


def money(x: float) -> str:
    return f"${x:,.0f}"


def pct(x: float, d: int = 1) -> str:
    return f"{x * 100:.{d}f}%"


def style(fig: go.Figure, h: int = 380) -> go.Figure:
    fig.update_layout(
        template="plotly_white", height=h,
        margin=dict(t=80, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#1C2233", size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0,
                    font=dict(color="#43485A")),
        xaxis=dict(gridcolor="rgba(28,34,51,0.06)",
                   zerolinecolor="rgba(28,34,51,0.12)",
                   linecolor="rgba(28,34,51,0.18)"),
        yaxis=dict(gridcolor="rgba(28,34,51,0.06)",
                   zerolinecolor="rgba(28,34,51,0.12)",
                   linecolor="rgba(28,34,51,0.18)"),
    )
    if fig.layout.title.text:  # keep the title above the legend strip
        fig.update_layout(title=dict(
            yref="container", y=0.97, yanchor="top",
            font=dict(family="Space Grotesk, sans-serif", color="#1C2233", size=16)))
    return fig


def edu_card(icon: str, title: str, body: str, color: str = "#2F62F0"):
    st.markdown(
        f'<div class="edu-card" style="border-left-color:{color}">'
        f'<div class="icon">{icon}</div><div class="title">{title}</div>'
        f'<div class="body">{body}</div></div>',
        unsafe_allow_html=True,
    )


def sleeve_weight_editor(selection: list, key: str, defaults: dict = None) -> dict:
    """Editable per-fund weights within a sleeve, normalised to 100%."""
    equal = round(100 / len(selection), 1)
    df = pd.DataFrame({"Fund": selection,
                       "Weight %": [float((defaults or {}).get(f, equal))
                                    for f in selection]})
    edited = st.data_editor(
        df, key=f"{key}_{'_'.join(sorted(selection))}", hide_index=True,
        use_container_width=True,
        column_config={
            "Fund": st.column_config.TextColumn(disabled=True),
            "Weight %": st.column_config.NumberColumn(min_value=0.0, max_value=100.0,
                                                      step=5.0, format="%.1f"),
        })
    w = edited.set_index("Fund")["Weight %"].astype(float).clip(lower=0)
    if w.sum() <= 0:
        w[:] = 1.0
    return (w / w.sum()).to_dict()


# ------------------------------------------------------------------ cached data
@st.cache_data
def get_history() -> pd.DataFrame:
    return market.monthly_history()


@st.cache_data
def get_series_paths(mu_m: float, sd_m: float) -> np.ndarray:
    return engine.simulate_series_paths(mu_m, sd_m)


@st.cache_data
def get_fund_returns() -> pd.DataFrame:
    return funds.load_returns()


@st.cache_data
def get_universe_table() -> pd.DataFrame:
    return funds.universe_table(funds.load_returns())


def build_portfolio(fund_rets: pd.DataFrame, core_w: dict, sat_w: dict,
                    core_share: float) -> "dict | None":
    """Daily/monthly returns, stats and look-through mix for a core–satellite
    fund portfolio. Returns None if there isn't enough common history."""
    if not core_w:
        core_share = 0.0
    if not sat_w:
        core_share = 1.0
    core_r = funds.sleeve_returns(fund_rets, core_w) if core_w else None
    sat_r = funds.sleeve_returns(fund_rets, sat_w) if sat_w else None
    if core_r is not None and sat_r is not None:
        common = core_r.index.intersection(sat_r.index)
        daily = core_share * core_r.loc[common] + (1 - core_share) * sat_r.loc[common]
    else:
        daily = core_r if core_r is not None else sat_r
    if daily is None or len(daily) < 60:
        return None
    monthly = (1 + daily).resample("ME").prod() - 1
    if len(monthly) > 2:
        monthly = monthly.iloc[:-1]  # drop the partial current month
    eff = {t: core_share * w for t, w in core_w.items()}
    for t, w in sat_w.items():
        eff[t] = eff.get(t, 0.0) + (1 - core_share) * w
    look = {a: 0.0 for a in market.ASSETS}
    for t, w in eff.items():
        cat = funds.categorize(t)
        if cat == "Multi-Asset":
            for a, s in zip(market.ASSETS, market.MULTI_ASSET_SPLIT):
                look[a] += w * s
        else:
            look[market.BUCKET_OF_CATEGORY[cat]] += w
    return {"daily": daily, "monthly": monthly,
            "mu_m": float(monthly.mean()), "sd_m": float(monthly.std()),
            "eff": eff, "lookthrough": look}


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown("## 🧭 WealthLens")
    st.caption("Private wealth portfolio intelligence")
    st.caption(f"📈 {market.DATA_SOURCE} · 100-fund universe · as of {market.AS_OF}")
    name = st.text_input("Client name", "Alexandra Chen")
    value = st.number_input("Portfolio value (USD)", min_value=100_000,
                            max_value=1_000_000_000, value=5_000_000,
                            step=250_000, format="%d")

    st.markdown("### 🧱 Portfolio construction")
    st.caption("Build the client's portfolio from the fund universe — "
               "**every tab reads from this**.")
    fund_rets = get_fund_returns()
    universe = get_universe_table()
    label_of = dict(zip(universe["Fund"],
                        universe["Fund"] + "  ·  " + universe["Category"]))
    core_sel = st.multiselect("⚓ Core funds", list(fund_rets.columns),
                              default=["KGA", "KGB", "KGLOBE"],
                              format_func=lambda t: label_of.get(t, t))
    core_w = {}
    if core_sel:
        with st.expander("⚖️ Core weights"):
            core_w = sleeve_weight_editor(core_sel, "core_w")
    sat_sel = st.multiselect("🛰️ Satellite funds", list(fund_rets.columns),
                             default=["KUSNDQ", "KGOLD", "KVIET"],
                             format_func=lambda t: label_of.get(t, t))
    sat_w = {}
    if sat_sel:
        with st.expander("⚖️ Satellite weights"):
            sat_w = sleeve_weight_editor(sat_sel, "sat_w")
    core_share = st.slider("Core share of the portfolio (%)", 0, 100, 70,
                           help="The rest goes to satellites. 60–80% core is typical.") / 100

    st.markdown("### 📝 Risk questionnaire")
    age = st.slider("Age", 25, 85, 52)
    horizon_years = st.slider("Investment horizon (years)", 1, 30, 10)
    tolerance = st.slider("Comfort with market swings (1 = none, 10 = high)", 1, 10, 6)
    liquidity = st.selectbox("Cash needs from this portfolio",
                             ["Low", "Medium", "High"], index=0)

    score = engine.risk_score(age, horizon_years, tolerance, liquidity)
    profile = engine.profile_for_score(score)
    model = funds.MODEL_PORTFOLIOS[profile]

    st.markdown("### 🎯 Recommended portfolio")
    st.caption(f"The advisor's model for the **{profile}** profile, from the same "
               "fund universe — adjust it freely. It resets when the questionnaire "
               "changes the profile.")
    rec_core_sel = st.multiselect("⚓ Core funds (recommended)",
                                  list(fund_rets.columns), default=list(model["core"]),
                                  format_func=lambda t: label_of.get(t, t),
                                  key=f"rec_core_{profile}")
    rec_core_w = {}
    if rec_core_sel:
        with st.expander("⚖️ Core weights (recommended)"):
            rec_core_w = sleeve_weight_editor(rec_core_sel, f"rec_core_w_{profile}",
                                              defaults=model["core"])
    rec_sat_sel = st.multiselect("🛰️ Satellite funds (recommended)",
                                 list(fund_rets.columns), default=list(model["sat"]),
                                 format_func=lambda t: label_of.get(t, t),
                                 key=f"rec_sat_{profile}")
    rec_sat_w = {}
    if rec_sat_sel:
        with st.expander("⚖️ Satellite weights (recommended)"):
            rec_sat_w = sleeve_weight_editor(rec_sat_sel, f"rec_sat_w_{profile}",
                                             defaults=model["sat"])
    rec_core_share = st.slider("Core share (recommended) %", 0, 100,
                               int(model["core_share"] * 100),
                               key=f"rec_share_{profile}") / 100

# ------------------------------------------------------------------ core computations
history = get_history()

cur = build_portfolio(fund_rets, core_w, sat_w, core_share)
if cur is None:
    st.error("⚓ The current portfolio needs at least one fund with enough shared "
             "history — adjust **🧱 Portfolio construction** in the sidebar.")
    st.stop()
rec = build_portfolio(fund_rets, rec_core_w, rec_sat_w, rec_core_share)
if rec is None:
    st.error("🎯 The recommended portfolio needs at least one fund with enough "
             "shared history — adjust **🎯 Recommended portfolio** in the sidebar.")
    st.stop()

port_daily, port_monthly = cur["daily"], cur["monthly"]
mu_m, sd_m = cur["mu_m"], cur["sd_m"]
cur_mu, cur_vol = mu_m * 12, sd_m * np.sqrt(12)
current_w = cur["lookthrough"]

rec_monthly = rec["monthly"]
tgt_mu, tgt_vol = rec["mu_m"] * 12, rec["sd_m"] * np.sqrt(12)
target_w = rec["lookthrough"]

cur_paths = get_series_paths(round(mu_m, 6), round(sd_m, 6))
tgt_paths = get_series_paths(round(rec["mu_m"], 6), round(rec["sd_m"], 6))
cur_summary = engine.horizon_summary(cur_paths, value)
drifts = {a: current_w[a] - target_w[a] for a in market.ASSETS}
max_drift = max(abs(d) for d in drifts.values())

# ------------------------------------------------------------------ hero
first = name.split()[0] if name.strip() else "Your client"
st.markdown(
    f'<div class="hero">'
    f'<p class="eyebrow">WealthLens · portfolio intelligence</p>'
    f'<h1>{first}’s portfolio at a glance</h1>'
    f'<p>{money(value)} under advice &middot; {market.DATA_SOURCE} data as of {market.AS_OF}</p>'
    f'<span class="pill">Recommended profile: {profile} &middot; risk score {score}/100</span>'
    f'</div>',
    unsafe_allow_html=True,
)

tabs = st.tabs(["🏠 Overview", "🎯 Allocation Advisor", "🧱 Fund Lab · Core–Satellite",
                "🌪️ Stress Lab", "🔮 Future Paths", "📜 Track Record", "🎓 Learn"])


# ------------------------------------------------------------------ chart builders
def allocation_donut(weights: dict, title: str) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=market.ASSETS,
        values=[weights[a] for a in market.ASSETS],
        hole=0.62,
        marker=dict(colors=[market.COLORS[a] for a in market.ASSETS]),
        textinfo="label+percent", textposition="outside",
    ))
    fig.update_layout(title=title, showlegend=False)
    return style(fig, h=320)


def fan_chart(paths: np.ndarray, base_value: float, label: str) -> go.Figure:
    n = paths.shape[1]
    dates = pd.date_range(pd.Timestamp.today().normalize(), periods=n, freq="ME")
    vals = paths * base_value
    p5, p25, p50, p75, p95 = (np.percentile(vals, q, axis=0)
                              for q in (5, 25, 50, 75, 95))
    fig = go.Figure()
    for i in range(40):  # faint sample of individual futures
        fig.add_trace(go.Scatter(x=dates, y=vals[i],
                                 line=dict(width=1, color="rgba(47,98,240,0.05)"),
                                 hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=dates, y=p95, line=dict(width=0),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=dates, y=p5, fill="tonexty",
                             fillcolor="rgba(47,98,240,0.10)", line=dict(width=0),
                             name="5th–95th percentile (9 in 10 outcomes)"))
    fig.add_trace(go.Scatter(x=dates, y=p75, line=dict(width=0),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=dates, y=p25, fill="tonexty",
                             fillcolor="rgba(47,98,240,0.22)", line=dict(width=0),
                             name="25th–75th percentile (most likely zone)"))
    fig.add_trace(go.Scatter(x=dates, y=p50, name="Median path",
                             line=dict(color="#1C2233", width=3)))
    fig.add_hline(y=base_value, line_dash="dot", line_color="#8A93A8",
                  annotation_text="Today's value")
    fig.update_layout(title=f"2,500 simulated futures — {label}",
                      yaxis_tickprefix="$", yaxis_tickformat="~s")
    return style(fig, h=430)


def stress_compare_chart() -> go.Figure:
    names = list(engine.STRESS_SCENARIOS)
    cur = [engine.stress_impact(current_w, s["shocks"]) * 100
           for s in engine.STRESS_SCENARIOS.values()]
    tgt = [engine.stress_impact(target_w, s["shocks"]) * 100
           for s in engine.STRESS_SCENARIOS.values()]
    fig = go.Figure([
        go.Bar(y=names, x=cur, orientation="h", name="Your fund portfolio (look-through)",
               marker_color="#1C2233"),
        go.Bar(y=names, x=tgt, orientation="h", name=f"Recommended ({profile})",
               marker_color="#2F62F0"),
    ])
    fig.update_layout(barmode="group", xaxis_title="Portfolio impact (%)",
                      title="How each crisis would hit the portfolio")
    return style(fig, h=420)


# ================================================================== OVERVIEW
with tabs[0]:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Portfolio value", money(value))
    c2.metric("Expected return / yr", pct(cur_mu))
    c3.metric("Expected volatility", pct(cur_vol))
    c4.metric("Risk profile fit", profile)
    c5.metric("Largest allocation drift", pct(max_drift),
              delta="Rebalance advised" if max_drift > 0.05 else "Within tolerance",
              delta_color="inverse" if max_drift > 0.05 else "normal")
    st.caption(f"Return and volatility are estimated from your fund portfolio's own "
               f"track record ({len(core_w)} core + {len(sat_w)} satellite funds, "
               f"history since {port_monthly.index[0]:%b %Y}). Build or change the "
               f"portfolio in the sidebar.")

    if max_drift > 0.05:
        worst = max(drifts, key=lambda a: abs(drifts[a]))
        st.warning(f"⚠️ **Monitoring alert:** {worst} is "
                   f"{pct(abs(drifts[worst]))} {'above' if drifts[worst] > 0 else 'below'} "
                   f"your recommended target. See the **🎯 Allocation Advisor** tab "
                   f"for a rebalancing plan.")
    else:
        st.success("✅ Allocation is within ±5% of the recommended targets — no action needed.")

    col1, col2 = st.columns([1, 1.4])
    with col1:
        st.plotly_chart(allocation_donut(current_w,
                                         "Look-through asset mix (from your funds)"),
                        use_container_width=True)
    with col2:
        ten_y = cur_summary[cur_summary["Horizon"] == "10Y"].iloc[0]
        one_y = cur_summary[cur_summary["Horizon"] == "1Y"].iloc[0]
        st.markdown("#### 🔭 10-year outlook (your fund portfolio)")
        m1, m2, m3 = st.columns(3)
        m1.metric("Median outcome", money(ten_y["Median (50th)"]),
                  delta=pct(ten_y["Median (50th)"] / value - 1))
        m2.metric("If markets disappoint (5th)", money(ten_y["Pessimistic (5th)"]))
        m3.metric("If markets delight (95th)", money(ten_y["Best case (95th)"]))
        st.markdown("#### ⏱️ Shorter term")
        m4, m5, m6 = st.columns(3)
        m4.metric("1Y median", money(one_y["Median (50th)"]))
        m5.metric("1Y chance of being down", pct(one_y["Chance of loss"], 0))
        gfc = engine.STRESS_SCENARIOS["2008 Global Financial Crisis"]["shocks"]
        m6.metric("2008-style crisis impact", pct(engine.stress_impact(current_w, gfc)))
        st.caption("Numbers come from 2,500 Monte Carlo simulations and scenario "
                   "stress tests — explore the other tabs, and visit **🎓 Learn** "
                   "for plain-English explanations.")

# ================================================================== ADVISOR
with tabs[1]:
    st.markdown(f"### Your recommendation: **{profile}**")
    st.markdown(f"_{engine.PROFILE_BLURBS[profile]}_")
    with st.expander("📦 Inside the recommended portfolio — adjust it in the sidebar",
                     expanded=True):
        st.dataframe(pd.DataFrame(
            [{"Fund": t,
              "Sleeve": "⚓ Core" if t in rec_core_w else "🛰️ Satellite",
              "Category": funds.categorize(t),
              "Weight": pct(w)}
             for t, w in sorted(rec["eff"].items(), key=lambda kv: -kv[1])]),
            hide_index=True, use_container_width=True)
        st.caption(f"Seeded from the {profile} model portfolio; every fund, weight "
                   "and the core share can be changed under **🎯 Recommended "
                   "portfolio** in the sidebar — separately from the client's "
                   "current portfolio.")

    colg, colw = st.columns([1, 1.6])
    with colg:
        gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=score,
            title={"text": "Risk capacity score"},
            gauge=dict(
                axis=dict(range=[0, 100]),
                bar=dict(color="#1C2233", thickness=0.3),
                steps=[
                    dict(range=[0, 30], color="#E4E8F2"),
                    dict(range=[30, 45], color="#CFD9F0"),
                    dict(range=[45, 62], color="#AFC2F2"),
                    dict(range=[62, 78], color="#7497F2"),
                    dict(range=[78, 100], color="#2F62F0"),
                ],
            ),
        ))
        st.plotly_chart(style(gauge, h=300), use_container_width=True)
        st.caption("Built from your age, horizon, comfort with swings, and "
                   "liquidity needs. Higher score → more room for growth assets.")
    with colw:
        d1, d2 = st.columns(2)
        with d1:
            st.plotly_chart(allocation_donut(current_w, "Current (look-through)"),
                            use_container_width=True)
        with d2:
            st.plotly_chart(allocation_donut(target_w, f"Recommended · {profile}"),
                            use_container_width=True)

    st.markdown("### 🔁 Rebalancing plan")
    rows = []
    for a in market.ASSETS:
        d = drifts[a]
        dollars = -d * value
        action = "✅ Hold" if abs(d) < 0.02 else (
            f"🔴 Sell {money(-dollars)}" if dollars < 0 else f"🟢 Buy {money(dollars)}")
        rows.append({"Asset class": a, "Current": pct(current_w[a]),
                     "Target": pct(target_w[a]), "Drift": pct(d), "Action": action})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.caption("'Current' is the look-through mix of your fund portfolio: each fund "
               "counts toward its category's asset class; Multi-Asset funds are "
               "split 50 / 40 / 10 across Equity / Fixed Income / Alternatives.")

    st.markdown("### ⚖️ What following the advice changes")
    gfc = engine.STRESS_SCENARIOS["2008 Global Financial Crisis"]["shocks"]
    cur10 = float(np.percentile(cur_paths[:, 120] * value, 50))
    tgt10 = float(np.percentile(tgt_paths[:, 120] * value, 50))
    comp = pd.DataFrame({
        "Metric": ["Expected return / yr", "Expected volatility",
                   "2008-style crisis impact", "10Y median value",
                   "1Y chance of loss"],
        "Your fund portfolio": [
            pct(cur_mu), pct(cur_vol),
            pct(engine.stress_impact(current_w, gfc)),
            money(cur10),
            pct(float((cur_paths[:, 12] < 1).mean()), 0)],
        f"Recommended ({profile})": [
            pct(tgt_mu), pct(tgt_vol),
            pct(engine.stress_impact(target_w, gfc)),
            money(tgt10),
            pct(float((tgt_paths[:, 12] < 1).mean()), 0)],
    })
    st.dataframe(comp, hide_index=True, use_container_width=True)

# ================================================================== FUND LAB
with tabs[2]:
    edu_card("🧱", "Core–Satellite in one line",
             "The <b>Core</b> is the anchor: broad, steady funds holding most of the "
             "money and doing the compounding. <b>Satellites</b> are small, high-"
             "conviction side bets — themes, sectors, single countries — that try to "
             "add extra return without endangering the plan. Build both below from "
             "the 100-fund universe and compare all three track records.")

    cw1, cw2 = st.columns([1, 2.2])
    with cw1:
        lookback = st.selectbox("Analysis window", ["3Y", "5Y", "10Y", "Max"], index=1)
    with cw2:
        st.caption("The Core & Satellite funds, weights and split come from the "
                   "**sidebar** — this tab dissects that same portfolio sleeve "
                   "by sleeve. Change the sidebar and every tab updates.")

    years_back = {"3Y": 3, "5Y": 5, "10Y": 10}.get(lookback)
    window_rets = (fund_rets if years_back is None else
                   fund_rets.loc[fund_rets.index.max() - pd.DateOffset(years=years_back):])

    if not core_w or not sat_w:
        st.info("Add at least one fund to **each** sleeve in the sidebar to compare "
                "core vs satellite. With one sleeve empty, the whole portfolio is "
                "simply the other sleeve — see the other tabs.")
    else:
        core_r = funds.sleeve_returns(window_rets, core_w)
        sat_r = funds.sleeve_returns(window_rets, sat_w)
        common = core_r.index.intersection(sat_r.index)
        if len(common) < 60:
            st.warning("The selected funds share less than ~3 months of history in "
                       "this window — pick older funds or a longer window.")
        else:
            core_r, sat_r = core_r.loc[common], sat_r.loc[common]
            total_r = core_share * core_r + (1 - core_share) * sat_r
            st.caption(f"Common history for this selection: "
                       f"**{common[0].date()} → {common[-1].date()}** "
                       f"(constrained by the youngest fund and the {lookback} window).")

            mt = funds.perf(total_r)
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Whole portfolio · ann. return", pct(mt["Annualised return"]))
            k2.metric("Volatility", pct(mt["Volatility"]))
            k3.metric("Sharpe ratio", f"{mt['Sharpe ratio']:.2f}")
            k4.metric("Max drawdown", pct(mt["Max drawdown"]))

            growth = pd.DataFrame({
                "Core": (1 + core_r).cumprod(),
                "Satellite": (1 + sat_r).cumprod(),
                "Whole portfolio": (1 + total_r).cumprod(),
            }) * 100
            gfig = go.Figure([
                go.Scatter(x=growth.index, y=growth["Core"], name="Core",
                           line=dict(color=funds.CORE_COLOR, width=2)),
                go.Scatter(x=growth.index, y=growth["Satellite"], name="Satellite",
                           line=dict(color=funds.SAT_COLOR, width=2)),
                go.Scatter(x=growth.index, y=growth["Whole portfolio"],
                           name=f"Whole portfolio ({core_share:.0%} core)",
                           line=dict(color=funds.TOTAL_COLOR, width=3)),
            ])
            gfig.update_layout(title="Growth of 100 — core vs satellite vs whole portfolio",
                               yaxis_title="Indexed value")
            st.plotly_chart(style(gfig, h=420), use_container_width=True)

            cdd, csb = st.columns(2)
            with cdd:
                ddf = go.Figure()
                for nm, s, col in [("Core", core_r, funds.CORE_COLOR),
                                   ("Satellite", sat_r, funds.SAT_COLOR),
                                   ("Whole portfolio", total_r, funds.TOTAL_COLOR)]:
                    g = (1 + s).cumprod()
                    ddf.add_trace(go.Scatter(x=g.index, y=(g / g.cummax() - 1) * 100,
                                             name=nm, line=dict(color=col, width=1.8)))
                ddf.update_layout(title="Drawdowns — how deep each sleeve fell",
                                  yaxis_ticksuffix="%")
                st.plotly_chart(style(ddf, h=380), use_container_width=True)
            with csb:
                labels = (["Core", "Satellite"]
                          + list(core_w) + list(sat_w))
                parents = (["", ""]
                           + ["Core"] * len(core_w) + ["Satellite"] * len(sat_w))
                values = ([core_share, 1 - core_share]
                          + [core_share * w for w in core_w.values()]
                          + [(1 - core_share) * w for w in sat_w.values()])
                sb = go.Figure(go.Sunburst(
                    labels=labels, parents=parents, values=values,
                    branchvalues="total",
                    marker=dict(colors=[funds.CORE_COLOR, funds.SAT_COLOR]
                                + ["rgba(47,98,240,0.55)"] * len(core_w)
                                + ["rgba(224,159,62,0.6)"] * len(sat_w)),
                    texttemplate="%{label}<br>%{percentRoot:.0%}",
                    hovertemplate="%{label}: %{percentRoot:.1%} of portfolio<extra></extra>",
                ))
                sb.update_layout(title="How the portfolio is built")
                st.plotly_chart(style(sb, h=380), use_container_width=True)

            st.markdown("### 📋 Sleeve scorecard")
            mc, ms = funds.perf(core_r), funds.perf(sat_r)
            fmt2 = {"Sharpe ratio": lambda v: f"{v:.2f}"}
            st.dataframe(pd.DataFrame({
                "Metric": list(mc),
                "⚓ Core": [fmt2.get(k, pct)(v) for k, v in mc.items()],
                "🛰️ Satellite": [fmt2.get(k, pct)(v) for k, v in ms.items()],
                "🧱 Whole portfolio": [fmt2.get(k, pct)(v) for k, v in mt.items()],
            }), hide_index=True, use_container_width=True)

            contrib = {t: core_share * w * ((1 + fund_rets[t].loc[common].fillna(0)).prod() - 1)
                       for t, w in core_w.items()}
            contrib |= {t: (1 - core_share) * w * ((1 + fund_rets[t].loc[common].fillna(0)).prod() - 1)
                        for t, w in sat_w.items()}
            cs = pd.Series(contrib).sort_values()
            cfig = go.Figure(go.Bar(
                x=cs.values * 100, y=cs.index, orientation="h",
                marker_color=[funds.CORE_COLOR if t in core_w else funds.SAT_COLOR
                              for t in cs.index],
                text=[f"{v * 100:+.1f}%" for v in cs.values], textposition="outside"))
            cfig.update_layout(title="Who did the heavy lifting — contribution to total "
                                     "return (weight × fund return)",
                               xaxis_ticksuffix="%")
            st.plotly_chart(style(cfig, h=90 + 34 * len(cs)), use_container_width=True)

    with st.expander("🔎 Fund universe explorer — all 100 funds"):
        st.dataframe(
            universe, hide_index=True, use_container_width=True, height=420,
            column_config={
                "Ann. return": st.column_config.NumberColumn(format="percent"),
                "Volatility": st.column_config.NumberColumn(format="percent"),
                "Max drawdown": st.column_config.NumberColumn(format="percent"),
            })
        st.caption("Categories are indicative, inferred from fund naming conventions. "
                   "Returns are computed from each fund's full available history.")

# ================================================================== STRESS LAB
with tabs[3]:
    st.markdown("### Pick a crisis and watch what happens")
    scen_name = st.selectbox(
        "Scenario",
        list(engine.STRESS_SCENARIOS),
        format_func=lambda s: f"{engine.STRESS_SCENARIOS[s]['icon']} {s}")
    scen = engine.STRESS_SCENARIOS[scen_name]
    st.info(f"{scen['icon']} **{scen_name}** — {scen['desc']}")

    loss = engine.stress_impact(current_w, scen["shocks"])
    rec = engine.recovery_months(loss, current_w)
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Portfolio impact", pct(loss), delta=money(loss * value),
              delta_color="inverse")
    s2.metric("Value after shock", money(value * (1 + loss)))
    s3.metric("Estimated recovery", f"{rec} months" if rec else "—",
              help="Time to climb back to today's value growing at the expected return.")
    s4.metric("Recommended-mix impact", pct(engine.stress_impact(target_w, scen["shocks"])))

    contribs = [value * current_w[a] * scen["shocks"][a] for a in market.ASSETS]
    wf = go.Figure(go.Waterfall(
        x=["Today", "Equity", "Fixed Income", "Alternatives", "After shock"],
        measure=["absolute", "relative", "relative", "relative", "total"],
        y=[value, *contribs, 0],
        connector=dict(line=dict(color="#C9CFDA")),
        decreasing=dict(marker=dict(color="#D2483F")),
        increasing=dict(marker=dict(color="#2E8B6B")),
        totals=dict(marker=dict(color="#1C2233")),
    ))
    wf.update_layout(title="Where the damage comes from",
                     yaxis_tickprefix="$", yaxis_tickformat="~s")
    st.plotly_chart(style(wf, h=380), use_container_width=True)

    st.plotly_chart(stress_compare_chart(), use_container_width=True)

    with st.expander("🎛️ Build your own scenario"):
        cc1, cc2, cc3 = st.columns(3)
        ceq = cc1.slider("Equity shock %", -60, 30, -20) / 100
        cfi = cc2.slider("Fixed Income shock %", -30, 20, -5) / 100
        calt = cc3.slider("Alternatives shock %", -50, 30, -10) / 100
        custom = {"Equity": ceq, "Fixed Income": cfi, "Alternatives": calt}
        closs = engine.stress_impact(current_w, custom)
        k1, k2, k3 = st.columns(3)
        k1.metric("Portfolio impact", pct(closs), delta=money(closs * value),
                  delta_color="inverse")
        k2.metric("Value after shock", money(value * (1 + closs)))
        crec = engine.recovery_months(closs, current_w)
        k3.metric("Estimated recovery", f"{crec} months" if crec else "—")

# ================================================================== FUTURE PATHS
with tabs[4]:
    which = st.radio("Simulate with…",
                     ["Your fund portfolio", f"Recommended ({profile})"],
                     horizontal=True)
    use_paths = cur_paths if which == "Your fund portfolio" else tgt_paths
    st.caption("Both portfolios are simulated from their own realised monthly "
               "return and volatility — the recommended one is the adjustable "
               "fund portfolio in the sidebar.")

    st.plotly_chart(fan_chart(use_paths, value, which), use_container_width=True)

    st.markdown("### 📅 What the simulations say at each horizon")
    summary = engine.horizon_summary(use_paths, value)
    disp = summary.copy()
    for col in ["Pessimistic (5th)", "Cautious (25th)", "Median (50th)",
                "Optimistic (75th)", "Best case (95th)"]:
        disp[col] = disp[col].map(money)
    st.dataframe(
        disp, hide_index=True, use_container_width=True,
        column_config={"Chance of loss": st.column_config.ProgressColumn(
            "Chance of ending below today", format="percent",
            min_value=0.0, max_value=1.0)},
    )

    st.markdown("### 🔍 Zoom into one horizon")
    hz = st.select_slider("Horizon", options=list(engine.HORIZONS), value="1Y")
    m = engine.HORIZONS[hz]
    vals = use_paths[:, m] * value
    h1, h2, h3, h4 = st.columns(4)
    h1.metric(f"Median at {hz}", money(float(np.median(vals))))
    h2.metric("Chance of gain", pct(float((vals >= value).mean()), 0))
    h3.metric("1-in-20 bad case", money(float(np.percentile(vals, 5))))
    h4.metric("1-in-20 great case", money(float(np.percentile(vals, 95))))
    hist_fig = go.Figure(go.Histogram(x=vals, nbinsx=60, marker_color="#2F62F0",
                                      opacity=0.85))
    hist_fig.add_vline(x=value, line_dash="dot", line_color="#D2483F",
                       annotation_text="Today's value")
    hist_fig.update_layout(title=f"All 2,500 simulated outcomes at {hz}",
                           xaxis_tickprefix="$", xaxis_tickformat="~s",
                           yaxis_title="Number of simulations")
    st.plotly_chart(style(hist_fig, h=360), use_container_width=True)

# ================================================================== TRACK RECORD
with tabs[5]:
    start = max(port_monthly.index[0], rec_monthly.index[0])
    cur_ret = port_monthly.loc[start:]   # your fund portfolio, monthly
    tgt_ret = rec_monthly.loc[start:]    # recommended fund portfolio, monthly
    cur_growth = value * (1 + cur_ret).cumprod()
    tgt_growth = value * (1 + tgt_ret).cumprod()

    g = go.Figure([
        go.Scatter(x=cur_growth.index, y=cur_growth, name="Your fund portfolio",
                   line=dict(color=market.COLORS["Portfolio"], width=2.5)),
        go.Scatter(x=tgt_growth.index, y=tgt_growth, name=f"Recommended ({profile})",
                   line=dict(color=market.COLORS["Recommended"], width=2.5, dash="dash")),
    ])
    g.update_layout(title=f"If {money(value)} had been invested in "
                          f"{cur_ret.index[0]:%b %Y}",
                    yaxis_tickprefix="$", yaxis_tickformat="~s")
    st.plotly_chart(style(g, h=400), use_container_width=True)
    st.caption("The window starts at the youngest fund across both portfolios — "
               "both lines cover the same period for a fair comparison.")

    cur_dd = cur_growth / cur_growth.cummax() - 1
    dd_fig = go.Figure(go.Scatter(x=cur_dd.index, y=cur_dd * 100, fill="tozeroy",
                                  line=dict(color="#D2483F"), name="Drawdown"))
    dd_fig.update_layout(title="Drawdowns — how far below the previous peak (your portfolio)",
                         yaxis_ticksuffix="%")

    annual_cur = ((1 + cur_ret).resample("YE").prod() - 1) * 100
    annual_tgt = ((1 + tgt_ret).resample("YE").prod() - 1) * 100
    yr_fig = go.Figure([
        go.Bar(x=annual_cur.index.year, y=annual_cur, name="Your fund portfolio",
               marker_color=market.COLORS["Portfolio"]),
        go.Bar(x=annual_tgt.index.year, y=annual_tgt, name="Recommended",
               marker_color=market.COLORS["Recommended"]),
    ])
    yr_fig.update_layout(title="Calendar-year returns", yaxis_ticksuffix="%",
                         barmode="group")

    cdd, cyr = st.columns(2)
    with cdd:
        st.plotly_chart(style(dd_fig, h=340), use_container_width=True)
    with cyr:
        st.plotly_chart(style(yr_fig, h=340), use_container_width=True)

    st.markdown("### 📋 Performance scorecard")
    mc, mt = engine.perf_metrics(cur_ret), engine.perf_metrics(tgt_ret)
    fmt = {"Sharpe ratio": lambda v: f"{v:.2f}"}
    score_df = pd.DataFrame({
        "Metric": list(mc),
        "Your fund portfolio": [fmt.get(k, pct)(v) for k, v in mc.items()],
        f"Recommended ({profile})": [fmt.get(k, pct)(v) for k, v in mt.items()],
    })
    st.dataframe(score_df, hide_index=True, use_container_width=True)
    st.caption("Both portfolios are core–satellite fund selections from the same "
               "100-fund universe (sidebar). Monthly rebalancing assumed; past "
               "performance never guarantees future results.")

# ================================================================== LEARN
with tabs[6]:
    st.markdown("## 🎓 Understand every number you just saw")
    st.caption("No jargon. Each card explains one concept from the other tabs.")

    st.markdown("#### Your money lives in three buckets")
    b1, b2, b3 = st.columns(3)
    with b1:
        edu_card("📈", "Equity — the engine",
                 "Shares of companies. Highest long-run growth, biggest swings along "
                 "the way. This is what makes the portfolio <b>grow</b>.",
                 market.COLORS["Equity"])
    with b2:
        edu_card("🛡️", "Fixed Income — the seatbelt",
                 "Bonds: loans to governments and companies that pay steady interest. "
                 "They usually hold their value when stocks fall. This is what keeps "
                 "you <b>safe</b>.", market.COLORS["Fixed Income"])
    with b3:
        edu_card("🏛️", "Alternatives — the spice",
                 "Real estate, private markets, commodities, hedge strategies. They "
                 "move to their own rhythm, which smooths the overall ride. This is "
                 "what makes the mix <b>resilient</b>.", market.COLORS["Alternatives"])

    st.markdown("#### The big ideas behind the dashboard")
    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        edu_card("🥚", "Diversification",
                 "Don't put all eggs in one basket. Because the three buckets rarely "
                 "fall together, mixing them gives you <b>most of the return with "
                 "much less of the pain</b> — see the chart below.")
    with r1c2:
        edu_card("💓", "Volatility",
                 "The 'bumpiness' of the ride. A volatility of 12% means a typical "
                 "year ends within ±12% of the expected path. <b>More volatility = "
                 "wider fan</b> in Future Paths.")
    with r1c3:
        edu_card("🌊", "Drawdown",
                 "How far you are below your highest point, peak-to-trough. A 30% "
                 "drawdown needs a <b>43% gain</b> just to break even — which is why "
                 "we manage downside first.")
    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1:
        edu_card("🌦️", "The fan chart = a weather forecast",
                 "Nobody knows the exact future, so we simulate 2,500 of them. The "
                 "dark band holds the middle half of outcomes; the light band holds "
                 "9 out of 10. The median is the 'most typical' future — <b>not a "
                 "promise</b>.")
    with r2c2:
        edu_card("🏗️", "Stress test = earthquake-proofing",
                 "Engineers shake a building's design before it's built. The Stress "
                 "Lab replays famous crises against <i>your</i> mix so a 2008-style "
                 "shock is a <b>known quantity, not a surprise</b>.")
    with r2c3:
        edu_card("✂️", "Rebalancing = a regular haircut",
                 "Winners grow until they dominate the portfolio and quietly raise "
                 "your risk. Trimming back to target <b>locks in gains and keeps risk "
                 "where you chose it</b> — that's the drift alert on the Overview.")
    r3c1, r3c2, r3c3 = st.columns(3)
    with r3c1:
        edu_card("⚓", "Core = the ship",
                 "60–80% of the money in broad, diversified, low-drama funds. Its "
                 "only job is to <b>compound quietly for decades</b> and keep the "
                 "whole plan on course.", funds.CORE_COLOR)
    with r3c2:
        edu_card("🛰️", "Satellite = the speedboats",
                 "Small, deliberate side bets — a tech theme, gold, Vietnam — each "
                 "too small to sink the ship if it fails, but big enough to "
                 "<b>add meaningful return if the idea works</b>.", funds.SAT_COLOR)
    with r3c3:
        edu_card("🧱", "Why split core & satellite?",
                 "It gives your conviction a <b>budget</b>. The Fund Lab shows each "
                 "sleeve's track record separately, so you can see whether the "
                 "satellites actually earned their keep — or just added noise.",
                 funds.TOTAL_COLOR)

    st.markdown("#### Seeing is believing")
    ch1, ch2 = st.columns(2)
    with ch1:
        eq_growth = (1 + history["Equity"]).cumprod()
        mix_ret = engine.backtest({"Equity": .5, "Fixed Income": .35,
                                   "Alternatives": .15}, history)
        mix_growth = (1 + mix_ret).cumprod()
        div_fig = go.Figure([
            go.Scatter(x=eq_growth.index, y=eq_growth, name="100% Equity",
                       line=dict(color=market.COLORS["Equity"])),
            go.Scatter(x=mix_growth.index, y=mix_growth, name="Balanced 50/35/15",
                       line=dict(color=market.COLORS["Fixed Income"], width=2.5)),
        ])
        div_fig.update_layout(title="Diversification: similar destination, calmer journey",
                              yaxis_title="Growth of $1")
        st.plotly_chart(style(div_fig, h=330), use_container_width=True)
        st.caption("The balanced mix dodged the worst of every crash yet kept most "
                   "of the growth.")
    with ch2:
        loss_fig = go.Figure(go.Bar(
            x=cur_summary["Horizon"], y=cur_summary["Chance of loss"] * 100,
            marker_color="#2F62F0",
            text=[f"{v:.0f}%" for v in cur_summary["Chance of loss"] * 100],
            textposition="outside"))
        loss_fig.update_layout(title="Time is your best friend: chance of being below "
                                     "today's value", yaxis_ticksuffix="%",
                               yaxis_range=[0, 60])
        st.plotly_chart(style(loss_fig, h=330), use_container_width=True)
        st.caption("From your own simulations: the longer you stay invested, the "
                   "smaller the chance of loss.")

    dd = eq_growth / eq_growth.cummax() - 1
    trough = dd.idxmin()
    peak = eq_growth.loc[:trough].idxmax()
    after = eq_growth.loc[trough:]
    rec_idx = after[after >= eq_growth.loc[peak]].index
    anat = go.Figure(go.Scatter(x=eq_growth.index, y=eq_growth, name="Equity",
                                line=dict(color=market.COLORS["Equity"])))
    anat.add_trace(go.Scatter(x=[peak], y=[eq_growth.loc[peak]], mode="markers+text",
                              text=["Peak 🏔️"], textposition="top center",
                              marker=dict(size=11, color="#2E8B6B"), showlegend=False))
    anat.add_trace(go.Scatter(x=[trough], y=[eq_growth.loc[trough]], mode="markers+text",
                              text=[f"Trough 🕳️ ({dd.min():.0%})"],
                              textposition="bottom center",
                              marker=dict(size=11, color="#D2483F"), showlegend=False))
    if len(rec_idx):
        anat.add_trace(go.Scatter(x=[rec_idx[0]], y=[eq_growth.loc[rec_idx[0]]],
                                  mode="markers+text", text=["Recovered 🎉"],
                                  textposition="top center",
                                  marker=dict(size=11, color="#2F62F0"),
                                  showlegend=False))
    anat.update_layout(title="Anatomy of a drawdown (worst equity episode in the data)",
                       yaxis_title="Growth of $1")
    st.plotly_chart(style(anat, h=340), use_container_width=True)

    with st.expander("📖 Glossary — every term on this dashboard"):
        st.dataframe(pd.DataFrame([
            ["Median (50th percentile)", "Half the simulated futures end above this value, half below."],
            ["5th / 95th percentile", "The 1-in-20 bad and 1-in-20 great outcomes — the realistic edges, not the absolute extremes."],
            ["Expected return", "The average yearly growth rate we assume for the mix, before any single year's luck."],
            ["Volatility", "Typical size of yearly swings around the expected path."],
            ["Sharpe ratio", "Return earned per unit of risk taken. Above ~0.5 is solid for a diversified portfolio."],
            ["Max drawdown", "The single worst peak-to-trough fall in the period."],
            ["CAGR / annualised return", "The single steady yearly rate that would produce the same end value."],
            ["Drift", "How far an asset class has wandered from its target weight."],
            ["Monte Carlo simulation", "Rolling the dice thousands of times with realistic market behaviour to map possible futures."],
            ["Stress test", "Applying a historical or hypothetical crisis to today's portfolio to estimate the hit."],
            ["Core–Satellite", "Most of the portfolio in broad, steady funds (core) plus small high-conviction bets (satellites) with a fixed risk budget."],
            ["Contribution to return", "Each fund's weight × its return — how much of the portfolio's result that fund personally delivered."],
        ], columns=["Term", "Plain-English meaning"]),
            hide_index=True, use_container_width=True)

st.markdown("---")
st.caption(f"⚠️ WealthLens is an illustrative analytics tool. All analytics are built "
           f"from the same 100-fund universe (daily fund returns, {market.DATA_START} "
           f"→ {market.AS_OF}); asset classes use {market.DATA_SOURCE}. It is not "
           "investment advice; consult your advisor before acting on any output.")
