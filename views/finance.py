import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import compute_target, metric_with_target, format_month_id

def render_finance(filtered_df, df, period_type, selected_period):
    # --- KPI kuartal terpilih ---
    gross_revenue = filtered_df['price'].sum()
    total_discount_value = filtered_df['price'].sum() - filtered_df['final_price'].sum()
    return_loss = filtered_df[filtered_df['is_returned'] == True]['final_price'].sum()
    net_revenue = filtered_df[filtered_df['is_returned'] == False]['final_price'].sum()

    # --- Series full history untuk hitung target ---
    def quarterly_calc(x):
        return pd.Series({
            'gross_revenue': x['price'].sum(),
            'net_revenue': x[x['is_returned'] == False]['final_price'].sum(),
            'discount_value': x['price'].sum() - x['final_price'].sum(),
            'return_loss': x[x['is_returned'] == True]['final_price'].sum(),
        })

    period_col = 'year' if period_type in ["Tahun", "Semua"] else 'quarter'
    q_fin_all = df.groupby(period_col).apply(quarterly_calc).sort_index()

    q_fin_all.index = q_fin_all.index.astype(str)

    target_gross = compute_target(q_fin_all['gross_revenue'], selected_period)
    target_net = compute_target(q_fin_all['net_revenue'], selected_period)
    target_discount = compute_target(q_fin_all['discount_value'], selected_period)
    target_loss = compute_target(q_fin_all['return_loss'], selected_period)

    m1, m2, m3, m4 = st.columns(4)
    metric_with_target(m1, "Pendapatan Kotor", gross_revenue, target_gross, fmt="{:,.0f}", prefix="Rp ")
    metric_with_target(m2, "Pendapatan Bersih", net_revenue, target_net, fmt="{:,.0f}", prefix="Rp ")
    metric_with_target(m3, "Total Nilai Diskon", total_discount_value, target_discount, fmt="{:,.0f}", prefix="Rp ", lower_is_better=True)
    metric_with_target(m4, "Kerugian Retur", return_loss, target_loss, fmt="{:,.0f}", prefix="Rp ", lower_is_better=True)

    # ================== ROW 1 ==================
    r1c1, r1c2 = st.columns([2, 1])

    with r1c1:
        # Chart 1a: Tren Gross vs Net Revenue BULANAN + garis discount rate
        monthly_fin = filtered_df.groupby('month_year').apply(
            lambda x: pd.Series({
                'gross_revenue': x['price'].sum(),
                'net_revenue': x[x['is_returned'] == False]['final_price'].sum(),
                'discount_percent': x['discount_percent'].mean()
            })
        ).reset_index().sort_values('month_year')
        monthly_fin['label'] = monthly_fin['month_year'].apply(format_month_id)

        fig_fin_area = go.Figure()
        fig_fin_area.add_trace(go.Scatter(x=monthly_fin['label'], y=monthly_fin['gross_revenue'], fill='tozeroy', name='Pendapatan Kotor', mode='lines+markers', fillcolor='rgba(99, 102, 241, 0.4)', line=dict(color='#6366F1'), yaxis='y1'))
        fig_fin_area.add_trace(go.Scatter(x=monthly_fin['label'], y=monthly_fin['net_revenue'], fill='tozeroy', name='Pendapatan Bersih', mode='lines+markers', fillcolor='rgba(129, 140, 248, 0.6)', line=dict(color='#818CF8'), yaxis='y1'))
        fig_fin_area.add_trace(go.Scatter(x=monthly_fin['label'], y=monthly_fin['discount_percent'], name='Tingkat Diskon (%)', mode='lines+markers', line=dict(color='#312E81', width=3), yaxis='y2'))
        fig_fin_area.update_layout(title=f'Pendapatan Kotor & Bersih vs Diskon per Bulan ({selected_period})',
                               height=230, margin=dict(t=45, b=0, l=10, r=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                               yaxis=dict(title='Pendapatan (Rp)', side='left', showgrid=False),
                               yaxis2=dict(title='Tingkat Diskon (%)', side='right', overlaying='y', showgrid=False),
                               legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_fin_area, use_container_width=True)

    with r1c2:
        # Chart 1b: Beban Diskon per Kategori Produk
        fin_discount = filtered_df.copy()
        fin_discount['discount_value'] = fin_discount['price'] - fin_discount['final_price']
        disc_cat = fin_discount.groupby('product_category')['discount_value'].sum().reset_index()
        disc_cat = disc_cat.sort_values('discount_value', ascending=True)
        fig_disc_cat = px.bar(disc_cat, x='discount_value', y='product_category', orientation='h',
                              title=f"Beban Diskon per Kategori ({selected_period})",
                              color='discount_value',
                              labels={'discount_value': 'Total Diskon (Rp)', 'product_category': 'Kategori'},
                              text_auto='.2s', color_continuous_scale=['#E0E6ED', '#4F46E5'])
        fig_disc_cat.update_layout(height=230, margin=dict(t=45, b=0, l=10, r=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
        fig_disc_cat.update_traces(textposition='outside', cliponaxis=False)
        st.plotly_chart(fig_disc_cat, use_container_width=True)

    # ================== ROW 2 ==================
    c1, c2 = st.columns(2)
    with c1:
        # Chart 2: Bar Chart Return loss per brand tier - snapshot kuartal terpilih
        loss_df = filtered_df[filtered_df['is_returned'] == True].groupby('brand_tier')['final_price'].sum().reset_index()
        if not loss_df.empty:
            fig_loss = px.bar(loss_df, x='brand_tier', y='final_price', title=f"Kerugian Retur per Tingkat Brand ({selected_period})",
                              color='final_price',
                              text_auto='.2s', labels={'final_price': 'Kerugian (Rp)', 'brand_tier': 'Tingkat Brand'},
                              color_continuous_scale=['#E0E6ED', '#6366F1'])
            fig_loss.update_layout(height=230, margin=dict(t=45, b=0, l=10, r=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
            st.plotly_chart(fig_loss, use_container_width=True)
        else:
            st.info("Tidak ada data retur untuk kuartal ini.")

    with c2:
        # Chart 3: Bar Horizontal Metode Pembayaran - snapshot kuartal terpilih
        filtered_df_pay = filtered_df.copy()
        filtered_df_pay['payment_method'] = filtered_df_pay['payment_method'].str.replace('_', ' ').str.title()
        payment_counts = filtered_df_pay.groupby('payment_method').agg(Jumlah=('order_id', 'count'), Avg_Value=('final_price', 'mean')).reset_index()
        payment_counts = payment_counts.sort_values('Jumlah', ascending=True)

        fig_pay = px.bar(payment_counts, x='Jumlah', y='payment_method', orientation='h',
                             title=f"Preferensi Metode Pembayaran ({selected_period})", color='Jumlah', hover_data=['Avg_Value'],
                             labels={'payment_method': 'Metode Pembayaran', 'Jumlah': 'Jumlah Transaksi'},
                             color_continuous_scale=['#E0E6ED', '#4F46E5'])
        fig_pay.update_layout(height=230, margin=dict(t=45, b=0, l=10, r=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_pay, use_container_width=True)