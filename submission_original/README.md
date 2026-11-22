# Proyek Analisis Data E-Commerce

**Nama:** `ISI NAMA ANDA`  
**Email:** `ISI EMAIL ANDA`  
**ID Dicoding:** `ISI ID DICODING ANDA`

Proyek ini dibuat mandiri dari dataset Olist untuk menjawab dua kebutuhan bisnis pada periode pembelian 1 Januari 2017–31 Agustus 2018.

1. Wilayah mana yang patut diprioritaskan untuk evaluasi logistik berdasarkan tingkat keterlambatan pengiriman, dan bagaimana perbedaan ulasan pelanggan antara pesanan tepat waktu dan terlambat?
2. Bagaimana pelanggan dapat dikelompokkan dengan RFM agar strategi retensi atau aktivasi ulang lebih terarah?

Analisis lanjutan menggunakan RFM dengan pengelompokan manual; tidak ada machine learning. Nilai monetary adalah total harga item dalam BRL tanpa ongkir. Dashboard hanya ditujukan untuk dijalankan secara lokal.

## Dashboard

Dashboard interaktif dapat diakses di [Streamlit Community Cloud](https://e74msuh4aypedeau9bxoac.streamlit.app/).

## Menjalankan dashboard

Gunakan Python 3.11 atau lebih baru.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r submission_original\requirements.txt
python -m streamlit run submission_original\dashboard.py
```

## Berkas utama

- `analysis.py`: pemuatan, assessment, cleaning, EDA, dan RFM.
- `dashboard.py`: dashboard Streamlit lokal.
- `notebook.ipynb`: dokumentasi analisis yang dapat dijalankan sel demi sel.

Sebelum mengumpulkan, ganti tiga placeholder identitas di atas dengan data milik Anda sendiri dan jalankan notebook dari awal.
