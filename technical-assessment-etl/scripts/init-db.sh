#!/bin/bash
set -e

if [ -z "$SA_PASSWORD" ]; then
  echo "ERROR: SA_PASSWORD environment variable is required"
  exit 1
fi

DB_NAME="${MSSQL_DB_NAME:-ETL_DATA}"

/opt/mssql/bin/sqlservr &
SQL_PID=$!

RETRIES=30
for i in $(seq 1 $RETRIES); do
  /opt/mssql-tools18/bin/sqlcmd \
    -S localhost -U sa -P "$SA_PASSWORD" -C \
    -Q "SELECT 1" > /dev/null 2>&1 && break
  echo "Waiting for SQL Server... ($i/$RETRIES)"
  sleep 2
done

echo "Ensuring database [$DB_NAME] exists..."
/opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$SA_PASSWORD" -C \
  -Q "IF DB_ID('$DB_NAME') IS NULL CREATE DATABASE [$DB_NAME]"

SCHEMA_COUNT=$(/opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$SA_PASSWORD" -C \
  -d "$DB_NAME" \
  -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'etl'" \
  -h -1 2>/dev/null | tr -d ' ')

if [ "$SCHEMA_COUNT" = "0" ] || [ -z "$SCHEMA_COUNT" ]; then
  echo "Initializing schema in [$DB_NAME] from /schemas/target_schema.sql..."
  /opt/mssql-tools18/bin/sqlcmd \
    -S localhost -U sa -P "$SA_PASSWORD" -C \
    -d "$DB_NAME" \
    -i /schemas/target_schema.sql
  echo "Schema created successfully."
else
  echo "Schema already exists ($SCHEMA_COUNT tables in [$DB_NAME].[etl]), skipping initialization."
fi

wait $SQL_PID
