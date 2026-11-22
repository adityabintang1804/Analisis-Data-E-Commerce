"""Dashboard lokal untuk proyek analisis e-commerce yang mandiri."""
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from submission_original.analysis import (  # noqa: E402
    MIN_STATE_ORDERS,
    SEGMENT_ORDER,
    prepare_analysis,
)


@st.cache_data(show_spinner="Memuat dan menghitung data…")
def get_data():
    return prepare_analysis()


def make_bar(frame, x, y, title, color="#2F6690", horizontal=False):
    plot = frame.copy()
    fig, ax = plt.subplots(figsize=(9, 4.8))
    if horizontal:
        ax.barh(plot[y], plot[x], color=color)
        ax.set_xlabel(x.replace("_", " ").title())
    else:
        ax.bar(plot[x], plot[y], color=color)
        ax.set_ylabel(y.replace("_", " ").title())
        ax.tick_params(axis="x", rotation=35)
    ax.set_title(title, loc="left", fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def main():
    st.set_page_config(page_title="E-Commerce Insight", page_icon="📦", layout="wide")
    st.title("E-Commerce Insight: Pengiriman dan Retensi Pelanggan")
    st.caption("Dataset Olist • Periode pembelian 1 Januari 2017–31 Agustus 2018 • Mata uang BRL")
    data = get_data()

    delivery_tab, rfm_tab, quality_tab = st.tabs(
        ["Pengiriman & Ulasan", "Segmentasi RFM", "Kualitas Data"]
    )
    with delivery_tab:
        state = data["delivery"].copy()
        review = data["review"].copy()
        priority = state.loc[state["eligible_for_priority"]].head(10)
        late_overall = data["orders"].loc[
            data["orders"]["is_in_period"]
            & data["orders"]["is_delivered"]
            & data["orders"]["delivery_is_known"], "is_late"
        ].mean() * 100
        on_time_review = review.loc[review["delivery_status"].eq("Tepat waktu"), "average_review"].iloc[0]
        late_review = review.loc[review["delivery_status"].eq("Terlambat"), "average_review"].iloc[0]
        a, b, c = st.columns(3)
        a.metric("Keterlambatan keseluruhan", f"{late_overall:.2f}%")
        b.metric("Skor tepat waktu", f"{on_time_review:.2f}/5")
        c.metric("Skor terlambat", f"{late_review:.2f}/5", f"{late_review - on_time_review:.2f} poin")
        st.subheader("Wilayah prioritas untuk evaluasi logistik")
        st.caption(f"Peringkat hanya memakai state dengan minimal {MIN_STATE_ORDERS} pesanan berstatus delivered dan tanggal pengiriman lengkap.")
        st.pyplot(make_bar(priority.sort_values("late_rate_pct"), "late_rate_pct", "customer_state", "Tingkat keterlambatan per state (%)", horizontal=True), width="stretch")
        st.subheader("Hubungan ketepatan pengiriman dan ulasan")
        st.pyplot(make_bar(review, "delivery_status", "bad_review_rate_pct", "Proporsi ulasan buruk (skor 1–2)"), width="stretch")
        st.dataframe(priority[["customer_state", "total_orders", "late_rate_pct", "average_review", "bad_review_rate_pct"]], hide_index=True, width="stretch")
        st.info("Temuan ini menunjukkan hubungan pada data historis; tidak membuktikan bahwa keterlambatan adalah satu-satunya penyebab ulasan buruk.")

    with rfm_tab:
        rfm = data["rfm"]
        summary = data["rfm_summary"]
        selected = st.multiselect("Pilih segmen", SEGMENT_ORDER, default=SEGMENT_ORDER)
        shown = summary.loc[summary["segment"].isin(selected)]
        a, b, c = st.columns(3)
        a.metric("Pelanggan tersegmentasi", f"{len(rfm):,}")
        b.metric("Pelanggan berulang", f"{(rfm['frequency'].ge(2).mean() * 100):.2f}%")
        c.metric("Nilai barang", f"BRL {rfm['monetary'].sum():,.2f}")
        st.subheader("Komposisi pelanggan menurut segmentasi manual")
        st.pyplot(make_bar(shown, "segment", "customers", "Jumlah pelanggan per segmen", "#5B8E7D"), width="stretch")
        st.subheader("Nilai barang yang dikontribusikan tiap segmen")
        st.pyplot(make_bar(shown, "segment", "monetary", "Kontribusi nilai barang per segmen", "#C96C50"), width="stretch")
        st.dataframe(shown, hide_index=True, width="stretch")
        st.caption("Recency dihitung terhadap 1 September 2018; frequency adalah jumlah order unik; monetary adalah total harga item tanpa ongkir. Segmen bersifat aturan bisnis manual, bukan prediksi churn.")

    with quality_tab:
        st.subheader("Ringkasan assessment sebelum cleaning")
        st.dataframe(data["quality"], hide_index=True, width="stretch")
        st.markdown("""
        - Nilai tanggal pengiriman yang kosong tidak diimputasi; order tersebut dikeluarkan hanya dari metrik keterlambatan.
        - Review yang berulang per order dipilih satu, yaitu review dengan tanggal pembuatan paling akhir, sehingga tidak menggandakan pesanan.
        - Harga item yang tidak dapat diparsing tidak dijumlahkan ke monetary RFM.
        """)


if __name__ == "__main__":
    main()
