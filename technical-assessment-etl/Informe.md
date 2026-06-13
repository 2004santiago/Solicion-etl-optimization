# Prueba Tecnica - Data Engineer Senior

## Objetivo

Construir un pipeline ETL que extrae datos CSV heterogeneos de tres sistemas fuente, los transforma y unifica, aplica reglas de calidad de datos y carga el resultado en SQL Server.

La solucion implementada usa:

- **Apache Airflow** para orquestar el pipeline.
- **Python + pandas** para extraccion, transformacion y validaciones.
- **SQL Server 2022 Developer** como base destino.
- **Docker Compose** para ejecutar toda la aplicacion con un solo comando.

## Ejecucion con Docker

### Requisitos

- Docker Desktop o Docker Engine.
- Docker Compose v2.
- Puertos disponibles:
  - `1433` para SQL Server.
  - `8090` para Airflow.

### Levantar la solucion completa

Desde la raiz del repositorio:

```bash
docker compose up --build
```

Esto levanta:

- `sqlserver`: SQL Server con la base `ETL_DATA` y el esquema `etl`.
- `airflow-postgres`: base de metadatos de Airflow.
- `airflow-init`: migracion inicial y creacion del usuario de Airflow.
- `airflow-apiserver`: UI/API de Airflow.
- `airflow-scheduler` y `airflow-dag-processor`: servicios de planificacion y lectura de DAGs.

### Acceso a Airflow

- URL: <http://localhost:8090>
- Usuario: `airflow`
- Password: `airflow`

El DAG principal es:

```text
etl_csv_to_sqlserver
```

La ejecucion es manual. En Airflow, activar el DAG y usar **Trigger DAG**.

### Conexion a SQL Server desde el host

```text
Server: localhost,1433
User: sa
Password: P@ssw0rd2025!
Database: ETL_DATA
```

Variables opcionales:

| Variable | Descripcion | Default |
| --- | --- | --- |
| `SA_PASSWORD` | Password del usuario `sa` | `P@ssw0rd2025!` |
| `MSSQL_DB_NAME` | Nombre de la base destino | `ETL_DATA` |
| `_AIRFLOW_WWW_USER_USERNAME` | Usuario inicial de Airflow | `airflow` |
| `_AIRFLOW_WWW_USER_PASSWORD` | Password inicial de Airflow | `airflow` |

Ejemplo:

```bash
SA_PASSWORD=MiPassword123! MSSQL_DB_NAME=etl_produccion docker compose up --build
```

### Reiniciar desde cero

```bash
docker compose down -v
docker compose up --build
```

El parametro `-v` elimina los volumenes de SQL Server y Airflow, por lo que la base se inicializa nuevamente.

## Estructura de la solucion

```text
solution/
  airflow/
    Dockerfile
    requirements.txt
    dags/
      etl_csv_to_sqlserver_dag.py
      data/
        source_a/
        source_b/
        source_c/
      etl/
        config.py
        extract.py
        transform.py
        load.py
        quality.py
    output/
      quality_report.csv
      quality_report.json
      transformed/
  notebook/
    01_notebook.ipynb
sql/
  target_schema.sql
scripts/
  init-db.sh
docker-compose.yml
```

## Pipeline ETL

El DAG principal es `etl_csv_to_sqlserver`. Para que la orquestacion sea mas clara en Airflow, el flujo se divide visualmente por fuente y luego consolida la informacion antes de cargarla en SQL Server:

```text
limpieza_SOURCE_A \
limpieza_SOURCE_B  -> unir_y_organizar -> load_to_sqlserver
limpieza_SOURCE_C /
```

### Tareas del DAG

