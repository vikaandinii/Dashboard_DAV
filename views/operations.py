import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import compute_target, metric_with_target, format_month_id

def render_operations(filtered_df, df, period_type, selected_period):
    # --- KPI kuartal terpilih ---
    avg_delivery = filtered_df['delivery_days'].mean()
    avg_shipping = filtered_df['shipping_cost'].mean()
    return_rate = (filtered_df['is_returned'].sum() / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0

    # --- Series full history untuk hitung target ---
    period_col = 'year' if period_type in ["Tahun", "Semua"] else 'quarter'
    q_delivery_all = df.groupby(period_col)['delivery_days'].mean().sort_index()
    q_shipping_all = df.groupby(period_col)['shipping_cost'].mean().sort_index()
    q_return_all = (df.groupby(period_col)['is_returned'].mean() * 100).sort_index()

    q_delivery_all.index = q_delivery_all.index.astype(str)
    q_shipping_all.index = q_shipping_all.index.astype(str)
    q_return_all.index = q_return_all.index.astype(str)

    target_delivery = compute_target(q_delivery_all, selected_period)
    target_shipping = compute_target(q_shipping_all, selected_period)
    target_return = compute_target(q_return_all, selected_period)

    m1, m2, m3 = st.columns(3)
    metric_with_target(m1, "Rata-rata Lama Pengiriman", avg_delivery, target_delivery, fmt="{:.1f}", suffix=" Hari", lower_is_better=True)
    metric_with_target(m2, "Tingkat Retur Keseluruhan", return_rate, target_return, fmt="{:.1f}", suffix="%", lower_is_better=True)
    metric_with_target(m3, "Rata-rata Ongkos Kirim", avg_shipping, target_shipping, fmt="{:,.0f}", prefix="Rp ", lower_is_better=True)

    c1, c2 = st.columns(2)
    with c1:
        # Chart 1: Bar Chart Alasan Retur - snapshot kuartal terpilih
        return_df = filtered_df[filtered_df['is_returned'] == True]
        if not return_df.empty:
            return_reason_counts = return_df['return_reason'].value_counts().reset_index()
            return_reason_counts.columns = ['Alasan', 'Jumlah']
            fig_return = px.bar(return_reason_counts, x='Alasan', y='Jumlah', title=f"Alasan Retur Tertinggi ({selected_period})",
                                color='Jumlah',
                                text_auto=True, color_continuous_scale=['#E0E6ED', '#0F2545'])
            fig_return.update_layout(height=230, margin=dict(t=25, b=0, l=10, r=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
            st.plotly_chart(fig_return, use_container_width=True)
        else:
            st.info("Tidak ada data retur untuk kuartal ini.")

    with c2:
        # Chart 2: Bar Chart Lama Pengiriman (Top 10 Lambat) - snapshot kuartal terpilih
        delivery_df = filtered_df.groupby('customer_province')['delivery_days'].mean().reset_index()
        delivery_df = delivery_df.sort_values('delivery_days', ascending=False)
        if not delivery_df.empty:
            target_q3 = delivery_df['delivery_days'].quantile(0.75)
            max_delivery = delivery_df['delivery_days'].max()

            top10_lambat = delivery_df.head(10).sort_values('delivery_days', ascending=True)
            fig_delivery = px.bar(top10_lambat, x='delivery_days', y='customer_province', orientation='h',
                                  title=f"Top 10 Pengiriman Terlama ({selected_period})", text_auto='.1f',
                                  labels={'delivery_days': 'Rata-rata Hari', 'customer_province': 'Provinsi'})
            fig_delivery.add_vline(x=target_q3, line_dash="dash", line_color="#2B5A96", annotation_text=f"Target: {target_q3:.1f}")
            fig_delivery.update_traces(marker_color=['#0B1A30' if x == max_delivery else '#2B5A96' for x in top10_lambat['delivery_days']])
            fig_delivery.update_layout(height=230, margin=dict(t=25, b=0, l=10, r=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_delivery, use_container_width=True)
        else:
            st.info("Tidak ada data pengiriman untuk kuartal ini.")

    # ================== ROW 2 ==================
    c3, c4 = st.columns([2, 1])
    
    with c3:
        # Chart 3a: Tren Volume Pesanan vs Return Rate BULANAN
        monthly_ops = filtered_df.groupby('month_year').agg({'order_id': 'nunique', 'is_returned': 'mean'}).reset_index()
        monthly_ops['is_returned'] = monthly_ops['is_returned'] * 100
        monthly_ops = monthly_ops.sort_values('month_year')
        monthly_ops['label'] = monthly_ops['month_year'].apply(format_month_id)

        fig_ops = go.Figure()
        fig_ops.add_trace(go.Bar(x=monthly_ops['label'], y=monthly_ops['order_id'], name='Volume Pesanan', marker_color='#2B5A96', yaxis='y1'))
        fig_ops.add_trace(go.Scatter(x=monthly_ops['label'], y=monthly_ops['is_returned'], name='Tingkat Retur (%)', mode='lines+markers', line=dict(color='#0B1A30', width=3), yaxis='y2'))
        fig_ops.update_layout(title=f'Volume Pesanan vs Tingkat Retur per Bulan ({selected_period})',
                               height=230, margin=dict(t=25, b=0, l=10, r=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                               yaxis=dict(title='Volume Pesanan', side='left', showgrid=False),
                               yaxis2=dict(title='Tingkat Retur (%)', side='right', overlaying='y', showgrid=False),
                               legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_ops, use_container_width=True)

    with c4:
        # Chart 3b: Pengiriman Tercepat per Kategori Produk
        fast_delivery = filtered_df.groupby('product_category')['delivery_days'].mean().reset_index().sort_values('delivery_days', ascending=True)
        fig_fast = px.bar(fast_delivery, x='product_category', y='delivery_days',
                          title=f"Lama Pengiriman per Kategori ({selected_period})", text_auto='.1f',
                          color='delivery_days',
                          labels={'delivery_days': 'Hari', 'product_category': 'Kategori'},
                          color_continuous_scale=['#E0E6ED', '#183B68'])
        
        # Zoom the y-axis to make small differences visible
        min_y = fast_delivery['delivery_days'].min() - 0.2
        max_y = fast_delivery['delivery_days'].max() + 0.3
        fig_fast.update_layout(height=230, margin=dict(t=25, b=0, l=10, r=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
        fig_fast.update_yaxes(range=[min_y, max_y])
        fig_fast.update_traces(textposition='outside', cliponaxis=False)
        st.plotly_chart(fig_fast, use_container_width=True)