"""WealthLens — private-wealth portfolio advisor, monitor & educator."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import engine
import market

st.set_page_config(page_title="WealthLens", page_icon="🧭", layout="wide")

# ------------------------------------------------------------------ styling
st.markdown("""
<style>
.hero {
  background: linear-gradient(120deg, #6C5CE7 0%, #0984E3 100%);
  border-radius: 18px; padding: 1.6rem 2rem; margin-bottom: .8rem; color: white;
}
.hero h1 { color: white; margin: 0; font-size: 2.1rem; }
.hero p  { color: rgba(255,255,255,.88); margin: .25rem 0 0; font-size: 1.05rem; }
.edu-card {
  background: white; border-radius: 16px; padding: 1.1rem 1.3rem;
  box-shadow: 0 2px 14px rgba(45,52,84,.08); height: 100%;
  border-top: 4px solid #6C5CE7; margin-bottom: 1rem;
}
.edu-card .icon { font-size: 1.9rem; }
.edu-card .title { font-weight: 700; font-size: 1.05rem; margin: .25rem 0 .35rem; }
.edu-card .body { color: #555; font-size: .92rem; line-height: 1.45; }
.pill {
  display: inline-block; background: rgba(255,255,255,.18); border-radius: 999px;
  padding: .25rem .8rem; margin-top: .6rem; font-size: .85rem; color: white;
}
div[data-testid="stMetric"] {
  background: white; border-radius: 14px; padding: .8rem 1rem;
  box-shadow: 0 2px 10px rgba(45,52,84,.07);
}
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
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
    )
    if fig.layout.title.text:  # keep the title above the legend strip
        fig.update_layout(title=dict(yref="container", y=0.97, yanchor="top"))
    return fig


def edu_card(icon: str, title: str, body: str, color: str = "#6C5CE7"):
    st.markdown(
        f'<div class="edu-card" style="border-top-color:{color}">'
        f'<div class="icon">{icon}</div><div class="title">{title}</div>'
        f'<div class="body">{body}</div></div>',
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------ cached data
@st.cache_data
def get_history() -> pd.DataFrame:
    return market.monthly_history()


@st.cache_data
def get_unit_paths(w_tuple: tuple) -> np.ndarray:
    weights = dict(zip(market.ASSETS, w_tuple))
    return engine.simulate_unit_paths(weights)


def paths_for(weights: dict) -> np.ndarray:
    return get_unit_paths(tuple(round(weights[a], 4) for a in market.ASSETS))


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown("## 🧭 WealthLens")
    st.caption("Private wealth portfolio intelligence")
    name = st.text_input("Client name", "Alexandra Chen")
    value = st.number_input("Portfolio value (USD)", min_value=100_000,
                            max_value=1_000_000_000, value=5_000_000,
                            step=250_000, format="%d")

    st.markdown("### 📌 Current allocation")
    eq = st.slider("Equity %", 0, 100, 62)
    fi = st.slider("Fixed Income %", 0, 100, 23)
    alt = st.slider("Alternatives %", 0, 100, 15)
    total = eq + fi + alt
    if total == 0:
        eq, fi, alt, total = 34, 33, 33, 100
    current_w = {"Equity": eq / total, "Fixed Income": fi / total,
                 "Alternatives": alt / total}
    if total != 100:
        st.caption(f"Sliders sum to {total}% — normalised to "
                   + " / ".join(pct(current_w[a], 0) for a in market.ASSETS))

    st.markdown("### 📝 Risk questionnaire")
    age = st.slider("Age", 25, 85, 52)
    horizon_years = st.slider("Investment horizon (years)", 1, 30, 10)
    tolerance = st.slider("Comfort with market swings (1 = none, 10 = high)", 1, 10, 6)
    liquidity = st.selectbox("Cash needs from this portfolio",
                             ["Low", "Medium", "High"], index=0)

# ------------------------------------------------------------------ core computations
history = get_history()
score = engine.risk_score(age, horizon_years, tolerance, liquidity)
profile = engine.profile_for_score(score)
target_w = engine.RISK_PROFILES[profile]

cur_mu, cur_vol = engine.stats(current_w)
tgt_mu, tgt_vol = engine.stats(target_w)
cur_paths = paths_for(current_w)
tgt_paths = paths_for(target_w)
cur_summary = engine.horizon_summary(cur_paths, value)
drifts = {a: current_w[a] - target_w[a] for a in market.ASSETS}
max_drift = max(abs(d) for d in drifts.values())

# ------------------------------------------------------------------ hero
st.markdown(
    f'<div class="hero"><h1>🧭 WealthLens</h1>'
    f'<p>Portfolio intelligence for <b>{name}</b> · {money(value)} under advice</p>'
    f'<span class="pill">Recommended profile: {profile} · risk score {score}/100</span></div>',
    unsafe_allow_html=True,
)

tabs = st.tabs(["🏠 Overview", "🎯 Allocation Advisor", "🌪️ Stress Lab",
                "🔮 Future Paths", "📜 Track Record", "🎓 Learn"])


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
                                 line=dict(width=1, color="rgba(108,92,231,0.06)"),
                                 hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=dates, y=p95, line=dict(width=0),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=dates, y=p5, fill="tonexty",
                             fillcolor="rgba(108,92,231,0.14)", line=dict(width=0),
                             name="5th–95th percentile (9 in 10 outcomes)"))
    fig.add_trace(go.Scatter(x=dates, y=p75, line=dict(width=0),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=dates, y=p25, fill="tonexty",
                             fillcolor="rgba(108,92,231,0.30)", line=dict(width=0),
                             name="25th–75th percentile (most likely zone)"))
    fig.add_trace(go.Scatter(x=dates, y=p50, name="Median path",
                             line=dict(color="#6C5CE7", width=3)))
    fig.add_hline(y=base_value, line_dash="dot", line_color="#636E72",
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
        go.Bar(y=names, x=cur, orientation="h", name="Current allocation",
               marker_color="#0984E3"),
        go.Bar(y=names, x=tgt, orientation="h", name=f"Recommended ({profile})",
               marker_color="#E84393"),
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
        st.plotly_chart(allocation_donut(current_w, "Where your money sits today"),
                        use_container_width=True)
    with col2:
        ten_y = cur_summary[cur_summary["Horizon"] == "10Y"].iloc[0]
        one_y = cur_summary[cur_summary["Horizon"] == "1Y"].iloc[0]
        st.markdown("#### 🔭 10-year outlook (current allocation)")
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

    colg, colw = st.columns([1, 1.6])
    with colg:
        gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=score,
            title={"text": "Risk capacity score"},
            gauge=dict(
                axis=dict(range=[0, 100]),
                bar=dict(color="#6C5CE7", thickness=0.3),
                steps=[
                    dict(range=[0, 30], color="#dfe6e9"),
                    dict(range=[30, 45], color="#c7ecee"),
                    dict(range=[45, 62], color="#a3e4d7"),
                    dict(range=[62, 78], color="#f9e79f"),
                    dict(range=[78, 100], color="#f5b7b1"),
                ],
            ),
        ))
        st.plotly_chart(style(gauge, h=300), use_container_width=True)
        st.caption("Built from your age, horizon, comfort with swings, and "
                   "liquidity needs. Higher score → more room for growth assets.")
    with colw:
        d1, d2 = st.columns(2)
        with d1:
            st.plotly_chart(allocation_donut(current_w, "Current"),
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

    st.markdown("### ⚖️ What following the advice changes")
    gfc = engine.STRESS_SCENARIOS["2008 Global Financial Crisis"]["shocks"]
    cur10 = float(np.percentile(cur_paths[:, 120] * value, 50))
    tgt10 = float(np.percentile(tgt_paths[:, 120] * value, 50))
    comp = pd.DataFrame({
        "Metric": ["Expected return / yr", "Expected volatility",
                   "2008-style crisis impact", "10Y median value",
                   "1Y chance of loss"],
        "Current allocation": [
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

# ================================================================== STRESS LAB
with tabs[2]:
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
        connector=dict(line=dict(color="#b2bec3")),
        decreasing=dict(marker=dict(color="#E17055")),
        increasing=dict(marker=dict(color="#00B894")),
        totals=dict(marker=dict(color="#0984E3")),
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
with tabs[3]:
    which = st.radio("Simulate with…", ["Current allocation", f"Recommended ({profile})"],
                     horizontal=True)
    use_paths = cur_paths if which == "Current allocation" else tgt_paths

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
    hist_fig = go.Figure(go.Histogram(x=vals, nbinsx=60, marker_color="#6C5CE7",
                                      opacity=0.85))
    hist_fig.add_vline(x=value, line_dash="dot", line_color="#d63031",
                       annotation_text="Today's value")
    hist_fig.update_layout(title=f"All 2,500 simulated outcomes at {hz}",
                           xaxis_tickprefix="$", xaxis_tickformat="~s",
                           yaxis_title="Number of simulations")
    st.plotly_chart(style(hist_fig, h=360), use_container_width=True)

# ================================================================== TRACK RECORD
with tabs[4]:
    cur_ret = engine.backtest(current_w, history)
    tgt_ret = engine.backtest(target_w, history)
    cur_growth = value * (1 + cur_ret).cumprod()
    tgt_growth = value * (1 + tgt_ret).cumprod()

    g = go.Figure([
        go.Scatter(x=cur_growth.index, y=cur_growth, name="Current allocation",
                   line=dict(color=market.COLORS["Portfolio"], width=2.5)),
        go.Scatter(x=tgt_growth.index, y=tgt_growth, name=f"Recommended ({profile})",
                   line=dict(color=market.COLORS["Recommended"], width=2.5, dash="dash")),
    ])
    g.update_layout(title=f"If {money(value)} had been invested 20 years ago",
                    yaxis_tickprefix="$", yaxis_tickformat="~s")
    st.plotly_chart(style(g, h=400), use_container_width=True)

    cur_dd = cur_growth / cur_growth.cummax() - 1
    dd_fig = go.Figure(go.Scatter(x=cur_dd.index, y=cur_dd * 100, fill="tozeroy",
                                  line=dict(color="#E17055"), name="Drawdown"))
    dd_fig.update_layout(title="Drawdowns — how far below the previous peak (current mix)",
                         yaxis_ticksuffix="%")

    annual_cur = ((1 + cur_ret).resample("YE").prod() - 1) * 100
    annual_tgt = ((1 + tgt_ret).resample("YE").prod() - 1) * 100
    yr_fig = go.Figure([
        go.Bar(x=annual_cur.index.year, y=annual_cur, name="Current",
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

    st.markdown("### 📋 Performance scorecard (20-year backtest)")
    mc, mt = engine.perf_metrics(cur_ret), engine.perf_metrics(tgt_ret)
    fmt = {"Sharpe ratio": lambda v: f"{v:.2f}"}
    score_df = pd.DataFrame({
        "Metric": list(mc),
        "Current allocation": [fmt.get(k, pct)(v) for k, v in mc.items()],
        f"Recommended ({profile})": [fmt.get(k, pct)(v) for k, v in mt.items()],
    })
    st.dataframe(score_df, hide_index=True, use_container_width=True)
    st.caption("Backtest uses the app's illustrative market history with monthly "
               "rebalancing; past performance never guarantees future results.")

# ================================================================== LEARN
with tabs[5]:
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
            marker_color="#6C5CE7",
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
                              marker=dict(size=11, color="#00B894"), showlegend=False))
    anat.add_trace(go.Scatter(x=[trough], y=[eq_growth.loc[trough]], mode="markers+text",
                              text=[f"Trough 🕳️ ({dd.min():.0%})"],
                              textposition="bottom center",
                              marker=dict(size=11, color="#d63031"), showlegend=False))
    if len(rec_idx):
        anat.add_trace(go.Scatter(x=[rec_idx[0]], y=[eq_growth.loc[rec_idx[0]]],
                                  mode="markers+text", text=["Recovered 🎉"],
                                  textposition="top center",
                                  marker=dict(size=11, color="#0984E3"),
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
        ], columns=["Term", "Plain-English meaning"]),
            hide_index=True, use_container_width=True)

st.markdown("---")
st.caption("⚠️ WealthLens is an illustrative analytics tool using simulated market "
           "data and assumptions. It is not investment advice; consult your advisor "
           "before acting on any output.")
