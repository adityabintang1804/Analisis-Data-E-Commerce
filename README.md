# E-Commerce Delivery & Customer Insight

Proyek ini menganalisis data transaksi Olist untuk memahami dua hal yang sering menjadi penentu pengalaman belanja: ketepatan pengiriman dan perilaku pelanggan setelah bertransaksi. Hasilnya disajikan dalam notebook analisis serta dashboard interaktif.

**Nama:** `ISI NAMA ANDA`  
**Email:** `ISI EMAIL ANDA`  
**ID Dicoding:** `ISI ID DICODING ANDA`

## Dashboard

Lihat dashboard interaktif di [Streamlit Community Cloud](https://e74msuh4aypedeau9bxoac.streamlit.app/).

## Fokus Analisis

Analisis menggunakan data pembelian dari 1 Januari 2017 sampai 31 Agustus 2018 dan menjawab dua pertanyaan utama.

1. State mana yang perlu menjadi perhatian dalam evaluasi logistik berdasarkan tingkat keterlambatan, dan bagaimana ulasan pelanggan berbeda antara pengiriman tepat waktu dan terlambat?
2. Bagaimana pelanggan dapat dikelompokkan menggunakan Recency, Frequency, dan Monetary (RFM) agar strategi retensi lebih tepat sasaran?

Segmentasi RFM dibuat dengan aturan bisnis manual, sehingga hasilnya mudah dijelaskan dan tidak memakai machine learning. Nilai monetary merepresentasikan total harga item dalam BRL, tanpa ongkos kirim.

## Isi Proyek

```text
.
├── analysis.py              # Pemuatan data, cleaning, EDA, dan RFM
├── notebook.ipynb           # Dokumentasi proses analisis lengkap
├── dashboard/
│   └── dashboard.py         # Aplikasi Streamlit
├── data/                    # Dataset Olist yang diperlukan aplikasi
└── requirements.txt         # Library Python
```

## Menjalankan Secara Lokal

Pastikan Python 3.11 atau versi lebih baru sudah tersedia, lalu jalankan perintah berikut dari root proyek.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run dashboard\dashboard.py
```

Dashboard akan terbuka pada alamat lokal yang ditampilkan oleh Streamlit. Tekan `Ctrl + C` di terminal untuk menghentikan server.

## Catatan Analisis

- Pesanan dengan tanggal pengiriman yang tidak lengkap tidak dipaksa menjadi tepat waktu atau terlambat.
- Satu review terbaru digunakan untuk setiap order agar jumlah pesanan tidak terduplikasi saat analisis.
- Temuan mengenai keterlambatan dan review menunjukkan pola historis, bukan bukti hubungan sebab-akibat.
- Recency dihitung dengan tanggal acuan 1 September 2018.

Sebelum submission, isi identitas pada bagian awal README dan notebook dengan data milik sendiri.
