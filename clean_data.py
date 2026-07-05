import pandas as pd
import nbformat as nbf

# 1. GENERATE JUPYTER NOTEBOOK
nb = nbf.v4.new_notebook()

text = """\
# Shopnesia Data Preprocessing & Cleaning
Notebook ini digunakan untuk membersihkan data mentah dari `shopnesia_gabungan_2021_2023.csv` sebelum digunakan oleh dashboard Streamlit.
"""

code_1 = """\
import pandas as pd

# Load data
df = pd.read_csv('shopnesia_gabungan_2021_2023.csv')
print("Total Baris Sebelum Cleaning:", len(df))
print("\\nNilai Unik Payment Method Sebelum Cleaning:")
print(df['payment_method'].unique())
"""

code_2 = """\
# Normalisasi Payment Method
# Mapping berbagai inkonsistensi penulisan ke format standar
payment_mapping = {
    'COD (Cash on Delivery)': 'COD',
    'COD': 'COD',
    'cod': 'COD',
    'Transfer Bank': 'Bank Transfer',
    'transfer bank': 'Bank Transfer',
    'Bank Transfer': 'Bank Transfer',
    'E-Wallet (GoPay/OVO/Dana)': 'E-Wallet',
    'E-Wallet': 'E-Wallet',
    'e-wallet': 'E-Wallet',
    'Ewallet': 'E-Wallet',
    'Paylater': 'Paylater',
    'Kartu Kredit': 'Kartu Kredit'
}

df['payment_method'] = df['payment_method'].map(payment_mapping).fillna(df['payment_method'])

print("\\nNilai Unik Payment Method Setelah Cleaning:")
print(df['payment_method'].unique())
"""

code_3 = """\
# Normalisasi Kategori Produk
category_mapping = {
    'sepatu ': 'Sepatu', 'sepatu': 'Sepatu',
    'atasan': 'Atasan', 'atasaan': 'Atasan',
    'bawahan': 'Bawahan',
    'tas': 'Tas',
    'aksesoris': 'Aksesoris', 'asesoris': 'Aksesoris', 'aksesories': 'Aksesoris'
}
df['product_category'] = df['product_category'].str.lower().map(category_mapping).fillna(df['product_category'].str.title())

# Normalisasi Provinsi (Menyamakan format Title Case)
df['customer_province'] = df['customer_province'].str.title()

# Simpan data yang telah dibersihkan
df.to_csv('shopnesia_cleaned.csv', index=False)
print("\\nData berhasil disimpan ke 'shopnesia_cleaned.csv'")
"""

nb['cells'] = [
    nbf.v4.new_markdown_cell(text),
    nbf.v4.new_code_cell(code_1),
    nbf.v4.new_code_cell(code_2),
    nbf.v4.new_code_cell(code_3)
]

with open('preprocessing.ipynb', 'w') as f:
    nbf.write(nb, f)

print("Berhasil membuat preprocessing.ipynb")

# 2. EKSEKUSI PROSES CLEANING UNTUK MENGHASILKAN CSV
df = pd.read_csv('shopnesia_gabungan_2021_2023.csv')
payment_mapping = {
    'COD (Cash on Delivery)': 'COD', 'COD': 'COD', 'cod': 'COD',
    'Transfer Bank': 'Bank Transfer', 'transfer bank': 'Bank Transfer', 'Bank Transfer': 'Bank Transfer',
    'E-Wallet (GoPay/OVO/Dana)': 'E-Wallet', 'E-Wallet': 'E-Wallet', 'e-wallet': 'E-Wallet', 'Ewallet': 'E-Wallet',
    'Paylater': 'Paylater', 'Kartu Kredit': 'Kartu Kredit'
}
df['payment_method'] = df['payment_method'].map(payment_mapping).fillna(df['payment_method'])
category_mapping = {
    'sepatu ': 'Sepatu', 'sepatu': 'Sepatu',
    'atasan': 'Atasan', 'atasaan': 'Atasan',
    'bawahan': 'Bawahan',
    'tas': 'Tas',
    'aksesoris': 'Aksesoris', 'asesoris': 'Aksesoris', 'aksesories': 'Aksesoris'
}
df['product_category'] = df['product_category'].str.lower().map(category_mapping).fillna(df['product_category'].str.title())
df['customer_province'] = df['customer_province'].str.title()
df.to_csv('shopnesia_cleaned.csv', index=False)

print("Berhasil menghasilkan shopnesia_cleaned.csv")
