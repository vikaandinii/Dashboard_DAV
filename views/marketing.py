import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import compute_target, metric_with_target, format_month_id, clean_heatmap_text

def render_marketing(filtered_df, df, period_type, selected_period):
    # --- KPI kuartal terpilih ---
    avg_discount = filtered_df['discount_percent'].mean()
    total_customers = filtered_df['customer_id'].nunique()
    total_orders = filtered_df['order_id'].nunique()
    avg_order_per_cust = total_orders / total_customers if total_customers > 0 else 0

    # --- Series full history untuk hitung target ---
    period_col = 'year' if period_type in ["Tahun", "Semua"] else 'quarter'
    q_discount_all = df.groupby(period_col)['discount_percent'].mean().sort_index()
    q_cust_all = df.groupby(period_col)['customer_id'].nunique().sort_index()
    q_orders_all = df.groupby(period_col)['order_id'].nunique().sort_index()
    q_opc_all = (q_orders_all / q_cust_all).sort_index()

    q_discount_all.index = q_discount_all.index.astype(str)
    q_cust_all.index = q_cust_all.index.astype(str)
    q_orders_all.index = q_orders_all.index.astype(str)
    q_opc_all.index = q_opc_all.index.astype(str)

    target_discount = compute_target(q_discount_all, selected_period)
    target_customers = compute_target(q_cust_all, selected_period)
    target_opc = compute_target(q_opc_all, selected_period)

    m1, m2, m3 = st.columns(3)
    metric_with_target(m1, "Rata-rata Diskon", avg_discount, target_discount, fmt="{:.1f}", suffix="%", lower_is_better=True)
    metric_with_target(m2, "Total Pelanggan", total_customers, target_customers, fmt="{:,.0f}")
    metric_with_target(m3, "Pesanan per Pelanggan", avg_order_per_cust, target_opc, fmt="{:.1f}", suffix="x")

    CH = 220
    MARGIN = dict(t=25, b=5, l=5, r=5)

    # ================== ROW 1 ==================
    r1c1, r1c2, r1c3 = st.columns(3)

    with r1c1:
        # Chart 1: Tren Pendapatan vs Diskon BULANAN di dalam kuartal terpilih
        monthly_mkt = filtered_df.groupby('month_year').apply(
            lambda x: pd.Series({
                'final_price': x['final_price'].sum(),
                'discount_percent': x['discount_percent'].mean()
            })
        ).reset_index().sort_values('month_year')
        monthly_mkt['label'] = monthly_mkt['month_year'].apply(format_month_id)

        fig_dual = go.Figure()
        fig_dual.add_trace(go.Bar(x=monthly_mkt['label'], y=monthly_mkt['final_price'], name='Pendapatan', marker_color='#818CF8', yaxis='y1'))
        fig_dual.add_trace(go.Scatter(x=monthly_mkt['label'], y=monthly_mkt['discount_percent'], name='Diskon (%)', mode='lines+markers', line=dict(color='#4F46E5', width=2), yaxis='y2'))
        fig_dual.update_layout(title=f'Pendapatan vs Diskon per Bulan ({selected_period})',
                               height=CH, margin=MARGIN, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                               yaxis=dict(title='', side='left', showgrid=False),
                               yaxis2=dict(title='', side='right', overlaying='y', showgrid=False),
                               showlegend=False, font=dict(size=9))
                               
        if target_discount is not None and not pd.isna(target_discount) and period_type != "Semua":
            fig_dual.add_hline(y=target_discount, line_dash="dash", line_color="#312E81", 
                               annotation_text=f"Target Diskon: {target_discount:.1f}%", 
                               annotation_position="top left", 
                               annotation_bgcolor="rgba(244, 247, 254, 0.8)",
                               annotation_bordercolor="#312E81",
                               annotation_borderwidth=1,
                               yref="y2")
        st.plotly_chart(fig_dual, use_container_width=True)

    with r1c2:
        # Chart 2: Scatter diskon vs kuantitas - snapshot kuartal terpilih
        sample_df = filtered_df.sample(n=min(3000, len(filtered_df)), random_state=42) if len(filtered_df) > 0 else filtered_df
        fig_scatter = px.scatter(sample_df, x='discount_percent', y='quantity', opacity=0.4, color='product_category',
                                 title=f"Diskon vs Kuantitas ({selected_period})", labels={'discount_percent': 'Diskon (%)', 'quantity': 'Qty'},
                                 color_discrete_sequence=['#6366F1', '#818CF8', '#A5B4FC', '#C7D2FE'])
        fig_scatter.update_layout(height=CH, margin=MARGIN, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                   showlegend=False, font=dict(size=10))
        st.plotly_chart(fig_scatter, use_container_width=True)

    with r1c3:
        # Chart 3: Histogram distribusi jumlah order per customer - snapshot kuartal terpilih
        orders_per_cust = filtered_df.groupby('customer_id')['order_id'].nunique().reset_index()
        fig_hist = px.histogram(orders_per_cust, x='order_id', nbins=10, title=f"Order per Customer ({selected_period})",
                                labels={'order_id': 'Jml Order', 'count': 'Jml Customer'},
                                color_discrete_sequence=['#6366F1'])
        fig_hist.update_layout(height=CH, margin=MARGIN, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(size=10))
        st.plotly_chart(fig_hist, use_container_width=True)

    # ================== ROW 2: Cohort heatmaps ==================
    cohort_df = df.copy()
    cohort_df['order_month_period'] = cohort_df['order_date'].dt.to_period('M')

    first_month = cohort_df.groupby('customer_id')['order_month_period'].min().rename('cohort_month')
    cohort_df = cohort_df.merge(first_month, on='customer_id')

    cohort_df['period_number'] = (cohort_df['order_month_period'] - cohort_df['cohort_month']).apply(lambda x: x.n)
    cohort_df['cohort_month_str'] = cohort_df['cohort_month'].astype(str)

    cust_counts = cohort_df.groupby(['cohort_month_str', 'period_number'])['customer_id'].nunique().reset_index()
    retention_pivot = cust_counts.pivot(index='cohort_month_str', columns='period_number', values='customer_id').sort_index()
    retention_pct = retention_pivot.divide(retention_pivot[0], axis=0) * 100

    rev_counts = cohort_df.groupby(['cohort_month_str', 'period_number'])['final_price'].sum().reset_index()
    revenue_pivot = rev_counts.pivot(index='cohort_month_str', columns='period_number', values='final_price').sort_index()

    if period_type == "Semua":
        selected_year = "Seluruh Waktu"
        valid_months = retention_pct.index.tolist()
    elif period_type == "Tahun":
        selected_year = str(selected_period)
        valid_months = [f"{selected_year}-{str(m).zfill(2)}" for m in range(1, 13)]
    else:
        selected_year = selected_period[:4]
        selected_q = selected_period[-2:]
        q_months = {
            'Q1': ['-01', '-02', '-03'],
            'Q2': ['-04', '-05', '-06'],
            'Q3': ['-07', '-08', '-09'],
            'Q4': ['-10', '-11', '-12']
        }
        valid_months = [f"{selected_year}{m}" for m in q_months.get(selected_q, [])]

    retention_pct = retention_pct[retention_pct.index.isin(valid_months)].dropna(axis=1, how='all')
    revenue_pivot = revenue_pivot[revenue_pivot.index.isin(valid_months)].dropna(axis=1, how='all')

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        fig_retention = go.Figure(data=go.Heatmap(
            z=retention_pct.values,
            x=[f"M+{c}" for c in retention_pct.columns],
            y=retention_pct.index,
            colorscale=[[0, '#EEF2FF'], [0.5, '#818CF8'], [1, '#4F46E5']],
            text=clean_heatmap_text(retention_pct, lambda v: f"{v:.0f}%"),
            texttemplate="%{text}",
            textfont={"size": 8},
            hoverongaps=False,
            hovertemplate="Cohort: %{y}<br>Bulan ke-: %{x}<br>Retention: %{z:.1f}%<extra></extra>",
            showscale=False
        ))
        fig_retention.update_layout(title=f"Cohort Retention (%) per Bulan - Tahun {selected_year}",
                                     height=CH, margin=MARGIN,
                                     plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                     font=dict(size=9))
        st.plotly_chart(fig_retention, use_container_width=True)

    with r2c2:
        fig_revenue = go.Figure(data=go.Heatmap(
            z=revenue_pivot.values,
            x=[f"M+{c}" for c in revenue_pivot.columns],
            y=revenue_pivot.index,
            colorscale=[[0, '#EEF2FF'], [0.5, '#6366F1'], [1, '#312E81']], # Diganti dari Pink ke Indigo/Ungu
            text=clean_heatmap_text(revenue_pivot, lambda v: f"{v/1e6:.1f}M"),
            texttemplate="%{text}",
            textfont={"size": 8},
            hoverongaps=False,
            hovertemplate="Cohort: %{y}<br>Bulan ke-: %{x}<br>Pendapatan: Rp %{z:,.0f}<extra></extra>",
            showscale=False
        ))
        fig_revenue.update_layout(title=f"Cohort Revenue (Rp) per Bulan - Tahun {selected_year}",
                                   height=CH, margin=MARGIN,
                                   plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                   font=dict(size=9))
        st.plotly_chart(fig_revenue, use_container_width=True)