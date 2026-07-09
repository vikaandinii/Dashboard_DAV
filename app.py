import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Shopnesia Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern dashboard matching the design references
st.markdown("""
<style>
/* Reset background with a soft modern color and a beautiful SVG wave header */
.stApp {
    background-color: #F4F7FE !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1440 250'%3E%3Cpath fill='%236366F1' fill-opacity='1' d='M0,128L48,144C96,160,192,192,288,186.7C384,181,480,139,576,149.3C672,160,768,224,864,240C960,256,1056,224,1152,202.7C1248,181,1344,171,1392,165.3L1440,160L1440,0L1392,0C1344,0,1248,0,1152,0C1056,0,960,0,864,0C768,0,672,0,576,0C480,0,384,0,288,0C192,0,96,0,48,0L0,0Z'%3E%3C/path%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-size: 100% 250px;
}

/* Custom Navbar Header */
header[data-testid="stHeader"] {background-color: transparent !important;}
.block-container {padding-top: 1.5rem !important; padding-bottom: 0rem !important;}

/* Title styling */
h1 {
    color: #FFFFFF !important;
    font-weight: 800 !important;
    font-size: 2.5rem !important;
    text-shadow: 1px 1px 4px rgba(0,0,0,0.1);
    margin-bottom: 1rem !important;
}

/* Filter select box */
div[data-testid="stSelectbox"] > div > div {
    background-color: rgba(255, 255, 255, 0.9) !important;
    border-radius: 12px !important;
    color: #1E293B !important;
    border: none !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    backdrop-filter: blur(5px);
}
div[data-testid="stSelectbox"] label {
    color: #FFFFFF !important;
    font-weight: 600;
}

/* Custom Radio Button styling to look like Pills (Top Navbar) */
div[role="radiogroup"] {
    position: relative;
    z-index: 1 !important;
    gap: 10px;
    background-color: rgba(255, 255, 255, 0.85);
    padding: 8px 15px;
    border-radius: 25px;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    margin-bottom: 25px; /* Memberi jarak agar tidak mepet dengan logo */
    justify-content: center;
}
div[role="radiogroup"] > label {
    background: transparent !important;
    color: #334155 !important;
    font-weight: 700;
    padding: 8px 16px;
    border-radius: 20px;
    transition: all 0.3s ease;
    cursor: pointer;
}
/* Hide the actual radio circle entirely */
div[role="radiogroup"] label > div:first-child,
div[role="radiogroup"] label > div:first-of-type,
div[role="radiogroup"] span[data-baseweb="radio"] > div:first-child {
    display: none !important;
}
div[role="radiogroup"] > label:hover {
    background-color: rgba(255, 255, 255, 0.2) !important;
}
div[role="radiogroup"] > label[data-checked="true"],
div[role="radiogroup"] > label:has(input:checked) {
    background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
    box-shadow: 0 4px 10px rgba(99, 102, 241, 0.4);
}
div[role="radiogroup"] > label[data-checked="true"] *,
div[role="radiogroup"] > label:has(input:checked) * {
    color: #FFFFFF !important;
}

/* Modern Metric Cards */
div[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border-radius: 16px;
    padding: 15px 30px !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.04) !important;
    border: 1px solid rgba(0,0,0,0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    height: 90px !important;
    position: relative !important;
    display: flex;
    flex-direction: column;
    justify-content: center;
    margin-bottom: 0px !important;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px rgba(0,0,0,0.08) !important;
}
div[data-testid="stMetric"] > div {
    color: #4F46E5 !important;
    font-weight: 800 !important;
}
div[data-testid="stMetricValue"] {
    font-size: 1.4rem !important;
}
div[data-testid="stMetric"] label, div[data-testid="stMetric"] p {
    color: #000000 !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    margin-bottom: 2px !important;
}

/* Remove background color (pill) from metric delta and move to bottom right */
div[data-testid="stMetricDelta"] {
    background-color: transparent !important;
    align-self: flex-end !important;
    margin-top: -10px !important; /* tarik sedikit ke atas agar lebih rapat */
}
div[data-testid="stMetricDelta"] > div,
div[data-testid="stMetricDelta"] * {
    background-color: transparent !important;
    font-size: 0.95rem !important;
}

/* Markdown info boxes */
div.stMarkdown > div > div.stInfo {
    background-color: rgba(59, 130, 246, 0.1) !important;
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 12px;
    color: #1E3A8A !important;
}
/* Memastikan dropdown tahun tidak tertutup radio button */
div[data-testid="stSelectbox"] {
    position: relative;
    z-index: 9999 !important;
}
div[role="radiogroup"] {
    position: relative;
    z-index: 1 !important;
}
</style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data
def load_data():
    df = pd.read_csv("shopnesia_cleaned.csv")
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['year'] = df['order_date'].dt.year
    df['month_year'] = df['order_date'].dt.to_period('M').astype(str)
    df['quarter'] = df['order_date'].dt.to_period('Q').astype(str)
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("File 'shopnesia_cleaned.csv' tidak ditemukan.")
    st.stop()

# --- TOP NAVBAR (SINGLE ROW) ---
def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""

logo_b64 = get_base64("logo_transparent.png")
logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height: 120px; vertical-align: middle;">' if logo_b64 else '🛍️'

col1, col2, col3 = st.columns([1.5, 3, 1])

with col1:
    st.markdown(f"<div style='display:flex; align-items:center; margin-top:-30px;'>{logo_html}</div>", unsafe_allow_html=True)

with col3:
    c3a, c3b = st.columns(2)
    with c3a:
        years = ["Semua Tahun"] + sorted([str(y) for y in df['year'].unique()])
        selected_year = st.selectbox("Tahun", years, index=len(years) - 1, label_visibility="collapsed")
    with c3b:
        if selected_year == "Semua Tahun":
            options = ["Sepanjang Waktu"]
            selected_q_option = st.selectbox("Kuartal", options, index=0, label_visibility="collapsed", disabled=True)
        else:
            quarters_in_year = sorted([q[-2:] for q in df['quarter'].unique() if q.startswith(selected_year)])
            options = ["Sepanjang Tahun"] + quarters_in_year
            default_index = len(options) - 1 if selected_year == years[-1] else 0
            selected_q_option = st.selectbox("Kuartal", options, index=default_index, label_visibility="collapsed")

if selected_year == "Semua Tahun":
    period_type = "Semua"
    selected_period = "Semua Tahun"
elif selected_q_option == "Sepanjang Tahun":
    period_type = "Tahun"
    selected_period = selected_year
else:
    period_type = "Kuartal"
    selected_period = f"{selected_year}{selected_q_option}"

with col2:
    page = st.radio("Navigasi", ["Sales", "Marketing", "Operations & Logistics", "Finance"], horizontal=True, label_visibility="collapsed")

# Terapkan filter global
if period_type == "Semua":
    filtered_df = df.copy()
elif period_type == "Tahun":
    filtered_df = df[df['year'].astype(str) == selected_period]
else:
    filtered_df = df[df['quarter'] == selected_period]

# ==========================================
# ROUTING PAGES
# ==========================================
if page == "Sales":
    import views.sales
    views.sales.render_sales(filtered_df, df, period_type, selected_period)
elif page == "Marketing":
    import views.marketing
    views.marketing.render_marketing(filtered_df, df, period_type, selected_period)
elif page == "Operations & Logistics":
    import views.operations
    views.operations.render_operations(filtered_df, df, period_type, selected_period)
elif page == "Finance":
    import views.finance
    views.finance.render_finance(filtered_df, df, period_type, selected_period)