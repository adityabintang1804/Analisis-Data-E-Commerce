"""Analisis mandiri dataset Olist untuk submission proyek akhir.

Modul ini sengaja memusatkan aturan bisnis agar notebook dan dashboard
menampilkan angka yang sama. Analisis bersifat deskriptif, bukan prediksi.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
ANALYSIS_START = pd.Timestamp("2017-01-01")
ANALYSIS_END = pd.Timestamp("2018-09-01")  # batas akhir eksklusif
REFERENCE_DATE = pd.Timestamp("2018-09-01")
MIN_STATE_ORDERS = 100

SEGMENT_ORDER = [
    "Champions",
    "Pelanggan baru",
    "Pelanggan potensial",
    "Perlu perhatian",
    "Tidak aktif",
]


def _read_csv(filename: str) -> pd.DataFrame:
    """Membaca satu CSV sumber dengan lokasi yang konsisten."""
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Dataset tidak ditemukan: {path}")
    return pd.read_csv(path)


def load_raw_data() -> dict[str, pd.DataFrame]:
    """Memuat hanya tabel yang diperlukan oleh dua pertanyaan bisnis."""
    return {
        "orders": _read_csv("orders_dataset.csv"),
        "customers": _read_csv("customers_dataset.csv"),
        "items": _read_csv("order_items_dataset.csv"),
        "reviews": _read_csv("order_reviews_dataset.csv"),
    }


def assess_data(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Ringkas masalah kualitas data yang diperiksa sebelum cleaning."""
    records = []
    for name, frame in raw.items():
        records.append(
            {
                "tabel": name,
                "baris": len(frame),
                "duplikat_persis": int(frame.duplicated().sum()),
                "nilai_kosong": int(frame.isna().sum().sum()),
            }
        )
    return pd.DataFrame(records)


def _prepare_latest_reviews(reviews: pd.DataFrame) -> pd.DataFrame:
    """Satu skor review terbaru per order, agar grain tetap satu order."""
    clean = reviews.drop_duplicates().copy()
    clean["review_creation_date"] = pd.to_datetime(
        clean["review_creation_date"], errors="coerce"
    )
    clean["review_score"] = pd.to_numeric(clean["review_score"], errors="coerce")
    clean = clean.sort_values(["order_id", "review_creation_date", "review_id"])
    latest = clean.drop_duplicates("order_id", keep="last")
    return latest[["order_id", "review_score"]]


