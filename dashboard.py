import time
import html as _html
import requests
import streamlit as st
import plotly.graph_objects as go

FASTAPI_URL = "http://fastapi:8000"

st.set_page_config(
    page_title="PromptGuard",
    page_icon=None,
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
    padding: 1.2rem 0 1.5rem 0; border-bottom: 1px solid #21262d; margin-bottom: 1.75rem;
}
.pg-logo { display: flex; align-items: center; gap: 0.6rem; }
.pg-logo-mark {
    width: 32px; height: 32px;
    background: #238636;
    border-radius: 6px; display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700; color: #fff; letter-spacing: -0.5px;
}
.pg-logo-text { font-size: 1rem; font-weight: 600; color: #e6edf3; letter-spacing: -0.01em; }
.pg-logo-sub  { font-size: 0.7rem; color: #8b949e; font-weight: 400; }

.pg-guard-on {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: rgba(63,185,80,0.1); border: 1px solid rgba(63,185,80,0.3);
    color: #3fb950; border-radius: 6px; padding: 0.3rem 0.85rem;
    font-size: 0.78rem; font-weight: 600; font-family: 'JetBrains Mono', monospace;
}
.pg-guard-off {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: rgba(248,81,73,0.1); border: 1px solid rgba(248,81,73,0.3);
    color: #f85149; border-radius: 6px; padding: 0.3rem 0.85rem;
    font-size: 0.78rem; font-weight: 600; font-family: 'JetBrains Mono', monospace;
}

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

.pg-panel-title {
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.06em;
    text-transform: uppercase; color: #8b949e;
    margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid #21262d;
}

.pg-decision-blocked {
    background: rgba(248,81,73,0.12); border: 1px solid rgba(248,81,73,0.3);
    color: #f85149; border-radius: 6px; padding: 0.5rem 1.2rem;
    font-size: 1.1rem; font-weight: 700; letter-spacing: 0.1em;
    display: inline-block; font-family: 'JetBrains Mono', monospace;
}
.pg-decision-allowed {
    background: rgba(63,185,80,0.12); border: 1px solid rgba(63,185,80,0.3);
    color: #3fb950; border-radius: 6px; padding: 0.5rem 1.2rem;
    font-size: 1.1rem; font-weight: 700; letter-spacing: 0.1em;
    display: inline-block; font-family: 'JetBrains Mono', monospace;
}
.pg-decision-bypassed {
    background: rgba(210,153,34,0.12); border: 1px solid rgba(210,153,34,0.3);
    color: #d29922; border-radius: 6px; padding: 0.5rem 1.2rem;
    font-size: 1.1rem; font-weight: 700; letter-spacing: 0.1em;
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

.pg-chart-title {
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.06em;
    text-transform: uppercase; color: #8b949e; margin-bottom: 0.75rem;
}

div.stButton > button {
    background: #21262d !important; color: #e6edf3 !important;
    border: 1px solid #30363d !important; border-radius: 6px !important;
    font-weight: 500 !important; font-size: 0.85rem !important;
    padding: 0.45rem 1.2rem !important;
}
div.stButton > button:hover { background: #30363d !important; border-color: #8b949e !important; }

button[data-testid="baseButton-primary"] {
    background: #238636 !important; color: #fff !important;
    border: 1px solid #2ea043 !important;
}
button[data-testid="baseButton-primary"]:hover { background: #2ea043 !important; }

.stTextArea textarea {
    background: #0d1117 !important; border: 1px solid #30363d !important;
    color: #e6edf3 !important; font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important; border-radius: 6px !important;
}

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
.badge-u {
    background: rgba(210,153,34,0.12); color: #d29922;
    border: 1px solid rgba(210,153,34,0.25); border-radius: 4px;
    padding: 0.15rem 0.55rem; font-size: 0.7rem; font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {
    "protection_on": True,
    "last_result": None,
    "total_requests": 0,
    "threats_blocked": 0,
    "events": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ───────────────────────────────────────────────────────────────────
def api_toggle(enabled: bool):
    try:
        requests.post(f"{FASTAPI_URL}/toggle", json={"enabled": enabled}, timeout=4)
    except Exception:
        pass

def api_chat(prompt: str):
    try:
        r = requests.post(
            f"{FASTAPI_URL}/chat",
            json={"prompt": prompt, "system_prompt": "You are a helpful assistant."},
            timeout=300,
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def risk_color(score):
    if score >= 0.75: return "#f85149"
    if score >= 0.45: return "#d29922"
    return "#3fb950"

def plotly_layout(fig, height=220):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#8b949e", size=11),
        margin=dict(l=0, r=0, t=10, b=0), height=height,
        showlegend=False,
    )
    fig.update_xaxes(gridcolor="#21262d", zerolinecolor="#21262d", tickfont=dict(color="#8b949e"))
    fig.update_yaxes(gridcolor="#21262d", zerolinecolor="#21262d", tickfont=dict(color="#8b949e"))
    return fig

# ── Nav ───────────────────────────────────────────────────────────────────────
guard_label = "Protection: ON" if st.session_state.protection_on else "Protection: OFF"
guard_cls   = "pg-guard-on"    if st.session_state.protection_on else "pg-guard-off"

st.markdown(f"""
<div class="pg-nav">
    <div class="pg-logo">
        <div class="pg-logo-mark">PG</div>
        <div>
            <div class="pg-logo-text">PromptGuard</div>
            <div class="pg-logo-sub">Prompt Injection Detection</div>
        </div>
    </div>
    <span class="{guard_cls}">{guard_label}</span>
</div>
""", unsafe_allow_html=True)

# ── Toggle button ─────────────────────────────────────────────────────────────
_, tog_col = st.columns([6, 1])
with tog_col:
    btn_label = "Disable protection" if st.session_state.protection_on else "Enable protection"
    if st.button(btn_label, use_container_width=True):
        st.session_state.protection_on = not st.session_state.protection_on
        api_toggle(st.session_state.protection_on)
        st.rerun()

# ── Metrics ───────────────────────────────────────────────────────────────────
st.markdown('<div class="pg-section">Overview</div>', unsafe_allow_html=True)

m1, m2 = st.columns(2)

with m1:
    st.markdown(f"""
    <div class="pg-metric">
        <div class="pg-metric-label">Requests processed</div>
        <div class="pg-metric-value">{st.session_state.total_requests:,}</div>
        <div class="pg-metric-sub">This session</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="pg-metric">
        <div class="pg-metric-label">Threats blocked</div>
        <div class="pg-metric-value">{st.session_state.threats_blocked:,}</div>
        <div class="pg-metric-sub">This session</div>
    </div>
    """, unsafe_allow_html=True)

# ── Live analysis ─────────────────────────────────────────────────────────────
st.markdown('<div class="pg-section">Live Analysis</div>', unsafe_allow_html=True)

left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown('<div class="pg-panel-title">User Prompt Input</div>', unsafe_allow_html=True)
    prompt_input = st.text_area(
        label="", height=160,
        placeholder="Enter a prompt to test...",
        label_visibility="collapsed",
    )
    send_btn = st.button("Analyze Prompt", use_container_width=True, type="primary")

    if send_btn and prompt_input.strip():
        with st.spinner("Analyzing..."):
            result = api_chat(prompt_input.strip())

        st.session_state.last_result = result
        st.session_state.total_requests += 1

        decision = result.get("decision", "UNKNOWN")
        risk     = float(result.get("risk_score", 0))

        if decision == "BLOCKED":
            st.session_state.threats_blocked += 1

        cats = result.get("regex_categories") or []

        st.session_state.events.insert(0, {
            "prompt":   prompt_input.strip(),
            "decision": decision if st.session_state.protection_on else "BYPASSED",
            "risk":     round(risk, 2),
        })
        st.session_state.events = st.session_state.events[:20]

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

        # if protection is off, show bypassed regardless
        if not st.session_state.protection_on:
            badge_html = '<span class="pg-decision-bypassed">BYPASSED</span>'
            reason     = "Middleware is disabled. Prompt sent directly to the model."
        elif decision == "BLOCKED":
            badge_html = '<span class="pg-decision-blocked">BLOCKED</span>'
            if known:
                reason = "Matched a known attack in the vector database."
            elif cat_str != "—":
                reason = f"Detected pattern: <strong>{cat_str}</strong>."
            else:
                reason = "High semantic similarity to known attack prompts."
        else:
            badge_html = '<span class="pg-decision-allowed">ALLOWED</span>'
            reason     = "No injection patterns detected."

        risk_display = f'<span style="color:{bar_color};font-family:\'JetBrains Mono\',monospace;font-size:1rem;font-weight:700">{risk:.2f}</span>' if st.session_state.protection_on else '<span style="color:#8b949e;font-size:0.85rem">—</span>'

        st.markdown(f"""
        <div style="margin-bottom:1.5rem">
            <div style="font-size:0.72rem;color:#8b949e;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.5rem">Decision</div>
            {badge_html}
        </div>

        <div style="margin-bottom:1.5rem">
            <div style="font-size:0.72rem;color:#8b949e;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.3rem">
                Risk Score &nbsp;{risk_display}
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

        resp = result.get("response", "")
        if resp:
            st.markdown(f"""
        <div style="margin-top:1rem;padding:0.75rem 1rem;background:#0d1117;border:1px solid #21262d;
                    border-radius:6px;font-size:0.85rem;color:#e6edf3;line-height:1.6">
            <div style="font-size:0.7rem;color:#8b949e;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.5rem">LLM Response</div>
            {_html.escape(resp)}
        </div>""", unsafe_allow_html=True)

# ── Analytics ─────────────────────────────────────────────────────────────────
st.markdown('<div class="pg-section">Analytics</div>', unsafe_allow_html=True)

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
    st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

with ch2:
    st.markdown('<div class="pg-chart-title">Risk Score Distribution</div>', unsafe_allow_html=True)
    if ev:
        risks = [e["risk"] for e in ev]
        bins  = {"0.0-0.3": 0, "0.3-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0}
        for r in risks:
            if r < 0.3:   bins["0.0-0.3"] += 1
            elif r < 0.6: bins["0.3-0.6"] += 1
            elif r < 0.8: bins["0.6-0.8"] += 1
            else:          bins["0.8-1.0"] += 1
        fig2 = go.Figure(go.Bar(
            x=list(bins.keys()), y=list(bins.values()),
            marker_color=["#3fb950", "#d29922", "#f0883e", "#f85149"],
            width=[0.5]*4,
            text=list(bins.values()), textposition="outside",
            textfont=dict(color="#8b949e", size=11),
        ))
        fig2 = plotly_layout(fig2)
        fig2.update_xaxes(title_text="Risk Range", title_font=dict(color="#8b949e", size=10))
        fig2.update_yaxes(title_text="Count",      title_font=dict(color="#8b949e", size=10))
    else:
        fig2 = go.Figure()
        fig2 = plotly_layout(fig2)
        fig2.add_annotation(text="No data yet",
                            xref="paper", yref="paper", x=0.5, y=0.5,
                            showarrow=False, font=dict(color="#8b949e", size=12))
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

# ── Recent events ─────────────────────────────────────────────────────────────
st.markdown('<div class="pg-section">Recent Events</div>', unsafe_allow_html=True)

if not ev:
    st.markdown("""
    <div style="background:#161b22;border:1px solid #21262d;border-radius:10px;
                padding:1.1rem 1.5rem;color:#8b949e;font-size:0.83rem;text-align:center;">
        No events yet.
    </div>
    """, unsafe_allow_html=True)
else:
    rows = ""
    for e in ev[:10]:
        d = e["decision"]
        if d == "BLOCKED":
            badge = '<span class="badge-b">BLOCKED</span>'
        elif d == "BYPASSED":
            badge = '<span class="badge-u">BYPASSED</span>'
        else:
            badge = '<span class="badge-a">ALLOWED</span>'

        rows += f"""
<tr>
    <td style="max-width:650px;white-space:normal;word-break:break-word;
               font-family:'JetBrains Mono',monospace;color:#e6edf3;font-size:0.8rem;">
        {_html.escape(e["prompt"])}
    </td>
    <td>{badge}</td>
</tr>
"""
    st.markdown(f"""
<div style="background:#161b22;border:1px solid #21262d;border-radius:10px;overflow:hidden">
<table class="ev-table">
    <tr><th>Prompt</th><th>Decision</th></tr>
    {rows}
</table>
</div>
""", unsafe_allow_html=True)