import random
from datetime import datetime, timedelta

import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

FASTAPI_URL = "http://fastapi:8000"

st.set_page_config(
    page_title="PromptGuard Security Console",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0d1117; color: #e6edf3; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 2rem 2rem 2rem; max-width: 100%; }

.pg-nav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1rem 0 1.5rem 0; border-bottom: 1px solid #21262d; margin-bottom: 1.75rem;
}
.pg-logo { display: flex; align-items: center; gap: 0.6rem; }
.pg-logo-mark {
    width: 32px; height: 32px;
    background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
    border-radius: 7px; display: flex; align-items: center; justify-content: center;
    font-size: 17px; line-height: 1;
}
.pg-logo-text { font-size: 1.05rem; font-weight: 600; color: #e6edf3; letter-spacing: -0.01em; }
.pg-logo-sub { font-size: 0.7rem; color: #8b949e; font-weight: 400; }
.pg-title { font-size: 0.85rem; color: #8b949e; font-weight: 500; }

.pg-section {
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; color: #8b949e;
    margin: 2rem 0 0.85rem 0; display: flex; align-items: center; gap: 0.5rem;
}
.pg-section::after { content: ''; flex: 1; height: 1px; background: #21262d; }

.pg-metric {
    background: #161b22; border: 1px solid #21262d;
    border-radius: 10px; padding: 1.25rem 1.5rem; height: 100%;
}
.pg-metric-label {
    font-size: 0.72rem; color: #8b949e; font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.5rem;
}
.pg-metric-value {
    font-size: 2rem; font-weight: 700; color: #e6edf3;
    line-height: 1; font-family: 'JetBrains Mono', monospace;
}
.pg-metric-sub { font-size: 0.72rem; color: #8b949e; margin-top: 0.4rem; }
.pg-metric-trend-up { color: #3fb950; }
.pg-metric-trend-dn { color: #f85149; }

.pg-status-healthy {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: rgba(63,185,80,0.12); border: 1px solid rgba(63,185,80,0.3);
    color: #3fb950; border-radius: 20px; padding: 0.25rem 0.75rem;
    font-size: 0.78rem; font-weight: 600;
}
.pg-status-offline {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: rgba(248,81,73,0.12); border: 1px solid rgba(248,81,73,0.3);
    color: #f85149; border-radius: 20px; padding: 0.25rem 0.75rem;
    font-size: 0.78rem; font-weight: 600;
}

.pg-panel-title {
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.06em;
    text-transform: uppercase; color: #8b949e;
    margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid #21262d;
}

.pg-decision-blocked {
    background: rgba(248,81,73,0.12); border: 1px solid rgba(248,81,73,0.3);
    color: #f85149; border-radius: 6px; padding: 0.6rem 1.2rem;
    font-size: 1.3rem; font-weight: 700; letter-spacing: 0.08em;
    display: inline-block; font-family: 'JetBrains Mono', monospace;
}
.pg-decision-allowed {
    background: rgba(63,185,80,0.12); border: 1px solid rgba(63,185,80,0.3);
    color: #3fb950; border-radius: 6px; padding: 0.6rem 1.2rem;
    font-size: 1.3rem; font-weight: 700; letter-spacing: 0.08em;
    display: inline-block; font-family: 'JetBrains Mono', monospace;
}

.pg-risk-bar-wrap {
    background: #21262d; border-radius: 4px; height: 6px; margin: 0.5rem 0; overflow: hidden;
}
.pg-risk-bar-fill { height: 100%; border-radius: 4px; }

.pg-info-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.55rem 0; border-bottom: 1px solid #21262d; font-size: 0.83rem;
}
.pg-info-row:last-child { border-bottom: none; }
.pg-info-key { color: #8b949e; }
.pg-info-val { color: #e6edf3; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; }

.pg-review-card {
    background: #161b22; border: 1px solid #30363d;
    border-left: 3px solid #d29922; border-radius: 10px; padding: 1.25rem 1.5rem;
}
.pg-review-prompt {
    background: #0d1117; border: 1px solid #21262d; border-radius: 6px;
    padding: 0.75rem 1rem; font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem; color: #e6edf3; margin: 0.75rem 0; word-break: break-word;
}
.pg-review-meta { display: flex; gap: 2rem; margin: 0.75rem 0; flex-wrap: wrap; }
.pg-review-meta-item { font-size: 0.78rem; }
.pg-review-meta-label { color: #8b949e; }
.pg-review-meta-val { color: #e6edf3; font-weight: 600; font-family: 'JetBrains Mono', monospace; }

.pg-chart-title {
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.06em;
    text-transform: uppercase; color: #8b949e; margin-bottom: 0.75rem;
}

div.stButton > button {
    background: #238636 !important; color: #fff !important;
    border: 1px solid #2ea043 !important; border-radius: 6px !important;
    font-weight: 600 !important; font-size: 0.85rem !important;
    padding: 0.45rem 1.2rem !important;
}
div.stButton > button:hover { background: #2ea043 !important; }

.stTextArea textarea {
    background: #0d1117 !important; border: 1px solid #30363d !important;
    color: #e6edf3 !important; font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important; border-radius: 6px !important;
}

/* events table */
.ev-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
.ev-table th {
    text-align: left; padding: 0.6rem 1rem; border-bottom: 1px solid #21262d;
    color: #8b949e; font-weight: 500; font-size: 0.7rem;
    letter-spacing: 0.05em; text-transform: uppercase;
}
.ev-table td { padding: 0.65rem 1rem; border-bottom: 1px solid #0d1117; color: #e6edf3; }
.ev-table tr:last-child td { border-bottom: none; }
.ev-table tr:hover td { background: #1c2128; }
.badge-b {
    background: rgba(248,81,73,0.12); color: #f85149;
    border: 1px solid rgba(248,81,73,0.25); border-radius: 4px;
    padding: 0.15rem 0.55rem; font-size: 0.7rem; font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}
.badge-a {
    background: rgba(63,185,80,0.12); color: #3fb950;
    border: 1px solid rgba(63,185,80,0.25); border-radius: 4px;
    padding: 0.15rem 0.55rem; font-size: 0.7rem; font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}
</style>
""", unsafe_allow_html=True)

if "protection_on" not in st.session_state:
    st.session_state.protection_on = True
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "total_requests" not in st.session_state:
    st.session_state.total_requests = 0
if "threats_blocked" not in st.session_state:
    st.session_state.threats_blocked = 0
if "events" not in st.session_state:
    st.session_state.events = []

def api_toggle(enabled):
    try:
        requests.post(f"{FASTAPI_URL}/toggle", json={"enabled": enabled}, timeout=4)
    except Exception:
        pass

import time

def api_chat(prompt):
    try:
        start = time.time()

        print("[DASHBOARD] Sending request...")

        r = requests.post(
            f"{FASTAPI_URL}/chat",
            json={
                "prompt": prompt,
                "system_prompt": "You are a helpful assistant."
            },
            timeout=300,
        )

        print(f"[DASHBOARD] HTTP finished in {time.time()-start:.2f}s")

        parse = time.time()
        data = r.json()

        print(f"[DASHBOARD] JSON parse: {time.time()-parse:.4f}s")
        print(f"[DASHBOARD] TOTAL: {time.time()-start:.2f}s")

        return data

    except Exception as e:
        print("[DASHBOARD] ERROR:", e)
        return {"error": str(e)}

def api_health():
    try:
        r = requests.get(f"{FASTAPI_URL}/health", timeout=3)
        return r.json() if r.ok else None
    except Exception:
        return None


def risk_color(score):
    if score >= 0.75: return "#f85149"
    if score >= 0.45: return "#d29922"
    return "#3fb950"

def plotly_layout(fig, height=220):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#8b949e", size=11),
        margin=dict(l=0, r=0, t=10, b=0), height=height,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#8b949e")),
    )
    fig.update_xaxes(gridcolor="#21262d", zerolinecolor="#21262d", tickfont=dict(color="#8b949e"))
    fig.update_yaxes(gridcolor="#21262d", zerolinecolor="#21262d", tickfont=dict(color="#8b949e"))
    return fig

health = api_health()
system_ok = health is not None

st.markdown("""
<div class="pg-nav">
    <div class="pg-logo">
        <div class="pg-logo-mark">🛡️</div>
        <div>
            <div class="pg-logo-text">PromptGuard</div>
            <div class="pg-logo-sub">Security Console</div>
        </div>
    </div>
    <div class="pg-title">AI Threat Detection · LLM Security Platform</div>
</div>
""", unsafe_allow_html=True)



st.markdown('<div class="pg-section">System Overview</div>', unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)

with m1:
    st.markdown(f"""
    <div class="pg-metric">
        <div class="pg-metric-label">Requests Processed</div>
        <div class="pg-metric-value">{st.session_state.total_requests:,}</div>
        <div class="pg-metric-sub">This session</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    block_pct = round(st.session_state.threats_blocked / max(st.session_state.total_requests, 1) * 100, 1)
    st.markdown(f"""
    <div class="pg-metric">
        <div class="pg-metric-label">Threats Blocked</div>
        <div class="pg-metric-value">{st.session_state.threats_blocked:,}</div>
        <div class="pg-metric-sub pg-metric-trend-dn">{block_pct}% block rate</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    if system_ok:
        badge = '<span class="pg-status-healthy">● Healthy</span>'
        lora  = "Loaded" if health.get("lora_loaded") else "Fallback mode"
        sub   = f"LoRA classifier: {lora}"
    else:
        badge = '<span class="pg-status-offline">● Offline</span>'
        sub   = "Cannot reach FastAPI backend"
    st.markdown(f"""
    <div class="pg-metric">
        <div class="pg-metric-label">System Status</div>
        <div style="margin: 0.4rem 0 0.5rem 0">{badge}</div>
        <div class="pg-metric-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="pg-section">Live Analysis</div>', unsafe_allow_html=True)

left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown('<div class="pg-panel-title">User Prompt Input</div>', unsafe_allow_html=True)
    prompt_input = st.text_area(
        label="", height=160,
        placeholder="Enter a prompt to test against PromptGuard…",
        label_visibility="collapsed",
    )
    send_btn = st.button("⬆  Analyze Prompt", use_container_width=True)

    if send_btn and prompt_input.strip():
        import time

        overall = time.time()
        print("[STREAMLIT] Button clicked")

        with st.spinner("Analyzing…"):
            result = api_chat(prompt_input.strip())

        print(f"[STREAMLIT] api_chat returned after {time.time() - overall:.2f}s")

        st.session_state.last_result = result
        st.session_state.total_requests += 1

        decision = result.get("decision", "UNKNOWN")
        risk = float(result.get("risk_score", 0))

        print(f"[STREAMLIT] Before remaining processing: {time.time() - overall:.2f}s")

        if decision == "BLOCKED":
            st.session_state.threats_blocked += 1


        cats = result.get("regex_categories") or []

        if decision == "BLOCKED" and cats:
            event_type = cats[0]
        elif decision == "ALLOWED":
            event_type = "Benign"
        else:
            event_type = "Unknown"

        st.session_state.events.insert(0, {
            "prompt": prompt_input.strip(),
            "decision": decision,
            "risk": round(risk, 2),
        })

        st.session_state.events = st.session_state.events[:20]

        print(f"[STREAMLIT] TOTAL: {time.time() - overall:.2f}s")

with right:
    st.markdown('<div class="pg-panel-title">Detection Result</div>', unsafe_allow_html=True)
    result = st.session_state.last_result

    if result is None:
        st.markdown("""
        <div style="color:#8b949e;font-size:0.85rem;padding:2.5rem 0;text-align:center;">
            Submit a prompt to see the result.
        </div>
        """, unsafe_allow_html=True)
    elif "error" in result:
        st.error(f"Backend error: {result['error']}")
    else:
        decision  = result.get("decision", "UNKNOWN")
        risk      = float(result.get("risk_score", 0))
        cats      = result.get("regex_categories") or []
        cat_str   = cats[0] if cats else "—"
        known     = result.get("known_attack", False)
        bar_color = risk_color(risk)

        badge_cls = "pg-decision-blocked" if decision == "BLOCKED" else "pg-decision-allowed"
        icon      = "" if decision == "BLOCKED" else ""

        if decision == "BLOCKED":
            if known:
                reason = "Matched a known attack in the database."
            elif cat_str != "—":
                reason = f"Detected as <strong>{cat_str}</strong> by pattern analysis."
            else:
                reason = "High semantic similarity to known attack prompts."
        else:
            reason = "No injection patterns detected."

        st.markdown(f"""
        <div style="margin-bottom:1.5rem">
            <div style="font-size:0.72rem;color:#8b949e;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.5rem">Decision</div>
            <span class="{badge_cls}">{icon} {decision}</span>
        </div>

        <div style="margin-bottom:1.5rem">
            <div style="font-size:0.72rem;color:#8b949e;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.3rem">
                Risk Score &nbsp;<span style="color:{bar_color};font-family:'JetBrains Mono',monospace;font-size:1rem;font-weight:700">{risk:.2f}</span>
            </div>
            <div class="pg-risk-bar-wrap">
                <div class="pg-risk-bar-fill" style="width:{risk*100:.0f}%;background:{bar_color}"></div>
            </div>
        </div>

        <div class="pg-info-row">
            <span class="pg-info-key">Attack Category</span>
            <span class="pg-info-val">{cat_str}</span>
        </div>
        
        <div style="margin-top:1rem;padding:0.75rem 1rem;background:#1c2128;border-radius:6px;font-size:0.8rem;color:#8b949e;line-height:1.5">
            <span style="color:#e6edf3;font-weight:600">Why: </span>{reason}
        </div>
        """, unsafe_allow_html=True)

        if decision == "ALLOWED":
            resp = result.get("response", "")
            if resp:
                with st.expander("LLM Response", expanded=False):
                    st.markdown(f"<div style='font-size:0.85rem;color:#e6edf3'>{resp}</div>", unsafe_allow_html=True)


st.markdown('<div class="pg-section">Security Analytics</div>', unsafe_allow_html=True)

total_rq  = st.session_state.total_requests
total_blk = st.session_state.threats_blocked
total_ok  = total_rq - total_blk
ev        = st.session_state.events

ch1, ch2 = st.columns(2, gap="large")

with ch1:
    st.markdown('<div class="pg-chart-title">Blocked vs Allowed</div>', unsafe_allow_html=True)
    fig1 = go.Figure(go.Bar(
        x=["Allowed", "Blocked"], y=[total_ok, total_blk],
        marker_color=["#238636", "#da3633"], width=[0.5, 0.5],
        text=[total_ok, total_blk], textposition="outside",
        textfont=dict(color="#8b949e", size=11),
    ))
    fig1 = plotly_layout(fig1)
    fig1.update_layout(showlegend=False)
    st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

with ch2:
    # Risk score distribution from actual events
    st.markdown('<div class="pg-chart-title">Risk Score Distribution</div>', unsafe_allow_html=True)
    if ev:
        risks = [e["risk"] for e in ev]
        bins  = {"0.0–0.3": 0, "0.3–0.6": 0, "0.6–0.8": 0, "0.8–1.0": 0}
        for r in risks:
            if r < 0.3:   bins["0.0–0.3"] += 1
            elif r < 0.6: bins["0.3–0.6"] += 1
            elif r < 0.8: bins["0.6–0.8"] += 1
            else:          bins["0.8–1.0"] += 1
        fig2 = go.Figure(go.Bar(
            x=list(bins.keys()), y=list(bins.values()),
            marker_color=["#3fb950", "#d29922", "#f0883e", "#f85149"],
            width=[0.5]*4,
            text=list(bins.values()), textposition="outside",
            textfont=dict(color="#8b949e", size=11),
        ))
        fig2 = plotly_layout(fig2)
        fig2.update_layout(showlegend=False)
        fig2.update_xaxes(title_text="Risk Range", title_font=dict(color="#8b949e", size=10))
        fig2.update_yaxes(title_text="Count", title_font=dict(color="#8b949e", size=10))
    else:
        fig2 = go.Figure()
        fig2 = plotly_layout(fig2)
        fig2.add_annotation(text="No data yet — submit prompts to populate",
                            xref="paper", yref="paper", x=0.5, y=0.5,
                            showarrow=False, font=dict(color="#8b949e", size=12))
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})


st.markdown('<div class="pg-section">Recent Security Events</div>', unsafe_allow_html=True)

if not ev:
    st.markdown("""
    <div style="background:#161b22;border:1px solid #21262d;border-radius:10px;
                padding:1.1rem 1.5rem;color:#8b949e;font-size:0.83rem;text-align:center;">
        No events yet — submit a prompt above to see results here.
    </div>
    """, unsafe_allow_html=True)
else:
    import html as _html
    rows = ""

    for e in ev[:10]:
        badge = (
            '<span class="badge-b">BLOCKED</span>'
            if e["decision"] == "BLOCKED"
            else '<span class="badge-a">ALLOWED</span>'
        )
        safe_prompt = _html.escape(e["prompt"])

        rows += f"""
<tr>
    <td style="
        max-width:650px;
        white-space:normal;
        word-break:break-word;
        font-family:'JetBrains Mono', monospace;
        color:#e6edf3;
    ">
        {safe_prompt}
    </td>
    <td>{badge}</td>
</tr>
"""

    st.markdown(
        f"""
<div style="background:#161b22;border:1px solid #21262d;border-radius:10px;overflow:hidden">
<table class="ev-table">
    <tr>
        <th>Prompt</th>
        <th>Decision</th>
    </tr>
    {rows}
</table>
</div>
""",
        unsafe_allow_html=True,
    )