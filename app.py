import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Streamlit Community Cloud stores credentials in st.secrets.
# Mirror known keys into environment variables so the APEX modules work
# identically locally and in the cloud.
for _key in ["THE_ODDS_API_KEY", "APEX_PLAYER_HISTORY_URL", "APEX_AVAILABILITY_URL"]:
    try:
        if _key in st.secrets and str(st.secrets[_key]).strip():
            os.environ[_key] = str(st.secrets[_key]).strip()
    except Exception:
        pass

from apex.live import SPORTS, MARKETS, has_key
from apex.feeds import (
    normalize_history,
    normalize_availability,
    remote_history,
    remote_availability,
)
from apex.metrics import summary, calibration_table
from apex.governor import audit_groups
from apex.scanner import scan
from apex.storage import init_db, add_paper, ledger

st.set_page_config(
    page_title="APEX",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_db()

st.markdown("""
<style>
.block-container {max-width: 1080px; padding-top: 0.75rem; padding-bottom: 5rem;}
h1 {font-size: 2rem !important;}
div[data-testid="stMetric"] {
    border: 1px solid rgba(128,128,128,.22);
    padding: 10px;
    border-radius: 14px;
}
.stButton > button {
    width: 100%;
    min-height: 52px;
    border-radius: 14px;
    font-weight: 800;
}
@media (max-width: 640px) {
    .block-container {padding-left: .75rem; padding-right: .75rem;}
    h1 {font-size: 1.65rem !important;}
    div[data-testid="column"] {min-width: 0 !important;}
}
</style>
""", unsafe_allow_html=True)

st.title("⚡ APEX")
st.caption("Mobile live-prop scanner + self-auditing Governor")

# ---------- Load data ----------
history = st.session_state.get("history")
if history is None:
    try:
        history = remote_history()
        history_source = "remote"
    except Exception:
        history = None
    if history is None:
        history = normalize_history(pd.read_csv(Path(__file__).with_name("sample_player_history.csv")))
        history_source = "demo"
else:
    history_source = "session"

availability = st.session_state.get("availability")
if availability is None:
    try:
        availability = remote_availability()
        availability_source = "remote"
    except Exception:
        availability = None
    if availability is None:
        availability = normalize_availability(pd.read_csv(Path(__file__).with_name("sample_availability.csv")))
        availability_source = "demo"
else:
    availability_source = "session"

pred = st.session_state.get("pred")
if pred is None:
    pred = pd.read_csv(Path(__file__).with_name("sample_predictions.csv"))

pred["model_probability"] = pd.to_numeric(pred["model_probability"], errors="coerce").clip(.001,.999)
pred["odds"] = pd.to_numeric(pred["odds"], errors="coerce")
pred["result"] = pd.to_numeric(pred["result"], errors="coerce")
if "closing_odds" not in pred.columns:
    pred["closing_odds"] = pd.NA
pred = pred.dropna(subset=["model_probability","odds","result"])
audit = audit_groups(pred)

tabs = st.tabs(["⚡ SCAN", "🧠 GOVERNOR", "📒 LEDGER", "🔌 STATUS"])

# ---------- Scan ----------
with tabs[0]:
    sport = st.selectbox("Sport", list(SPORTS.keys()))
    markets = st.multiselect("Markets", MARKETS[sport], default=MARKETS[sport])
    max_events = st.slider("Games to scan", 1, 20, 8)

    if not has_key():
        st.error("Live odds are not connected yet. Open the STATUS tab for setup.")
    else:
        st.success("Live odds connected.")

    if st.button("⚡ ONE-TAP SCAN", type="primary", disabled=not has_key()):
        ranked, errors = scan(
            sport,
            SPORTS[sport],
            markets,
            history,
            availability,
            audit,
            max_events,
        )
        st.session_state["ranked"] = ranked
        st.session_state["errors"] = errors

    ranked = st.session_state.get("ranked", [])
    if ranked:
        actionable = [x for x in ranked if x["verdict"] in ("ATTACK","VALUE","WATCH")]
        top = (actionable or ranked)[:15]

        st.subheader(f"{len(actionable)} actionable signals")

        d = pd.DataFrame(top)
        show = d.copy()
        for c in [
            "raw_probability","model_probability","market_probability",
            "edge","ev","confidence","robustness","governor_multiplier"
        ]:
            show[c] = show[c].map(lambda x: f"{x:.1%}")
        show["projection"] = show["projection"].round(1)

        st.dataframe(
            show[[
                "verdict","apex_score","player","market","line","book",
                "projection","model_probability","market_probability",
                "edge","ev","governor_multiplier","status"
            ]],
            hide_index=True,
            use_container_width=True,
        )

        best = top[0]
        st.markdown(f"## {best['verdict']} · APEX {best['apex_score']}/100")
        st.write(f"**{best['player']} — Over {best['line']} {best['market']} · {best['book']}**")

        c1,c2,c3 = st.columns(3)
        c1.metric("Model", f"{best['model_probability']:.1%}")
        c2.metric("Market", f"{best['market_probability']:.1%}")
        c3.metric("Projection", f"{best['projection']:.1f}")

        c4,c5,c6 = st.columns(3)
        c4.metric("Edge", f"{best['edge']:+.1%}")
        c5.metric("EV", f"{best['ev']:+.1%}")
        c6.metric("Fair odds", str(best["fair_odds"]))

        if best.get("market_warning"):
            st.warning("Market movement weakened this signal, so APEX downgraded it.")

        if st.button("SAVE BEST AS PAPER TRADE"):
            add_paper(sport, best)
            st.success("Saved to paper-trade ledger.")

    elif "ranked" in st.session_state:
        st.info("Scan finished, but no live props matched the loaded player-history database.")

# ---------- Governor ----------
with tabs[1]:
    s = summary(pred)
    a,b,c,d = st.columns(4)
    a.metric("Brier", f"{s['brier']:.3f}")
    b.metric("Log loss", f"{s['log_loss']:.3f}")
    c.metric("Win rate", f"{s['win_rate']:.1%}")
    d.metric("Sim. ROI", f"{s['roi']:+.1%}")

    st.dataframe(audit, hide_index=True, use_container_width=True)

    cal = calibration_table(pred)
    fig, ax = plt.subplots()
    ax.plot([0,1],[0,1], linestyle="--")
    ax.scatter(cal["avg_probability"], cal["actual_win_rate"])
    ax.set_xlim(0,1)
    ax.set_ylim(0,1)
    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Actual win rate")
    st.pyplot(fig)

# ---------- Ledger ----------
with tabs[2]:
    rows = ledger()
    if rows:
        cols = [
            "created_at","sport","event_id","book","market","player","line",
            "odds","model_probability","market_probability","edge","ev",
            "verdict","result","closing_odds"
        ]
        st.dataframe(pd.DataFrame(rows, columns=cols), hide_index=True, use_container_width=True)
    else:
        st.info("No paper trades yet.")

# ---------- Status / setup ----------
with tabs[3]:
    st.subheader("Connection health")

    odds_ok = has_key()
    hist_remote = bool(os.getenv("APEX_PLAYER_HISTORY_URL","").strip())
    avail_remote = bool(os.getenv("APEX_AVAILABILITY_URL","").strip())

    st.write("✅ Live odds API connected" if odds_ok else "❌ Live odds API not connected")
    st.write("✅ Player-history feed configured" if hist_remote else f"⚠️ Player-history feed not configured — using {history_source}")
    st.write("✅ Availability feed configured" if avail_remote else f"⚠️ Availability feed not configured — using {availability_source}")

    st.markdown("### iPhone deployment checklist")
    st.markdown("""
1. Put this folder in a GitHub repository.
2. In Streamlit Community Cloud, create an app from that repository.
3. Set the app file to `app.py`.
4. Open **Advanced settings → Secrets**.
5. Paste your `THE_ODDS_API_KEY` and optional feed URLs from `.streamlit/secrets.example.toml`.
6. Deploy.
7. Open the resulting `streamlit.app` address in Safari.
8. Use **Share → Add to Home Screen** for an app-like icon.
""")

    st.info("Never upload your real API key into the GitHub repository.")

st.caption("APEX is probabilistic research software. No outcome or profit is guaranteed.")
