from __future__ import annotations

import sys
from pathlib import Path

import pendulum

try:
    from airflow.sdk import dag, task
except ImportError:
    from airflow.decorators import dag, task

AIRFLOW_HOME = Path("/opt/airflow")
for import_path in (AIRFLOW_HOME / "dags", AIRFLOW_HOME):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from etl.config import Settings
from etl.extract import validate_source_files
from etl.load import load_full_refresh
from etl.transform import build_transformed_dataset

SOURCE_FILES = {
    "SOURCE_A": [
        "source_a/customers.csv",
        "source_a/suppliers.csv",
        "source_a/products.csv",
        "source_a/invoices.csv",
        "source_a/invoice_lines.csv",
        "source_a/payments.csv",
    ],
    "SOURCE_B": [
        "source_b/clientes.csv",
        "source_b/proveedores.csv",
        "source_b/productos.csv",
        "source_b/facturas.csv",
        "source_b/factura_lineas.csv",
        "source_b/pagos.csv",
    ],
    "SOURCE_C": [
        "source_c/products_catalog.csv",
    ],
}


@dag(
    dag_id="etl_csv_to_sqlserver",
    description="Carga full refresh desde CSV heterogeneos hacia SQL Server ETL_DATA.etl.",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    tags=["etl", "csv", "sqlserver"],
)
def etl_csv_to_sqlserver():
    def _validate_source(source_name: str) -> list[str]:
        settings = Settings.from_env()
        validate_source_files(settings)
        return [str(settings.data_dir / file_name) for file_name in SOURCE_FILES[source_name]]

    @task(task_id="limpieza_SOURCE_A")
    def limpieza_source_a() -> list[str]:
        return _validate_source("SOURCE_A")

    @task(task_id="limpieza_SOURCE_B")
    def limpieza_source_b() -> list[str]:
        return _validate_source("SOURCE_B")

    @task(task_id="limpieza_SOURCE_C")
    def limpieza_source_c() -> list[str]:
        return _validate_source("SOURCE_C")

    @task(task_id="unir_y_organizar")
    def unir_y_organizar(_: list[str], __: list[str], ___: list[str]) -> dict[str, str]:
        return build_transformed_dataset(Settings.from_env())

    @task
    def load_to_sqlserver(manifest: dict[str, str]) -> dict[str, int]:
        return load_full_refresh(Settings.from_env(), manifest)

    source_a_files = limpieza_source_a()
    source_b_files = limpieza_source_b()
    source_c_files = limpieza_source_c()
    manifest = unir_y_organizar(source_a_files, source_b_files, source_c_files)
    load_to_sqlserver(manifest)


etl_csv_to_sqlserver()
