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
    --bg:        #0d1021;
    --surface:   #141829;
    --card:      #1c2135;
    --border:    #2a3260;
    --accent:    #34d399;
    --accent2:   #38bdf8;
    --accent3:   #a78bfa;
    --warn:      #fbbf24;
    --danger:    #f87171;
    --text:      #e8edff;
    --text-inv:  #0d1021;
    --muted:     #7c85b0;
    --dropdown-bg:   #fef08a;
    --dropdown-text: #0d1021;
    --option-hover:  #fde047;
    --option-sel:    #facc15;
    --radius:    16px;
    --radius-sm: 10px;
}

/* ── Base ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--text) !important;
}

/* ── All block containers — prevent Streamlit injecting a dark/black bg on rerun ── */
[data-testid="stVerticalBlock"],
[data-testid="stVerticalFlexBlock"],
[data-testid="stHorizontalBlock"],
[data-testid="stColumn"],
[data-testid="column"],
[data-testid="stTabsContent"],
[data-baseweb="tab-panel"],
[data-testid="stMain"],
.main .block-container,
section[data-testid="stSidebar"] > div,
div[class*="stTabsContent"],
div[class*="block-container"] {
    background-color: transparent !important;
    color: var(--text) !important;
}

/* Ensure text inside all containers is always readable */
[data-testid="stVerticalBlock"] *,
[data-testid="stVerticalFlexBlock"] *,
[data-testid="stTabsContent"] *,
[data-baseweb="tab-panel"] * {
    color: inherit;
}
[data-testid="stVerticalBlock"] p,
[data-testid="stVerticalFlexBlock"] p,
[data-testid="stTabsContent"] p,
[data-baseweb="tab-panel"] p,
[data-testid="stVerticalBlock"] span,
[data-baseweb="tab-panel"] span {
    color: var(--text) !important;
}

/* ── Centre + constrain to iPhone 16 Plus width (430 px) desktop frame ── */
[data-testid="stMain"] > div:first-child,
[data-testid="stMainBlockContainer"] {
    max-width: 460px !important;
    margin: 0 auto !important;
    padding: 56px 16px 80px 16px !important;
}

/* ── Hide default streamlit chrome ── */
#MainMenu, footer,
[data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }

/* Keep header visible but transparent/dark — contains sidebar toggle */
[data-testid="stHeader"] {
    background: var(--bg) !important;
    border-bottom: 1px solid var(--border) !important;
    z-index: 999 !important;
}

/* Hide only the deploy/share/github icon buttons in header, keep sidebar toggle */
[data-testid="stHeader"] [data-testid="stActionButtonLabel"],
[data-testid="stHeader"] [data-testid^="stActionButton"]:not([data-testid="stSidebarCollapsedControl"]) {
    display: none !important;
}

/* ── Sidebar toggle — always visible, clean style ── */
[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 1000 !important;
}
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="stSidebarCollapseButton"] button {
    background: var(--card) !important;
    border: 1.5px solid var(--accent) !important;
    border-radius: 10px !important;
    width: 36px !important;
    height: 36px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="stSidebarCollapseButton"] svg {
    fill: var(--accent) !important;
    color: var(--accent) !important;
    width: 20px !important;
    height: 20px !important;
}

/* ── Sidebar → slide-in drawer feel ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 2px solid var(--accent3) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebarNavItems"] a {
    border-radius: var(--radius-sm) !important;
    padding: 10px 14px !important;
    margin: 2px 0 !important;
    font-weight: 600 !important;
    transition: background 0.15s, color 0.15s;
}
[data-testid="stSidebarNavItems"] a:hover {
    background: rgba(167,139,250,0.12) !important;
    color: var(--accent3) !important;
}
[data-testid="stSidebarNavItems"] a[aria-selected="true"] {
    background: rgba(52,211,153,0.12) !important;
    color: var(--accent) !important;
    border-left: 3px solid var(--accent) !important;
}

/* ── Typography ── */
h1 { font-size: 1.45rem !important; font-weight: 800 !important; letter-spacing: -0.3px; margin-bottom: 4px !important;
     background: linear-gradient(90deg, var(--accent), var(--accent2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
h2, h3 { font-size: 1.05rem !important; font-weight: 700 !important; color: var(--accent3) !important; }
p, li { font-size: 0.92rem !important; color: var(--text) !important; }

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, var(--card), var(--surface)) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 14px 12px !important;
    transition: border-color 0.2s;
}
[data-testid="stMetric"]:hover { border-color: var(--accent2) !important; }
[data-testid="stMetricLabel"] { font-size: 0.72rem !important; color: var(--accent2) !important; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700 !important; }
[data-testid="stMetricValue"] { font-size: 1.35rem !important; font-weight: 800 !important; color: var(--accent) !important; }
[data-testid="stMetricDelta"] svg { display:none; }    

/* ── Buttons ── */
[data-testid="stFormSubmitButton"] button,
[data-testid="stButton"] button {
    width: 100% !important;
    background: linear-gradient(135deg, var(--accent), #10b981) !important;
    color: #03140a !important;
    border: none !important;
    border-radius: 50px !important;
    font-weight: 800 !important;
    font-size: 0.95rem !important;
    padding: 12px 20px !important;
    letter-spacing: 0.3px;
    box-shadow: 0 4px 14px rgba(52,211,153,0.35);
    transition: filter 0.15s, transform 0.1s;
}
[data-testid="stFormSubmitButton"] button:hover,
[data-testid="stButton"] button:hover {
    filter: brightness(1.12);
    transform: translateY(-1px);
}
[data-testid="stFormSubmitButton"] button:active,
[data-testid="stButton"] button:active { transform: translateY(0); }

/* Secondary buttons (non-submit) */
[data-testid="stButton"] button[kind="secondary"] {
    background: transparent !important;
    border: 1.5px solid var(--accent2) !important;
    color: var(--accent2) !important;
    box-shadow: none !important;
}
/* Primary button accent */
button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent), #10b981) !important;
}

