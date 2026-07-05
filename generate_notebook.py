import nbformat as nbf
nb = nbf.v4.new_notebook()

text_intro = '''# Shopnesia Data Preprocessing & Cleaning
Notebook ini dibuat agar Anda lebih mudah memahami langkah-langkah pembersihan data (data cleaning).
Data mentah yang digunakan adalah `shopnesia_gabungan_2021_2023.csv`.'''

code_load = '''import pandas as pd

# 1. Memuat Data Mentah
df = pd.read_csv("shopnesia_gabungan_2021_2023.csv")
print("Total Baris Data Mentah:", len(df))
df.head()'''

text_missing = '''## Menangani Data yang Kosong (Missing Values)
Mari kita cek apakah ada data yang kosong (NaN). Jika ada, kita akan menghapusnya agar tidak merusak perhitungan di dashboard.'''

code_missing = '''# Cek jumlah data yang kosong per kolom
print("Jumlah Data Kosong sebelum dibersihkan:")
print(df.isnull().sum())

# Menghapus baris yang memiliki nilai kosong (NaN)
df = df.dropna()

print("\\nTotal Baris setelah menghapus data kosong:", len(df))'''

text_clean = '''## Normalisasi Kategori (Memperbaiki Typo)
Kita akan memperbaiki penulisan nama metode pembayaran, kategori produk, dan provinsi agar seragam.'''

code_clean = '''# Normalisasi Payment Method
payment_mapping = {
    'COD (Cash on Delivery)': 'COD', 'cod': 'COD',
    'transfer bank': 'Bank Transfer', 'Transfer Bank': 'Bank Transfer',
    'e-wallet': 'E-Wallet', 'Ewallet': 'E-Wallet', 'E-Wallet (GoPay/OVO/Dana)': 'E-Wallet'
}
df['payment_method'] = df['payment_method'].map(payment_mapping).fillna(df['payment_method'])

# Normalisasi Kategori Produk
category_mapping = {
    'sepatu ': 'Sepatu', 'atasaan': 'Atasan', 'asesoris': 'Aksesoris', 'aksesories': 'Aksesoris'
}
df['product_category'] = df['product_category'].str.lower().map(category_mapping).fillna(df['product_category'].str.title())

# Normalisasi Provinsi (Huruf Besar di Awal Kata)
df['customer_province'] = df['customer_province'].str.title()

print("Metode Pembayaran saat ini:", df['payment_method'].unique())
print("Kategori Produk saat ini:", df['product_category'].unique())'''

text_save = '''## Menyimpan Data Bersih
Terakhir, kita simpan data yang sudah rapi ini ke dalam file `shopnesia_cleaned.csv` yang nantinya akan dibaca oleh dashboard.'''

code_save = '''df.to_csv("shopnesia_cleaned.csv", index=False)
print("Data berhasil disimpan ke 'shopnesia_cleaned.csv'!")'''

nb['cells'] = [
    nbf.v4.new_markdown_cell(text_intro),
    nbf.v4.new_code_cell(code_load),
    nbf.v4.new_markdown_cell(text_missing),
    nbf.v4.new_code_cell(code_missing),
    nbf.v4.new_markdown_cell(text_clean),
    nbf.v4.new_code_cell(code_clean),
    nbf.v4.new_markdown_cell(text_save),
    nbf.v4.new_code_cell(code_save)
]

with open('Pembersihan_Data_Shopnesia.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
