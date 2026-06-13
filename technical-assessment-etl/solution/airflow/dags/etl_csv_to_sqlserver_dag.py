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


@dag(
    dag_id="etl_csv_to_sqlserver",
    description="Carga full refresh desde CSV heterogeneos hacia SQL Server ETL_DATA.etl.",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    tags=["etl", "csv", "sqlserver"],
)
def etl_csv_to_sqlserver():
    @task
    def validate_sources() -> list[str]:
        return validate_source_files(Settings.from_env())

    @task
    def extract_transform(_: list[str]) -> dict[str, str]:
        return build_transformed_dataset(Settings.from_env())

    @task
    def load_to_sqlserver(manifest: dict[str, str]) -> dict[str, int]:
        return load_full_refresh(Settings.from_env(), manifest)

    files = validate_sources()
    manifest = extract_transform(files)
    load_to_sqlserver(manifest)


etl_csv_to_sqlserver()