/* ── Inputs & selects ── */
input, textarea, select,
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stDateInput"] input {
    background: var(--card) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
    font-size: 0.92rem !important;
    padding: 10px 12px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: var(--accent2) !important;
    box-shadow: 0 0 0 3px rgba(56,189,248,0.22) !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within {
    border-color: var(--accent2) !important;
    box-shadow: 0 0 0 3px rgba(56,189,248,0.22) !important;
}

/* ── Selectbox trigger (closed state) ── */
[data-baseweb="select"] {
    background: var(--card) !important;
    border-radius: var(--radius-sm) !important;
}
[data-baseweb="select"] > div {
    background: var(--card) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
}
/* Selected value + placeholder text in the closed trigger — must stay light */
[data-testid="stSelectbox"] span,
[data-testid="stSelectbox"] div[class*="singleValue"],
[data-testid="stSelectbox"] div[class*="placeholder"],
[data-testid="stSelectbox"] [data-baseweb="select"] span,
[data-testid="stSelectbox"] [data-baseweb="select"] div,
[data-testid="stSelectbox"] [data-baseweb="select"] p,
[data-testid="stMultiSelect"] span,
[data-testid="stMultiSelect"] div[class*="singleValue"],
[data-testid="stMultiSelect"] [data-baseweb="select"] span,
[data-baseweb="select"] > div span,
[data-baseweb="select"] > div div[class*="Value"],
[data-baseweb="select"] > div [data-value] {
    color: var(--text) !important;
}
/* Dropdown arrow icon */
[data-baseweb="select"] svg { fill: var(--accent2) !important; color: var(--accent2) !important; }

/* ── Dropdown popover / menu panel ── */
[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="menu"] {
    background: var(--dropdown-bg) !important;
    border: 1.5px solid #f59e0b !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.55) !important;
    color: var(--dropdown-text) !important;
}
/* Each option row */
[data-baseweb="menu"] ul,
[data-baseweb="menu"] li,
[role="listbox"],
[role="option"],
li[data-baseweb="option"] {
    background: var(--dropdown-bg) !important;
    color: #0d1021 !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    border: none !important;
}
/* Make sure all text nodes inside menu options are dark */
[data-baseweb="menu"] span,
[data-baseweb="menu"] div,
[data-baseweb="menu"] p,
[role="listbox"] span,
[role="option"] span {
    color: #0d1021 !important;
}
/* Option hover */
li[data-baseweb="option"]:hover,
[role="option"]:hover,
[data-baseweb="option"]:hover {
    background: var(--option-hover) !important;
    color: #0d1021 !important;
    cursor: pointer;
}
/* Option selected/active */
li[data-baseweb="option"][aria-selected="true"],
[role="option"][aria-selected="true"] {
    background: var(--option-sel) !important;
    color: #0d1021 !important;
    font-weight: 800 !important;
}
/* Option focused via keyboard */
li[data-baseweb="option"]:focus,
[role="option"]:focus {
    background: var(--option-hover) !important;
    color: #0d1021 !important;
    outline: none !important;
}
/* Multiselect tag pill */
[data-baseweb="tag"] {
    background: rgba(56,189,248,0.18) !important;
    border: 1px solid var(--accent2) !important;
    border-radius: 50px !important;
    color: var(--accent2) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
}

/* ── Slider ── */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background: var(--accent2) !important;
    border-color: var(--accent2) !important;
    box-shadow: 0 0 0 3px rgba(56,189,248,0.25) !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] div[data-testid="stSliderThumbValue"] {
    color: var(--accent2) !important;
    font-weight: 700 !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] div[data-testid="stTickBar"] {
    display: none;
}