| Tarea | Proposito |
| --- | --- |
| `limpieza_SOURCE_A` | Agrupa la validacion y preparacion de los CSV de `source_a`: clientes, proveedores, productos, facturas, lineas de factura y pagos. |
| `limpieza_SOURCE_B` | Agrupa la validacion y preparacion de los CSV de `source_b`, incluyendo lectura Latin-1, columnas en espanol y formatos numericos/fechas propios del sistema legado. |
| `limpieza_SOURCE_C` | Agrupa la validacion y preparacion del catalogo `source_c/products_catalog.csv`, incluyendo limpieza de precios con simbolo `$`. |
| `unir_y_organizar` | Ejecuta la transformacion consolidada: normaliza estructuras, aplica reglas de calidad, resuelve dependencias logicas y genera los datasets intermedios. |
| `load_to_sqlserver` | Carga los datasets transformados en SQL Server con estrategia full refresh y respetando integridad referencial. |

Esta division busca que el grafo de Airflow muestre mejor la responsabilidad de cada fuente. La logica de transformacion se mantiene centralizada en el codigo Python del ETL para evitar duplicar reglas de negocio.

Orden de carga en SQL Server:

```text
Customers -> Suppliers -> Products -> Invoices -> InvoiceLines -> Payments
```

Las tablas destino se crean desde `sql/target_schema.sql` en el esquema `etl`.

### Salidas intermedias

La tarea `unir_y_organizar` genera archivos intermedios en:

```text
solution/airflow/output/transformed/
```

Estos archivos son usados por `load_to_sqlserver` para cargar las tablas destino.

## Informe de Calidad de Datos

El EDA inicial esta documentado en:

```text
solution/notebook/01_notebook.ipynb
```

La seccion **Resumen Consolidado de Calidad de Datos** del notebook es la base de las reglas implementadas en el pipeline. Durante cada ejecucion, el ETL genera:

- `solution/airflow/output/quality_report.csv`: detalle por evento de calidad.
- `solution/airflow/output/quality_report.json`: resumen por accion, tabla, decisiones y eventos.

### Hallazgos identificados en el EDA

| Fuente | Hallazgo | Tratamiento |
| --- | --- | --- |
| `SOURCE_A` | Emails nulos en clientes | Default `no_disponible@placeholder.com` |
| `SOURCE_A` | Espacios adicionales en textos | Normalizacion con trim y espacios simples |
| `SOURCE_A` | Datos faltantes en proveedores, como email o contacto | Defaults o `NULL` segun obligatoriedad |
| `SOURCE_A` | Factura con cliente inexistente `C099` | Exclusion por FK huerfana |
| `SOURCE_A` | Pagos que exceden facturas `I008` e `I019` | Exclusion de pagos conflictivos |
| `SOURCE_A` | Multiples pagos por factura | Se aceptan si el acumulado no excede el total |
| `SOURCE_A` | Posibles pagos duplicados por llave de negocio | Deduplicacion solo ante coincidencia exacta |
| `SOURCE_B` | Correos faltantes en clientes y proveedores | Default `no_disponible@placeholder.com` |
| `SOURCE_B` | Espacios adicionales en nombres y razon social | Normalizacion con trim y espacios simples |
| `SOURCE_B` | Decimales con coma y separador de miles | Conversion a `Decimal` estandar |
| `SOURCE_B` | Producto con proveedor nulo | Se conserva con `supplier_id NULL` y se reporta |
| `SOURCE_B` | Factura con cliente inexistente `B099` | Exclusion por FK huerfana |
| `SOURCE_B` | Pagos que exceden factura `B008` | Exclusion de pagos conflictivos |
| `SOURCE_B` | Banco nulo en pagos de efectivo | Se acepta como valor esperado de negocio |
| `SOURCE_C` | Precios con simbolo `$` | Limpieza de moneda y conversion a decimal |
| `SOURCE_C` | Proveedor nulo en catalogo | Se conserva con `supplier_id NULL` y se reporta |
| `SOURCE_C` | Espacios adicionales en nombres de producto | Normalizacion con trim y espacios simples |
| Global | Registros sin ID de origen | Exclusion por falta de trazabilidad |
| Global | Fechas nulas o invalidas | Default `1900-01-01` para fechas requeridas |
| Cross-source | Duplicidad fiscal entre fuentes | No se fusionan registros; se conserva trazabilidad |
| Cross-source | Ausencia de SKU comun para productos | Se cargan productos por fuente manteniendo procedencia |

