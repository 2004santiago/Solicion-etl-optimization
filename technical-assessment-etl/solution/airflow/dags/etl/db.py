from __future__ import annotations

import importlib.util
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from etl.config import Settings


def make_engine(settings: Settings) -> Engine:
    host = settings.sqlserver_host
    if host == "sqlserver":
        # Airflow and SQL Server run in different Compose projects in this setup.
        host = "host.docker.internal"

    if importlib.util.find_spec("pymssql") is not None:
        password = quote_plus(settings.sqlserver_password)
        url = f"mssql+pymssql://{settings.sqlserver_user}:{password}@{host}:{settings.sqlserver_port}/{settings.sqlserver_db}"
    else:
        # The official Airflow image used here already includes pyodbc and ODBC Driver 18.
        odbc = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={host},{settings.sqlserver_port};"
            f"DATABASE={settings.sqlserver_db};"
            f"UID={settings.sqlserver_user};"
            f"PWD={settings.sqlserver_password};"
            "TrustServerCertificate=yes;"
        )
        url = f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc)}"
    return create_engine(url, pool_pre_ping=True, future=True)