def clean_and_merge(raw: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Membersihkan data lalu membentuk tabel level-order dan level-item.

    Order canceled/tidak delivered tidak dipakai untuk analisis pengalaman
    pengiriman atau RFM. Nilai tanggal yang tidak dapat diparsing tidak diisi
    dengan tebakan; baris tersebut hanya tidak masuk metrik terkait.
    """
    orders = raw["orders"].copy()
    customers = raw["customers"].copy()
    items = raw["items"].copy()

    for column in [
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]:
        orders[column] = pd.to_datetime(orders[column], errors="coerce")

    orders = orders.merge(
        customers[["customer_id", "customer_unique_id", "customer_state"]],
        on="customer_id",
        how="left",
        validate="one_to_one",
    )
    orders = orders.merge(
        _prepare_latest_reviews(raw["reviews"]),
        on="order_id",
        how="left",
        validate="one_to_one",
    )
    orders["review_score"] = pd.to_numeric(orders["review_score"], errors="coerce")
    orders["is_in_period"] = orders["order_purchase_timestamp"].between(
        ANALYSIS_START, ANALYSIS_END, inclusive="left"
    )
    orders["is_delivered"] = orders["order_status"].eq("delivered")
    orders["delivery_is_known"] = (
        orders["order_delivered_customer_date"].notna()
        & orders["order_estimated_delivery_date"].notna()
    )
    orders["is_late"] = pd.Series(pd.NA, index=orders.index, dtype="boolean")
    known = orders["delivery_is_known"]
    orders.loc[known, "is_late"] = (
        orders.loc[known, "order_delivered_customer_date"].dt.normalize()
        > orders.loc[known, "order_estimated_delivery_date"].dt.normalize()
    )
    orders["is_bad_review"] = orders["review_score"].isin([1, 2])

    items["price"] = pd.to_numeric(items["price"], errors="coerce")
    item_level = items.merge(
        orders[["order_id", "is_in_period", "is_delivered"]],
        on="order_id",
        how="left",
        validate="many_to_one",
    )
    order_value = (
        item_level.loc[item_level["price"].notna()]
        .groupby("order_id", as_index=False)["price"]
        .sum()
        .rename(columns={"price": "item_value_brl"})
    )
    orders = orders.merge(order_value, on="order_id", how="left", validate="one_to_one")
    return orders, item_level


def delivery_by_state(orders: pd.DataFrame) -> pd.DataFrame:
    """Hitung ketepatan pengiriman dan kepuasan per state pelanggan."""
    eligible = orders.loc[
        orders["is_in_period"] & orders["is_delivered"] & orders["delivery_is_known"]
    ].copy()
    eligible = eligible.loc[eligible["customer_state"].notna()].copy()
    summary = (
        eligible.groupby("customer_state", as_index=False)
        .agg(
            total_orders=("order_id", "nunique"),
            late_orders=("is_late", "sum"),
            average_review=("review_score", "mean"),
            reviewed_orders=("review_score", "count"),
            bad_reviews=("is_bad_review", "sum"),
        )
    )
    summary["late_rate_pct"] = 100 * summary["late_orders"] / summary["total_orders"]
    summary["bad_review_rate_pct"] = 100 * summary["bad_reviews"] / summary["reviewed_orders"]
    summary.loc[summary["reviewed_orders"].eq(0), "bad_review_rate_pct"] = pd.NA
    summary["eligible_for_priority"] = summary["total_orders"].ge(MIN_STATE_ORDERS)
    return summary.sort_values(["late_rate_pct", "total_orders"], ascending=[False, False])


def review_by_delivery_status(orders: pd.DataFrame) -> pd.DataFrame:
    """Bandingkan skor dan ulasan buruk untuk pengiriman tepat waktu/terlambat."""
    eligible = orders.loc[
        orders["is_in_period"]
        & orders["is_delivered"]
        & orders["delivery_is_known"]
        & orders["review_score"].between(1, 5)
    ].copy()
    eligible["delivery_status"] = eligible["is_late"].map(
        {True: "Terlambat", False: "Tepat waktu"}
    )
    result = (
        eligible.groupby("delivery_status", as_index=False)
        .agg(
            orders=("order_id", "nunique"),
            average_review=("review_score", "mean"),
            bad_reviews=("is_bad_review", "sum"),
        )
    )
    result["bad_review_rate_pct"] = 100 * result["bad_reviews"] / result["orders"]
    return result.set_index("delivery_status").reindex(["Tepat waktu", "Terlambat"]).reset_index()


def build_rfm(orders: pd.DataFrame) -> pd.DataFrame:
    """Membuat RFM dengan pengelompokan manual yang dapat dijelaskan."""
    eligible = orders.loc[
        orders["is_in_period"]
        & orders["is_delivered"]
        & orders["customer_unique_id"].notna()
        & orders["item_value_brl"].notna()
    ].copy()
    rfm = (
        eligible.groupby("customer_unique_id", as_index=False)
        .agg(
            last_purchase=("order_purchase_timestamp", "max"),
            frequency=("order_id", "nunique"),
            monetary=("item_value_brl", "sum"),
        )
    )
    rfm["recency_days"] = (REFERENCE_DATE - rfm["last_purchase"].dt.normalize()).dt.days
    rfm["segment"] = "Tidak aktif"
    rfm.loc[(rfm["recency_days"] <= 30) & (rfm["frequency"] >= 2), "segment"] = "Champions"
    rfm.loc[(rfm["recency_days"] <= 30) & (rfm["frequency"] == 1), "segment"] = "Pelanggan baru"
    rfm.loc[
        rfm["recency_days"].between(31, 90) & (rfm["frequency"] >= 2), "segment"
    ] = "Pelanggan potensial"
    rfm.loc[
        rfm["recency_days"].between(31, 90) & (rfm["frequency"] == 1), "segment"
    ] = "Perlu perhatian"
    rfm["segment"] = pd.Categorical(rfm["segment"], categories=SEGMENT_ORDER, ordered=True)
    return rfm


def rfm_summary(rfm: pd.DataFrame) -> pd.DataFrame:
    """Ringkasan segmen untuk pengambilan keputusan retensi."""
    summary = (
        rfm.groupby("segment", observed=False, as_index=False)
        .agg(
            customers=("customer_unique_id", "nunique"),
            median_recency_days=("recency_days", "median"),
            median_frequency=("frequency", "median"),
            monetary=("monetary", "sum"),
        )
    )
    summary["customer_share_pct"] = 100 * summary["customers"] / summary["customers"].sum()
    return summary


def prepare_analysis() -> dict[str, pd.DataFrame]:
    """Satu pintu untuk notebook dan dashboard."""
    raw = load_raw_data()
    orders, items = clean_and_merge(raw)
    delivery = delivery_by_state(orders)
    review = review_by_delivery_status(orders)
    rfm = build_rfm(orders)
    return {
        "quality": assess_data(raw),
        "orders": orders,
        "items": items,
        "delivery": delivery,
        "review": review,
        "rfm": rfm,
        "rfm_summary": rfm_summary(rfm),
    }
