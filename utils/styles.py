"""
Shared mobile-first CSS — makes the Streamlit app look like an iPhone 16 Plus app.
Call inject_mobile_css() at the top of every page after set_page_config().
"""
import streamlit as st


def inject_mobile_css():
    st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Root palette ── */
:root {
    --bg:        #0f1117;
    --surface:   #1a1d27;
    --card:      #22263a;
    --border:    #2e3352;
    --accent:    #4ade80;
    --accent2:   #22d3ee;
    --warn:      #fbbf24;
    --danger:    #f87171;
    --text:      #f0f4ff;
    --muted:     #8b92b3;
    --radius:    16px;
    --radius-sm: 10px;
}

/* ── Base ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--text) !important;
}

/* ── Centre + constrain to iPhone 16 Plus width (430 px) desktop frame ── */
[data-testid="stMain"] > div:first-child,
[data-testid="stMainBlockContainer"] {
    max-width: 460px !important;
    margin: 0 auto !important;
    padding: 56px 16px 80px 16px !important;
}

/* ── Hide default streamlit chrome (keep header for sidebar toggle on mobile) ── */
#MainMenu, footer,
[data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }

/* Keep header visible but make it blend with dark theme */
[data-testid="stHeader"] {
    background: var(--bg) !important;
    border-bottom: 1px solid var(--border) !important;
}
/* Hide only the deploy/github buttons inside the header */
[data-testid="stHeader"] [data-testid="stActionButtonLabel"] { display: none !important; }

/* Make the sidebar hamburger toggle more prominent on mobile */
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapseButton"] {
    background: var(--accent) !important;
    border-radius: 10px !important;
    padding: 4px !important;
}
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="stSidebarCollapseButton"] svg {
    fill: #05170b !important;
    color: #05170b !important;
}

/* ── Sidebar → slide-in drawer feel ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebarNavItems"] a {
    border-radius: var(--radius-sm) !important;
    padding: 10px 14px !important;
    margin: 2px 0 !important;
    font-weight: 500 !important;
    transition: background 0.15s;
}
[data-testid="stSidebarNavItems"] a:hover,
[data-testid="stSidebarNavItems"] a[aria-selected="true"] {
    background: var(--card) !important;
    color: var(--accent) !important;
}

/* ── Typography ── */
h1 { font-size: 1.45rem !important; font-weight: 800 !important; letter-spacing: -0.3px; margin-bottom: 4px !important; }
h2, h3 { font-size: 1.05rem !important; font-weight: 700 !important; color: var(--text) !important; }
p, li { font-size: 0.92rem !important; }

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 14px 12px !important;
}
[data-testid="stMetricLabel"] { font-size: 0.72rem !important; color: var(--muted) !important; text-transform: uppercase; letter-spacing: 0.5px; }
[data-testid="stMetricValue"] { font-size: 1.35rem !important; font-weight: 800 !important; color: var(--text) !important; }
[data-testid="stMetricDelta"] svg { display:none; }    

/* ── Buttons ── */
[data-testid="stFormSubmitButton"] button,
[data-testid="stButton"] button {
    width: 100% !important;
    background: var(--accent) !important;
    color: #05170b !important;
    border: none !important;
    border-radius: 50px !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 12px 20px !important;
    letter-spacing: 0.2px;
    transition: filter 0.15s;
}
[data-testid="stFormSubmitButton"] button:hover,
[data-testid="stButton"] button:hover { filter: brightness(1.12); }

/* Primary button accent */
button[kind="primary"] {
    background: var(--accent) !important;
}

/* ── Inputs & selects ── */
input, textarea, select,
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stDateInput"] input {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
    font-size: 0.92rem !important;
    padding: 10px 12px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(74,222,128,0.18) !important;
}

/* ── Selectbox ── */
[data-baseweb="select"] {
    background: var(--card) !important;
    border-radius: var(--radius-sm) !important;
}

/* ── Slider ── */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] div[data-testid="stTickBar"] {
    display: none;
}

/* ── Forms ── */
[data-testid="stForm"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 16px !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}
[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 12px 16px !important;
}

/* ── Dataframe / table ── */
[data-testid="stDataFrame"] {
    border-radius: var(--radius) !important;
    overflow: hidden;
    border: 1px solid var(--border) !important;
}
[data-testid="stDataFrame"] table { width: 100% !important; }
[data-testid="stDataFrame"] th {
    background: var(--card) !important;
    color: var(--muted) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 10px 12px !important;
}
[data-testid="stDataFrame"] td {
    background: var(--surface) !important;
    color: var(--text) !important;
    font-size: 0.88rem !important;
    padding: 10px 12px !important;
    border-bottom: 1px solid var(--border) !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: var(--radius-sm) !important;
    font-size: 0.88rem !important;
}
[data-testid="stSuccessAlert"]  { border-left: 4px solid var(--accent) !important; }
[data-testid="stWarningAlert"]  { border-left: 4px solid var(--warn) !important; }
[data-testid="stErrorAlert"]    { border-left: 4px solid var(--danger) !important; }
[data-testid="stInfoAlert"]     { border-left: 4px solid var(--accent2) !important; }

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 16px 0 !important; }

/* ── Checkbox ── */
[data-testid="stCheckbox"] label { font-size: 0.88rem !important; }

/* ── Label ── */
[data-testid="stWidgetLabel"], label { color: var(--muted) !important; font-size: 0.78rem !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.4px; }

/* ── Table for markdown ── */
table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
th { background: var(--card); color: var(--muted); padding: 8px 10px; text-align: left; font-size: 0.72rem; text-transform: uppercase; letter-spacing:0.5px; }
td { padding: 9px 10px; border-bottom: 1px solid var(--border); }

/* ── Columns: stack on very narrow ── */
@media (max-width: 500px) {
    [data-testid="stColumns"] { flex-direction: column !important; }
    [data-testid="stColumns"] > div { width: 100% !important; }
}

/* ── Skill badge pill ── */
.skill-badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 50px;
    font-size: 0.8rem;
    font-weight: 700;
    color: #05170b;
    background: var(--accent);
    margin-left: 8px;
}

/* ── Page title row ── */
.page-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
}

/* ── Nav card grid (home page) ── */
.nav-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 18px 8px !important;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.15s, background 0.15s;
    text-decoration: none !important;
    min-height: 90px;
}
.nav-card:hover { border-color: var(--accent) !important; background: var(--surface) !important; }
.nav-card .icon { font-size: 1.8rem; margin-bottom: 6px; }
.nav-card .label { font-size: 0.78rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.4px; }

/* st.page_link styling */
[data-testid="stPageLink"] a {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    background: var(--card) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 16px 8px !important;
    text-align: center !important;
    text-decoration: none !important;
    min-height: 80px !important;
    transition: border-color 0.15s;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: var(--text) !important;
}
[data-testid="stPageLink"] a:hover {
    border-color: var(--accent) !important;
    background: var(--surface) !important;
}
</style>
""", unsafe_allow_html=True)
