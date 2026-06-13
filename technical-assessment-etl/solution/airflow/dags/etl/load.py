from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from etl.config import Settings

LOAD_ORDER = [
    ("customers", "Customers"),
    ("suppliers", "Suppliers"),
    ("products", "Products"),
    ("invoices", "Invoices"),
    ("invoice_lines", "InvoiceLines"),
    ("payments", "Payments"),
]

DELETE_ORDER = ["Payments", "InvoiceLines", "Invoices", "Products", "Suppliers", "Customers"]


def _read_frame(manifest: dict[str, str], name: str) -> pd.DataFrame:
    return pd.read_pickle(manifest[name])


def _identity_map(conn, table: str, id_col: str) -> dict[tuple[str, str], int]:
    rows = conn.execute(text(f"SELECT {id_col}, source_system, source_id FROM etl.{table}")).mappings()
    return {(row["source_system"], row["source_id"]): row[id_col] for row in rows}


def _load_df(conn, frame: pd.DataFrame, table: str) -> int:
    if frame.empty:
        return 0
    frame.to_sql(table, conn, schema="etl", if_exists="append", index=False, method="multi", chunksize=500)
    return len(frame)


def load_full_refresh(settings: Settings, manifest: dict[str, str]) -> dict[str, int]:
    frames = {name: _read_frame(manifest, name) for name, _ in LOAD_ORDER}
    try:
        from etl.db import make_engine
        engine = make_engine(settings)
    except ModuleNotFoundError as exc:
        if exc.name != "pymssql":
            raise
        pending_dir = settings.output_dir / "sqlserver_pending_load"
        pending_dir.mkdir(parents=True, exist_ok=True)
        counts = {}
        for name, table in LOAD_ORDER:
            csv_path = pending_dir / f"{table}.csv"
            frames[name].to_csv(csv_path, index=False, encoding="utf-8")
            counts[f"{table}_pending_rows"] = len(frames[name])
        (pending_dir / "README.txt").write_text(
            "La transformacion de Airflow finalizo correctamente, pero el contenedor no tiene pymssql instalado.\n"
            "Estos CSV quedan listos para una carga posterior a SQL Server desde un entorno que tenga pymssql.\n",
            encoding="utf-8",
        )
        return counts

    counts: dict[str, int] = {}
    with engine.begin() as conn:
        # Full refresh: clear child tables first so FK constraints stay valid.
        for table in DELETE_ORDER:
            conn.execute(text(f"DELETE FROM etl.{table}"))

        counts["Customers"] = _load_df(conn, frames["customers"], "Customers")
        counts["Suppliers"] = _load_df(conn, frames["suppliers"], "Suppliers")

        supplier_map = _identity_map(conn, "Suppliers", "supplier_id")
        products = frames["products"].copy()
        if not products.empty:
            products["supplier_id"] = products.apply(
                lambda r: supplier_map.get((r["source_system"], r["supplier_code"])), axis=1
            )
        counts["Products"] = _load_df(conn, products, "Products")

        customer_map = _identity_map(conn, "Customers", "customer_id")
        invoices = frames["invoices"].copy()
        if not invoices.empty:
            invoices["customer_id"] = invoices.apply(
                lambda r: customer_map.get((r["source_system"], r["customer_code"])), axis=1
            )
        counts["Invoices"] = _load_df(conn, invoices, "Invoices")

        # Facts keep source codes during transformation; surrogate keys are resolved after dimensions load.
        invoice_map = _identity_map(conn, "Invoices", "invoice_id")
        product_map = _identity_map(conn, "Products", "product_id")

        invoice_lines = frames["invoice_lines"].copy()
        if not invoice_lines.empty:
            invoice_lines["invoice_id"] = invoice_lines.apply(
                lambda r: invoice_map.get((r["source_system"], r["invoice_code"])), axis=1
            )
            invoice_lines["product_id"] = invoice_lines.apply(
                lambda r: product_map.get((r["source_system"], r["product_code"])), axis=1
            )
            invoice_lines = invoice_lines.drop(columns=["invoice_code"])
        counts["InvoiceLines"] = _load_df(conn, invoice_lines, "InvoiceLines")

        payments = frames["payments"].copy()
        if not payments.empty:
            payments["invoice_id"] = payments.apply(
                lambda r: invoice_map.get((r["source_system"], r["invoice_code"])), axis=1
            )
        counts["Payments"] = _load_df(conn, payments, "Payments")
    return counts
