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
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1440 250'%3E%3Cpath fill='%23818CF8' fill-opacity='1' d='M0,128L48,144C96,160,192,192,288,186.7C384,181,480,139,576,149.3C672,160,768,224,864,240C960,256,1056,224,1152,202.7C1248,181,1344,171,1392,165.3L1440,160L1440,0L1392,0C1344,0,1248,0,1152,0C1056,0,960,0,864,0C768,0,672,0,576,0C480,0,384,0,288,0C192,0,96,0,48,0L0,0Z'%3E%3C/path%3E%3C/svg%3E");
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
    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    margin-bottom: 1rem !important;
}

/* Filter select box */
div[data-testid="stSelectbox"] > div > div {
    background-color: rgba(255, 255, 255, 0.95) !important;
    border-radius: 12px !important;
    color: #1E293B !important;
    border: none !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
div[data-testid="stSelectbox"] label {
    color: #FFFFFF !important;
    font-weight: 600;
}


div[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border-radius: 16px;
    padding: 15px 20px !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important;
    border: 1px solid rgba(0,0,0,0.05);
    transition: none;
    margin-bottom: 0px !important;
}
div[data-testid="stMetric"]:hover {
    transform: none;
    box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important;
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

/* Remove background color (pill) from metric delta and adjust position */
div[data-testid="stMetricDelta"] {
    background-color: transparent !important;
    align-self: flex-start !important;
    margin-top: 5px !important;
    padding-bottom: 5px !important;
}
div[data-testid="stMetricDelta"] > div,
div[data-testid="stMetricDelta"] * {
    background-color: transparent !important;
    font-size: 0.95rem !important;
    line-height: 1.2 !important;
}

/* Markdown info boxes */
div.stMarkdown > div > div.stInfo {
    background-color: rgba(59, 130, 246, 0.1) !important;
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 12px;
    color: #1E3A8A !important;
}
/* Memastikan dropdown tahun tidak tertutup navigasi */
div[data-testid="stSelectbox"] {
    position: relative;
    z-index: 9999 !important;
}
div[data-testid="stPills"] {
    margin-bottom: 25px; /* Memberi jarak agar tidak mepet dengan logo */
    justify-content: center;
}

/* --- RESPONSIVE MOBILE TWEAKS --- */
@media (max-width: 768px) {
    /* Perkecil judul dashboard */
    h1 {
        font-size: 1.75rem !important;
    }
    
    /* Sesuaikan tinggi SVG Header agar tetap terlihat rapi */
    .stApp {
        background-size: 100% 200px;
    }
    
    /* Navigasi lebih ringkas di layar kecil */
    div[role="radiogroup"] {
        padding: 5px 10px;
        gap: 5px;
        border-radius: 15px;
    }
    div[data-testid="stPills"] {
        margin-bottom: 10px;
    }
    
    /* Logo penyesuaian */
    div.stMarkdown img {
        height: 80px !important;
    }
}
</style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data
def load_data():
    # Cache clear
    df = pd.read_csv("shopnesia_cleaned.csv")
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['year'] = df['order_date'].dt.year
    df['month_year'] = df['order_date'].dt.to_period('M').astype(str)
    df['quarter'] = df['order_date'].dt.to_period('Q').astype(str)
    # Kalkulasi net_revenue kasar: asumsikan final_price adalah harga setelah diskon (jika retur = 0, jika retur = kurangi final price)
    # Untuk simplifikasi net_revenue = final_price dimana is_returned == False
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("File 'shopnesia_cleaned.csv' tidak ditemukan. Pastikan file berada di direktori yang sama dengan app.py.")
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
    # Menggunakan komponen st.pills asli dari Streamlit agar sangat responsif di semua perangkat (termasuk HP)
    page = st.pills("Navigasi", ["Sales", "Marketing", "Operations & Logistics", "Finance"], default="Sales", label_visibility="collapsed")
    if not page:
        page = "Sales" # Fallback jika user mendeselect pill

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