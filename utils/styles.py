"""
Playo-style mobile-first CSS for StringerS Badminton Academy.
Call inject_mobile_css() at the top of every page after set_page_config().
"""
import streamlit as st


def inject_mobile_css():
    st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,1,0');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg:        #f8faf8;
    --surface:   #eef6ee;
    --card:      #ffffff;
    --border:    #d4e8d4;
    --accent:    #34a853;
    --accent2:   #1e8e3e;
    --accent3:   #0d652d;
    --warn:      #f9ab00;
    --danger:    #ea4335;
    --text:      #202124;
    --text-inv:  #ffffff;
    --muted:     #5f6368;
    --dropdown-bg:   #ffffff;
    --dropdown-text: #202124;
    --select-bg:     #ffffff;
    --option-hover:  #e8f5e9;
    --option-sel:    #c8e6c9;
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

/* ── Centre + constrain — responsive: wider on desktop, narrow on mobile ── */
[data-testid="stMain"] > div:first-child,
[data-testid="stMainBlockContainer"] {
    max-width: 700px !important;
    margin: 0 auto !important;
    padding: 16px 24px 180px 24px !important;
}
@media (max-width: 768px) {
    [data-testid="stMain"] > div:first-child,
    [data-testid="stMainBlockContainer"] {
        max-width: 500px !important;
        padding: 16px 16px 180px 16px !important;
    }
}

/* ── Hide default streamlit chrome ── */
#MainMenu, footer,
[data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }

/* ── Hide sidebar completely ── */
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarNavItems"],
section[data-testid="stSidebar"],
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
    width: 0 !important;
    min-width: 0 !important;
    max-width: 0 !important;
    overflow: hidden !important;
}

/* Hide header — no sidebar toggle needed anymore */
[data-testid="stHeader"] {
    display: none !important;
}

