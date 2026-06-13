from __future__ import annotations

import pandas as pd

from etl.config import Settings
from etl.extract import read_csv
from etl.quality import QualityReport
from etl.transform_common import (
    _bool,
    _clean_text,
    _decimal,
    _exclude_missing_id,
    _optional_text,
    _required_text,
)


def products(settings: Settings, report: QualityReport) -> pd.DataFrame:
    rows = []
    df = _exclude_missing_id(read_csv(settings, "source_c/products_catalog.csv", "SOURCE_C"), "product_code", "Products", "SOURCE_C", report)
    for _, r in df.iterrows():
        sid = _clean_text(r["product_code"])
        rows.append({
            "product_code": sid, "product_name": _required_text(r["name"], "Products", "product_name", "SOURCE_C", sid, report),
            "category": _optional_text(r["category"], "Products", "category", "SOURCE_C", sid, report),
            "unit_price": _decimal(r["price"], "SOURCE_C", "Products", "unit_price", sid, report),
            "supplier_id": None, "supplier_code": _optional_text(r["supplier_code"], "Products", "supplier_code", "SOURCE_C", sid, report),
            "sku": None,
            "description": _optional_text(r["description"], "Products", "description", "SOURCE_C", sid, report),
            "uom": _optional_text(r["uom"], "Products", "uom", "SOURCE_C", sid, report),
            "is_active": _bool(r["active"]), "created_date": None,
            "source_system": "SOURCE_C", "source_id": sid})
    return pd.DataFrame(rows)
