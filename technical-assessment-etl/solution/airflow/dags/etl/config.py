from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    output_dir: Path
    sqlserver_host: str
    sqlserver_port: int
    sqlserver_db: str
    sqlserver_user: str
    sqlserver_password: str

    @classmethod
    def from_env(cls) -> "Settings":
        airflow_home = Path(os.getenv("AIRFLOW_HOME", "/opt/airflow"))
        candidate_data_dirs = [
            airflow_home / "data",
            airflow_home / "data_raw",
            airflow_home / "dags" / "data",
        ]
        default_data_dir = next((path for path in candidate_data_dirs if (path / "source_a").exists()), candidate_data_dirs[0])
        return cls(
            data_dir=Path(os.getenv("ETL_DATA_DIR", default_data_dir)),
            output_dir=Path(os.getenv("ETL_OUTPUT_DIR", airflow_home / "output")),
            sqlserver_host=os.getenv("SQLSERVER_HOST", "sqlserver"),
            sqlserver_port=int(os.getenv("SQLSERVER_PORT", "1433")),
            sqlserver_db=os.getenv("SQLSERVER_DB", "ETL_DATA"),
            sqlserver_user=os.getenv("SQLSERVER_USER", "sa"),
            sqlserver_password=os.getenv("SQLSERVER_PASSWORD", "P@ssw0rd2025!"),
        )

    @property
    def transformed_dir(self) -> Path:
        return self.output_dir / "transformed"