/* ── Forms ── */
[data-testid="stForm"] {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 16px !important;
    box-shadow: 0 2px 16px rgba(0,0,0,0.3);
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1.5px solid var(--accent3) !important;
    border-radius: var(--radius) !important;
}
[data-testid="stExpander"] summary {
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    color: var(--accent3) !important;
    padding: 12px 16px !important;
}
[data-testid="stExpander"] summary:hover { color: var(--text) !important; }
[data-testid="stExpander"] summary svg { fill: var(--accent3) !important; }

/* ── Dataframe / table ── */
[data-testid="stDataFrame"] {
    border-radius: var(--radius) !important;
    overflow: hidden;
    border: 1.5px solid var(--border) !important;
}
[data-testid="stDataFrame"] table { width: 100% !important; }
[data-testid="stDataFrame"] th {
    background: var(--card) !important;
    color: var(--accent2) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 10px 12px !important;
    border-bottom: 1.5px solid var(--accent2) !important;
}
[data-testid="stDataFrame"] td {
    background: var(--surface) !important;
    color: var(--text) !important;
    font-size: 0.88rem !important;
    padding: 10px 12px !important;
    border-bottom: 1px solid var(--border) !important;
}
[data-testid="stDataFrame"] tr:hover td { background: rgba(56,189,248,0.06) !important; }

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: var(--radius-sm) !important;
    font-size: 0.88rem !important;
    background: var(--surface) !important;
    color: var(--text) !important;
}
[data-testid="stSuccessAlert"]  { border-left: 4px solid var(--accent)  !important; background: rgba(52,211,153,0.08)  !important; }
[data-testid="stWarningAlert"]  { border-left: 4px solid var(--warn)    !important; background: rgba(251,191,36,0.08)   !important; }
[data-testid="stErrorAlert"]    { border-left: 4px solid var(--danger)  !important; background: rgba(248,113,113,0.08)  !important; }
[data-testid="stInfoAlert"]     { border-left: 4px solid var(--accent2) !important; background: rgba(56,189,248,0.08)   !important; }

/* ── Divider ── */
hr { border: none !important; border-top: 1.5px solid var(--border) !important; margin: 16px 0 !important; background: linear-gradient(90deg, var(--accent2), var(--accent3)) !important; height: 1.5px !important; opacity: 0.5; }

/* ── Tab / radio style selectors ── */
[data-baseweb="tab-list"] { background: var(--card) !important; border-radius: var(--radius-sm) !important; padding: 4px !important; }
[data-baseweb="tab"] { background: transparent !important; color: var(--muted) !important; border-radius: 8px !important; font-weight: 600 !important; transition: background 0.15s, color 0.15s; }
[data-baseweb="tab"]:hover { color: var(--accent2) !important; }
[aria-selected="true"][data-baseweb="tab"] { background: var(--accent2) !important; color: #03140a !important; }
[data-baseweb="tab-highlight"] { background: var(--accent2) !important; }
[data-baseweb="tab-border"] { background: transparent !important; }
/* Tab panel itself — always transparent so page bg shows through */
[data-baseweb="tab-panel"] {
    background: transparent !important;
    padding-top: 16px !important;
}

/* stMarkdownContainer inside tabs */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span {
    color: var(--text) !important;
}

/* ── Checkbox ── */
[data-testid="stCheckbox"] label { font-size: 0.88rem !important; color: var(--text) !important; text-transform: none !important; letter-spacing: normal !important; }
[data-testid="stCheckbox"] input:checked + div {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
}
[data-baseweb="checkbox"] [data-checked] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
}
/* Radio */
[data-testid="stRadio"] label { color: var(--text) !important; font-size: 0.9rem !important; text-transform: none !important; letter-spacing: normal !important; }
[data-baseweb="radio"] [data-checked] div { background: var(--accent2) !important; border-color: var(--accent2) !important; }

/* ── Label ── */
[data-testid="stWidgetLabel"], label { color: var(--accent2) !important; font-size: 0.78rem !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.5px; }

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
    color: #03140a;
    background: linear-gradient(135deg, var(--accent), #10b981);
    margin-left: 8px;
    box-shadow: 0 2px 8px rgba(52,211,153,0.3);
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
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 18px 8px !important;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
    text-decoration: none !important;
    min-height: 90px;
}
.nav-card:hover { border-color: var(--accent2) !important; background: rgba(56,189,248,0.07) !important; box-shadow: 0 4px 16px rgba(56,189,248,0.18) !important; }
.nav-card .icon { font-size: 1.8rem; margin-bottom: 6px; }
.nav-card .label { font-size: 0.78rem; font-weight: 700; color: var(--accent2); text-transform: uppercase; letter-spacing: 0.4px; }

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
    transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    color: var(--text) !important;
}
[data-testid="stPageLink"] a:hover {
    border-color: var(--accent2) !important;
    background: rgba(56,189,248,0.08) !important;
    box-shadow: 0 4px 16px rgba(56,189,248,0.18) !important;
    color: var(--accent2) !important;
}
</style>
""", unsafe_allow_html=True)
