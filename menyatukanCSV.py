import pandas as pd

# 1. Daftar nama file CSV yang ingin digabungkan
file_list = ['shopnesia_2021.csv', 'shopnesia_2022.csv', 'shopnesia_2023.csv']

# 2. Baca setiap file CSV dan simpan ke dalam list
df_list = [pd.read_csv(file) for file in file_list]

# 3. Gabungkan semua DataFrame menjadi satu
df_gabungan = pd.concat(df_list, ignore_index=True)

# 4. Simpan hasil gabungan ke file CSV baru
df_gabungan.to_csv('shopnesia_gabungan_2021_2023.csv', index=False)

print("Selesai! File telah berhasil disatukan menjadi 'shopnesia_gabungan_2021_2023.csv'")