/* ── Fixed Bottom Nav Bar (Playo-style) ── */
.bottom-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 64px;
    background: #ffffff;
    border-top: 1px solid #e0e0e0;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    padding: 0 8px;
    box-shadow: 0 -2px 12px rgba(0,0,0,0.08);
}
.bottom-nav-inner {
    display: flex;
    align-items: center;
    justify-content: space-around;
    width: 100%;
    max-width: 500px;
}
.bottom-nav a {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-decoration: none !important;
    gap: 2px;
    flex: 1;
    padding: 6px 0;
    border-radius: 12px;
    transition: background 0.15s;
}
.bottom-nav a:hover {
    background: rgba(52,168,83,0.08);
}
.bottom-nav a .material-symbols-rounded {
    font-size: 26px;
    color: #5f6368;
    transition: color 0.15s;
}
.bottom-nav a.active .material-symbols-rounded {
    color: #34a853;
}
.bottom-nav a .nav-label {
    font-size: 0.65rem;
    font-weight: 600;
    color: #5f6368;
    letter-spacing: 0.2px;
    transition: color 0.15s;
}
.bottom-nav a.active .nav-label {
    color: #34a853;
    font-weight: 700;
}
.bottom-nav a.active {
    background: rgba(52,168,83,0.10);
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
    box-shadow: 0 1px 6px rgba(0,0,0,0.07);
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
    background: linear-gradient(135deg, var(--accent), #b45309) !important;
    color: #1c0a00 !important;
    border: none !important;
    border-radius: 50px !important;
    font-weight: 800 !important;
    font-size: 0.95rem !important;
    padding: 12px 20px !important;
    letter-spacing: 0.3px;
    box-shadow: 0 4px 14px rgba(217,119,6,0.30);
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
    background: linear-gradient(135deg, var(--accent), #92400e) !important;
}

/* ── Inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
textarea {
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-size: 0.92rem !important;
    padding: 10px 12px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: var(--accent2) !important;
    box-shadow: 0 0 0 3px rgba(234,88,12,0.22) !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within {
    border-color: var(--accent2) !important;
    box-shadow: 0 0 0 3px rgba(234,88,12,0.22) !important;
}

/* ── Selectbox glitch fixes ── */
/* Only style the outer trigger border/radius — config.toml owns the colours */
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
[data-testid="stMultiSelect"] [data-baseweb="select"] > div:focus-within {
    border-color: var(--accent2) !important;
    box-shadow: 0 0 0 3px rgba(234,88,12,0.22) !important;
}
/* Arrow icon */
[data-testid="stSelectbox"] svg,
[data-testid="stMultiSelect"] svg {
    fill: var(--accent2) !important;
}
/* Fix text layout inside trigger */
div[data-baseweb="select"] div[role="button"] {
    text-align: left !important;
    padding-left: 10px !important;
}
.stSelectbox div[data-baseweb="select"] > div:first-child {
    display: flex !important;
    align-items: center !important;
}
/* Hide the virtual focus indicator that renders as a ghost box */
[data-testid="stSelectboxVirtualFocus"] {
    display: none !important;
}

/* ── Dropdown popover / menu panel ── */
[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="menu"] {
    background: var(--dropdown-bg) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.12) !important;
    color: var(--dropdown-text) !important;
}
/* Each option row */
[data-baseweb="menu"] ul,
[data-baseweb="menu"] li,
[role="listbox"],
[role="option"],
li[data-baseweb="option"] {
    background: var(--dropdown-bg) !important;
    color: #292524 !important;
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
    color: #292524 !important;
}
/* Option hover */
li[data-baseweb="option"]:hover,
[role="option"]:hover,
[data-baseweb="option"]:hover {
    background: var(--option-hover) !important;
    color: #292524 !important;
    cursor: pointer;
}
/* Option selected/active */
li[data-baseweb="option"][aria-selected="true"],
[role="option"][aria-selected="true"] {
    background: var(--option-sel) !important;
    color: #292524 !important;
    font-weight: 800 !important;
}
/* Option focused via keyboard */
li[data-baseweb="option"]:focus,
[role="option"]:focus {
    background: var(--option-hover) !important;
    color: #292524 !important;
    outline: none !important;
}
/* Multiselect tag pill */
[data-baseweb="tag"] {
    background: rgba(234,88,12,0.15) !important;
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
    box-shadow: 0 0 0 3px rgba(234,88,12,0.25) !important;
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
    box-shadow: 0 2px 16px rgba(0,0,0,0.07);
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
[data-testid="stDataFrame"] tr:hover td { background: rgba(217,119,6,0.06) !important; }

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: var(--radius-sm) !important;
    font-size: 0.88rem !important;
    background: var(--surface) !important;
    color: var(--text) !important;
}
[data-testid="stSuccessAlert"]  { border-left: 4px solid var(--accent)  !important; background: rgba(5,150,105,0.08)    !important; }
[data-testid="stWarningAlert"]  { border-left: 4px solid var(--warn)    !important; background: rgba(217,119,6,0.08)    !important; }
[data-testid="stErrorAlert"]    { border-left: 4px solid var(--danger)  !important; background: rgba(220,38,38,0.08)    !important; }
[data-testid="stInfoAlert"]     { border-left: 4px solid var(--accent2) !important; background: rgba(234,88,12,0.08)    !important; }

/* ── Divider ── */
hr { border: none !important; border-top: 1.5px solid var(--border) !important; margin: 16px 0 !important; background: linear-gradient(90deg, var(--accent2), var(--accent3)) !important; height: 1.5px !important; opacity: 0.5; }

/* ── Tab / radio style selectors ── */
[data-baseweb="tab-list"] { background: var(--surface) !important; border-radius: var(--radius-sm) !important; padding: 4px !important; border: 1px solid var(--border) !important; }
[data-baseweb="tab"] { background: transparent !important; color: var(--text) !important; border-radius: 8px !important; font-weight: 600 !important; transition: background 0.15s, color 0.15s; }
[data-baseweb="tab"]:hover { color: var(--accent2) !important; }
[aria-selected="true"][data-baseweb="tab"] { background: var(--accent2) !important; color: #ffffff !important; }
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

/* ── Streamlit native grey text overrides — captions, help, placeholder, small text ── */
[data-testid="stCaptionContainer"] p,
[data-testid="stCaptionContainer"],
.st-emotion-cache-nahz7x,
[data-testid="stWidgetLabel"] small,
[data-testid="stText"],
[data-testid="stText"] p,
small,
.caption,
figcaption {
    color: #64748b !important;
}
/* Placeholder text in inputs */
input::placeholder,
textarea::placeholder {
    color: #94a3b8 !important;
    opacity: 0.9;
}
/* Number input +/- stepper buttons */
[data-testid="stNumberInput"] button {
    color: #64748b !important;
    border-color: #94a3b8 !important;
}
/* Help/info icon next to labels */
[data-testid="stTooltipIcon"] svg {
    fill: #64748b !important;
    color: #64748b !important;
}
/* st.caption() */
[data-testid="stCaptionContainer"] * { color: #64748b !important; }
/* Any remaining Streamlit muted/secondary text */
.st-emotion-cache-16idsys p,
.st-emotion-cache-1gulkj5,
[class*="caption"],
[class*="helpText"] {
    color: #64748b !important;
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
th { background: var(--surface); color: var(--accent2); padding: 8px 10px; text-align: left; font-size: 0.72rem; text-transform: uppercase; letter-spacing:0.5px; border-bottom: 1.5px solid var(--border); }
td { padding: 9px 10px; border-bottom: 1px solid var(--border); }

/* ── Keep columns horizontal on mobile (needed for bottom nav row) ── */

/* ── Skill badge pill ── */
.skill-badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 50px;
    font-size: 0.8rem;
    font-weight: 700;
    color: #ffffff;
    background: linear-gradient(135deg, var(--accent), #92400e);
    margin-left: 8px;
    box-shadow: 0 2px 8px rgba(217,119,6,0.30);
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
.nav-card:hover { border-color: var(--accent2) !important; background: rgba(234,88,12,0.06) !important; box-shadow: 0 4px 16px rgba(234,88,12,0.14) !important; }
.nav-card .icon { font-size: 1.8rem; margin-bottom: 6px; }
.nav-card .label { font-size: 0.78rem; font-weight: 700; color: var(--accent2); text-transform: uppercase; letter-spacing: 0.4px; }

/* st.page_link styling */
[data-testid="stPageLink"] a {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    background: #ffffff !important;
    border: 1px solid #e0e0e0 !important;
    border-radius: 12px !important;
    padding: 8px 4px !important;
    text-align: center !important;
    text-decoration: none !important;
    min-height: 56px !important;
    transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
    font-size: 0.74rem !important;
    font-weight: 700 !important;
    color: #202124 !important;
}
[data-testid="stPageLink"] a:hover {
    border-color: #34a853 !important;
    background: rgba(52,168,83,0.08) !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08) !important;
    color: #1e8e3e !important;
}

/* ── Fixed bottom row for nav rendered via st.page_link ── */
[data-testid="stVerticalBlock"]:has(.bottom-nav-sentinel) .bottom-nav-sentinel {
    display: none !important;
}

[data-testid="stVerticalBlock"]:has(.bottom-nav-sentinel) [data-testid="stHorizontalBlock"] {
    position: fixed !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(700px, 100vw) !important;
    bottom: 0 !important;
    z-index: 9999 !important;
    margin: 0 !important;
    padding: 6px 8px calc(6px + env(safe-area-inset-bottom)) 8px !important;
    background: #ffffff !important;
    border-top: 1px solid #e0e0e0 !important;
    box-shadow: 0 -2px 12px rgba(0,0,0,0.08) !important;
    display: flex !important;
    flex-wrap: nowrap !important;
    gap: 6px !important;
    box-sizing: border-box !important;
}

.bottom-nav-spacer {
    height: calc(90px + env(safe-area-inset-bottom)) !important;
}

[data-testid="stVerticalBlock"]:has(.bottom-nav-sentinel) [data-testid="stHorizontalBlock"] > div {
    min-width: 0 !important;
    flex: 1 1 0 !important;
}

[data-testid="stVerticalBlock"]:has(.bottom-nav-sentinel) [data-testid="stPageLink"] a {
    min-height: 52px !important;
    padding: 6px 2px !important;
    border: none !important;
    border-radius: 10px !important;
    background: transparent !important;
    box-shadow: none !important;
}

[data-testid="stVerticalBlock"]:has(.bottom-nav-sentinel) [data-testid="stPageLink"] a:hover {
    background: rgba(52,168,83,0.10) !important;
    color: #1e8e3e !important;
}

[data-testid="stVerticalBlock"]:has(.bottom-nav-sentinel) [data-testid="stPageLink"] a p {
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    margin-top: 2px !important;
    line-height: 1 !important;
}
</style>
""", unsafe_allow_html=True)
