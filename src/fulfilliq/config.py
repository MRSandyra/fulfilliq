from __future__ import annotations

from pathlib import Path

SCHEMA_VERSION = 1
EVENT_TYPES = {"order_placed", "delivery_outcome"}
SOURCE_FILES = {
    "orders": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "translations": "product_category_name_translation.csv",
}
DEFAULT_MAX_RECORDS = 100
DEFAULT_MAX_BYTES = 256 * 1024
MAX_BATCH_BYTES = 1024 * 1024
MAX_RECORDS_PER_BATCH = 10_000


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