### Decisiones por tipo de problema

| Nivel | Decision aplicada |
| --- | --- |
| Tolerancia alta | Cargar el registro con default documentado: email placeholder, texto `NO DISPONIBLE` o fecha `1900-01-01`. |
| Tolerancia media | Limpiar automaticamente: whitespace, formatos de fecha, separadores decimales, miles, simbolos de moneda y encoding. |
| Tolerancia cero | Excluir y reportar: IDs de origen faltantes, FK huerfanas y pagos cuyo acumulado excede el total de factura. |
| Criterio candidato | Mantener registros de fuentes distintas sin fusionarlos y deduplicar pagos solo por llave de negocio exacta. |

### Conteos de defaults y exclusiones

Los conteos efectivos de cada ejecucion estan en `quality_report.json`. En la ultima ejecucion validada se obtuvo:

```json
{
  "totals_by_action": {
    "cleaned": 41,
    "default_applied": 9,
    "excluded": 16
  }
}
```

- Registros modificados con defaults: `totals_by_action.default_applied`.
- Registros limpiados automaticamente: `totals_by_action.cleaned`.
- Registros excluidos: `totals_by_action.excluded`.
- Motivo exacto de cada exclusion: columna `reason` en `quality_report.csv`.

Los conteos del EDA se conservan en el notebook como diagnostico inicial; los conteos del reporte corresponden a la ejecucion real del pipeline.

### Estrategia para duplicados y pagos conflictivos

- Los duplicados entre fuentes no se fusionan automaticamente. Se cargan como entidades independientes con `source_system` y `source_id` para mantener trazabilidad.
- Los pagos multiples se aceptan cuando el acumulado por factura no supera el total facturado.
- Los pagos duplicados se excluyen solo si coinciden fuente, factura, fecha, monto, metodo y referencia.
- Los pagos que exceden el total acumulado de la factura se excluyen y quedan reportados como `Pago excede el total acumulado de la factura`.

## Validacion

Comandos recomendados:

```bash
docker compose config
docker compose build
docker compose up -d --build
```

Despues de ejecutar el DAG, validar:

- El DAG `etl_csv_to_sqlserver` finaliza correctamente.
- En la vista Graph de Airflow se observan las tareas `limpieza_SOURCE_A`, `limpieza_SOURCE_B`, `limpieza_SOURCE_C`, `unir_y_organizar` y `load_to_sqlserver`.
- Las tablas `etl.Customers`, `etl.Suppliers`, `etl.Products`, `etl.Invoices`, `etl.InvoiceLines` y `etl.Payments` tienen registros cargados.
- Se generan `quality_report.csv` y `quality_report.json` en `solution/airflow/output`.

En la ultima ejecucion validada, los conteos cargados fueron:

| Tabla | Registros |
| --- | ---: |
| `etl.Customers` | 50 |
| `etl.Suppliers` | 40 |
| `etl.Products` | 70 |
| `etl.Invoices` | 48 |
| `etl.InvoiceLines` | 136 |
| `etl.Payments` | 52 |

Consulta sugerida en SQL Server:

```sql
SELECT 'Customers' AS table_name, COUNT(*) AS rows_loaded FROM etl.Customers
UNION ALL SELECT 'Suppliers', COUNT(*) FROM etl.Suppliers
UNION ALL SELECT 'Products', COUNT(*) FROM etl.Products
UNION ALL SELECT 'Invoices', COUNT(*) FROM etl.Invoices
UNION ALL SELECT 'InvoiceLines', COUNT(*) FROM etl.InvoiceLines
UNION ALL SELECT 'Payments', COUNT(*) FROM etl.Payments;
```
