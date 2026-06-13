from __future__ import annotations

from pathlib import Path

import pandas as pd

from etl.config import Settings


REQUIRED_FILES = [
    "source_a/customers.csv",
    "source_a/suppliers.csv",
    "source_a/products.csv",
    "source_a/invoices.csv",
    "source_a/invoice_lines.csv",
    "source_a/payments.csv",
    "source_b/clientes.csv",
    "source_b/proveedores.csv",
    "source_b/productos.csv",
    "source_b/facturas.csv",
    "source_b/factura_lineas.csv",
    "source_b/pagos.csv",
    "source_c/products_catalog.csv",
]


def validate_source_files(settings: Settings) -> list[str]:
    missing = [name for name in REQUIRED_FILES if not (settings.data_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing source files: {', '.join(missing)}")
    return [str(settings.data_dir / name) for name in REQUIRED_FILES]


def read_csv(settings: Settings, relative_path: str, source_system: str) -> pd.DataFrame:
    encoding = "latin-1" if source_system == "SOURCE_B" else "utf-8"
    return pd.read_csv(settings.data_dir / relative_path, dtype=str, encoding=encoding, keep_default_na=False)
