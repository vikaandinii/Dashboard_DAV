import pandas as pd
import streamlit as st


def get_sorted_quarters(df, quarter_col='quarter'):
    """Kembalikan list kuartal terurut kronologis, misal ['2021Q1','2021Q2',...]."""
    return sorted(df[quarter_col].unique().tolist())


def compute_target(quarterly_series, current_quarter):
    """
    Hitung target otomatis untuk `current_quarter` berdasarkan:
    target = nilai_kuartal_sebelumnya * (1 + rata-rata growth rate historis
             dari semua transisi kuartal SEBELUM current_quarter)

    quarterly_series: pandas Series, index = quarter string terurut, value = metrik
    current_quarter: string kuartal yang sedang dipilih (misal '2022Q3')

    Return None kalau current_quarter adalah kuartal pertama dalam data
    (tidak ada basis historis untuk membuat target).
    """
    quarters = quarterly_series.index.tolist()
    if current_quarter not in quarters:
        return None
    idx = quarters.index(current_quarter)
    if idx == 0:
        return None

    prev_value = quarterly_series.iloc[idx - 1]
    growth_rates = quarterly_series.pct_change()
    # growth rate dari transisi-transisi SEBELUM current_quarter (tidak termasuk transisi ke current)
    growth_before = growth_rates.iloc[1:idx]
    avg_growth = growth_before.mean() if len(growth_before) > 0 else 0.0
    if pd.isna(avg_growth):
        avg_growth = 0.0

    return prev_value * (1 + avg_growth)


def metric_with_target(col, label, actual, target, fmt="{:,.0f}", lower_is_better=False, prefix="", suffix=""):
    """
    Render st.metric lengkap dengan perbandingan ke target otomatis + badge pencapaian.

    col: kolom streamlit (hasil st.columns())
    actual: nilai aktual kuartal terpilih
    target: hasil compute_target() (bisa None kalau kuartal pertama)
    fmt: format string angka, misal "{:,.0f}" atau "{:.1f}"
    lower_is_better: True untuk metrik yang bagus kalau kecil (delivery days, return rate, dst)
    """
    actual_str = f"{prefix}{fmt.format(actual)}{suffix}"

    if target is None or target == 0 or pd.isna(target):
        col.metric(label, actual_str)
        return

    target_str = f"{prefix}{fmt.format(target)}{suffix}"
    delta_pct = ((actual - target) / target) * 100
    delta_color = "inverse" if lower_is_better else "normal"

    tercapai = (actual <= target) if lower_is_better else (actual >= target)
    status = "Tercapai" if tercapai else "Belum Tercapai"

    col.metric(
        label=label,
        value=actual_str,
        delta=f"{delta_pct:+.1f}% | Tgt: {target_str}",
        delta_color=delta_color,
        help=(
            f"Status: {status}\n\n"
            f"Nilai Target: {target_str}\n\n"
            "Info: Target ini diproyeksikan secara otomatis oleh sistem "
            "berdasarkan tren rata-rata pertumbuhan dari periode-periode sebelumnya."
        )
    )


def format_month_id(month_year_str):
    """Ubah 'YYYY-MM' jadi label ramah seperti 'Okt 2023'."""
    _BULAN_ID = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'Mei', 6: 'Jun',
                 7: 'Jul', 8: 'Agu', 9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Des'}
    try:
        year, month = month_year_str.split('-')
        return f"{_BULAN_ID[int(month)]} {year}"
    except Exception:
        return month_year_str


def clean_heatmap_text(pivot_df, fmt):
    """
    Bikin matriks teks untuk go.Heatmap dari pivot table yang punya NaN,
    supaya sel kosong (NaN) tampil blank, bukan tulisan 'NaN'.
    fmt: fungsi format, misal lambda v: f"{v:.0f}%"
    """
    try:
        if hasattr(pivot_df, 'map'):
            return pivot_df.map(lambda v: "" if pd.isna(v) else fmt(v)).values
        else:
            return pivot_df.applymap(lambda v: "" if pd.isna(v) else fmt(v)).values
    except Exception:
        return pivot_df.values