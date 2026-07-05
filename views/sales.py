import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import compute_target, metric_with_target, format_month_id

def render_sales(filtered_df, df, period_type, selected_period):
    # --- Data kuartal ini (tidak termasuk retur) ---
    sales_df = filtered_df[filtered_df['is_returned'] == False]
    total_revenue = sales_df['final_price'].sum()
    total_transactions = sales_df['order_id'].nunique()
    aov = total_revenue / total_transactions if total_transactions > 0 else 0
    total_quantity = sales_df['quantity'].sum()

    # --- Data full history (tidak difilter kuartal) untuk hitung target ---
    full_sales = df[df['is_returned'] == False]
    period_col = 'year' if period_type in ["Tahun", "Semua"] else 'quarter'

    q_revenue_all = full_sales.groupby(period_col)['final_price'].sum().sort_index()
    q_orders_all = full_sales.groupby(period_col)['order_id'].nunique().sort_index()
    q_aov_all = (q_revenue_all / q_orders_all).sort_index()
    q_qty_all = full_sales.groupby(period_col)['quantity'].sum().sort_index()

    q_revenue_all.index = q_revenue_all.index.astype(str)
    q_orders_all.index = q_orders_all.index.astype(str)
    q_aov_all.index = q_aov_all.index.astype(str)
    q_qty_all.index = q_qty_all.index.astype(str)

    target_revenue = compute_target(q_revenue_all, selected_period)
    target_aov = compute_target(q_aov_all, selected_period)
    target_qty = compute_target(q_qty_all, selected_period)

    quarters_sorted = q_revenue_all.index.tolist()
    idx = quarters_sorted.index(selected_period) if selected_period in quarters_sorted else -1
    if idx > 0:
        qoq_growth = ((q_revenue_all.iloc[idx] - q_revenue_all.iloc[idx - 1]) / q_revenue_all.iloc[idx - 1]) * 100
    else:
        qoq_growth = None

    if period_type == "Tahun":
        delta_text = "vs tahun sebelumnya"
        growth_label = "Pertumbuhan YoY"
    elif period_type == "Semua":
        delta_text = ""
        growth_label = "Pertumbuhan"
    else:
        delta_text = "vs kuartal sebelumnya"
        growth_label = "Pertumbuhan QoQ"

    m1, m2, m3, m4 = st.columns(4)
    metric_with_target(m1, "Total Pendapatan", total_revenue, target_revenue, fmt="{:,.0f}", prefix="Rp ")
    if qoq_growth is not None:
        m2.metric(growth_label, f"{qoq_growth:+.1f}%", delta=delta_text, delta_color="off")
    else:
        m2.metric(growth_label, "N/A")
    metric_with_target(m3, "Rata-rata Nilai Pesanan", aov, target_aov, fmt="{:,.0f}", prefix="Rp ")
    metric_with_target(m4, "Kuantitas Terjual", total_quantity, target_qty, fmt="{:,.0f}")

    # ================== ROW 1 ==================
    r1c1, r1c2 = st.columns([2, 1])
    
    with r1c1:
        # Chart 1a: Tren Penjualan BULANAN
        monthly_sales = sales_df.groupby('month_year')['final_price'].sum().reset_index().sort_values('month_year')
        monthly_sales['label'] = monthly_sales['month_year'].apply(format_month_id)

        fig_sales = px.line(monthly_sales, x='label', y='final_price', markers=True,
                            title=f"Tren Penjualan Bulanan ({selected_period})",
                            labels={'final_price': 'Pendapatan (Rp)', 'label': 'Bulan'},
                            color_discrete_sequence=['#818CF8'])
                            
        if target_revenue is not None and not pd.isna(target_revenue) and period_type != "Semua":
            num_months = 12 if period_type == "Tahun" else 3
            monthly_target = target_revenue / num_months
            fig_sales.add_hline(y=monthly_target, line_dash="dash", line_color="#A5B4FC", 
                                annotation_text=f"Target: Rp {monthly_target/1e6:.1f}M", 
                                annotation_position="top left")

        fig_sales.update_traces(line=dict(width=3), marker=dict(size=10))
        fig_sales.update_layout(height=230, margin=dict(t=25, b=0, l=10, r=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_sales, use_container_width=True)

    with r1c2:
        # Chart 1b: Pendapatan per Tingkat Brand (Donut)
        brand_sales = sales_df.groupby('brand_tier')['final_price'].sum().reset_index()
        fig_brand = px.pie(brand_sales, names='brand_tier', values='final_price', hole=0.5,
                           title=f"Pendapatan per Brand ({selected_period})",
                           color_discrete_sequence=['#6366F1', '#818CF8', '#A5B4FC', '#C7D2FE'])
        fig_brand.update_layout(height=230, margin=dict(t=25, b=0, l=10, r=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        fig_brand.update_traces(textposition='inside', textinfo='percent+label', showlegend=False)
        st.plotly_chart(fig_brand, use_container_width=True)

    # ================== ROW 2 ==================
    c1, c2 = st.columns(2)
    with c1:
        # Chart 2: Bar chart growth revenue per kategori (2021 vs 2023) - perbandingan tahunan, tidak terikat kuartal
        df_compare = df[(df['year'].isin([2021, 2023])) & (df['is_returned'] == False)]
        if not df_compare.empty:
            cat_compare = df_compare.groupby(['product_category', 'year'])['final_price'].sum().reset_index()
            cat_compare['year'] = cat_compare['year'].astype(str)
            cat_compare['label_text'] = cat_compare['final_price'].apply(lambda x: f"{x/1e9:.1f} Miliar" if x >= 1e9 else f"{x/1e6:.0f} Juta")
            fig_cat = px.bar(cat_compare, x='product_category', y='final_price', color='year', barmode='group',
                             title="Pertumbuhan Pendapatan per Kategori (2021 vs 2023)", text='label_text',
                             labels={'final_price': 'Pendapatan (Rp)', 'product_category': 'Kategori'},
                             color_discrete_sequence=['#A5B4FC', '#6366F1'])
            fig_cat.update_layout(height=230, margin=dict(t=35, b=0, l=10, r=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', legend_title_text='')
            fig_cat.update_traces(textposition='outside', textfont_size=9, cliponaxis=False)
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("Data 2021/2023 tidak lengkap untuk dibandingkan.")

    with c2:
        # Chart 3: Treemap revenue per provinsi - snapshot kuartal terpilih
        loc_col = 'customer_province'
        prov_sales = sales_df.groupby(loc_col)['final_price'].sum().reset_index()
        prov_sales = prov_sales.sort_values('final_price', ascending=False)
        top5_provs = prov_sales.head(5)[loc_col].tolist()

        labels = ["Total Revenue"]
        parents = [""]
        values = [prov_sales['final_price'].sum()]

        for prov in top5_provs:
            val = prov_sales[prov_sales[loc_col] == prov]['final_price'].values[0]
            labels.append(prov)
            parents.append("Total Revenue")
            values.append(val)

        others = prov_sales[~prov_sales[loc_col].isin(top5_provs)]
        if not others.empty:
            others_total = others['final_price'].sum()
            labels.append("Lainnya")
            parents.append("Total Revenue")
            values.append(others_total)

            for _, row in others.iterrows():
                label_name = row[loc_col] + " "
                labels.append(label_name)
                parents.append("Lainnya")
                values.append(row['final_price'])

        fig_prov = go.Figure(go.Treemap(
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            textinfo="label+percent parent",
            textfont=dict(color='#FFFFFF', size=12),
            marker=dict(colors=["#4338CA", "#4F46E5", "#6366F1", "#818CF8", "#A5B4FC", "#C7D2FE"] * (len(labels)//6 + 1)),
            maxdepth=2
        ))
        fig_prov.update_layout(title=f"Proporsi Pendapatan per Provinsi ({selected_period})", height=230, margin=dict(t=45, b=0, l=10, r=10))
        st.plotly_chart(fig_prov, use_container_width=True)