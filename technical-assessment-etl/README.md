# Prueba Técnica - Data Engineer Senior

## Objetivo

Construir un pipeline ETL que extraiga datos de múltiples fuentes CSV heterogéneas, los transforme y unifique, y los cargue en tablas de base de datos SQL Server.

## Contexto de Negocio

Una empresa opera con tres sistemas de información independientes que contienen datos de clientes, proveedores, productos, facturas y pagos. Se requiere consolidar toda la información en un único modelo de datos unificado en SQL Server para reporting y análisis.

## Sistemas Fuente

| Sistema | Descripción | Formato | Idioma columnas | Formato fechas | Formato decimales |
|---------|-------------|---------|-----------------|----------------|-------------------|
| **SOURCE_A** | ERP Moderno (USA) | CSV UTF-8 | Inglés (snake_case) | `YYYY-MM-DD` | Punto decimal (.) |
| **SOURCE_B** | CRM Legado (México) | CSV Latin-1 | Español (PascalCase) | `DD/MM/YYYY` | Coma decimal (,) y punto de miles |
| **SOURCE_C** | Portal de Proveedores | CSV UTF-8 | Mixto (Inglés) | N/A | Símbolo `$` como prefijo |

## Estructura de Archivos Fuente

```
data/
├── source_a/                     # ERP Moderno (inglés)
│   ├── customers.csv             (~25 registros)
│   ├── suppliers.csv             (~20 registros)
│   ├── products.csv              (~25 registros)
│   ├── invoices.csv              (~25 registros)
│   ├── invoice_lines.csv         (~71 registros)
│   └── payments.csv              (~30 registros)
├── source_b/                     # CRM Legado (español)
│   ├── clientes.csv              (~25 registros)
│   ├── proveedores.csv           (~20 registros)
│   ├── productos.csv             (~25 registros)
│   ├── facturas.csv              (~25 registros)
│   ├── factura_lineas.csv        (~71 registros)
│   └── pagos.csv                 (~30 registros)
└── source_c/                     # Portal Proveedores
    └── products_catalog.csv      (~20 registros)
```

## Tablas Destino (SQL Server)

El esquema DDL se encuentra en `sql/target_schema.sql`. Las tablas destino son:

| Tabla | Tipo | Descripción |
|-------|------|-------------|
| `etl.Customers` | Dimensión | Clientes unificados de SOURCE_A y SOURCE_B |
| `etl.Suppliers` | Dimensión | Proveedores unificados de SOURCE_A y SOURCE_B |
| `etl.Products` | Dimensión | Productos unificados de SOURCE_A, SOURCE_B y SOURCE_C |
| `etl.Invoices` | Fact | Cabeceras de factura de SOURCE_A y SOURCE_B |
| `etl.InvoiceLines` | Fact | Líneas de detalle de factura |
| `etl.Payments` | Fact | Pagos recibidos |

Cada tabla incluye:
- **Surrogate key** (`IDENTITY`) para desacoplar del ID de origen
- Campos `source_system` y `source_id` para trazabilidad
- Columnas `created_at` / `updated_at` para auditoría

## ⚠️ Calidad de Datos

**Los archivos fuente contienen deliberadamente datos inconsistentes, duplicados, valores faltantes y errores de formato.** Esto simula escenarios reales de integración de datos.

Se espera que el pipeline maneje estas situaciones según las siguientes reglas:

### Reglas de Tolerancia

| Nivel | Acción | Aplica a |
|-------|--------|----------|
| **Tolerancia alta** | Cargar el registro reemplazando el valor por un default documentado | • Fechas nulas → `1900-01-01` • Emails nulos → `no_disponible@placeholder.com` • Nombres/textos vacíos → `NO DISPONIBLE` |
| **Tolerancia media** | Cargar el registro aplicando limpieza automática y documentarlo | • Whitespace extra en strings (trim) • Formatos de fecha/decimal inconsistentes (normalizar) • Encoding de caracteres (normalizar a UTF-8) |
| **Tolerancia cero** | Excluir el registro y reportarlo en el informe de calidad con el motivo | • FK huérfanas (factura con cliente inexistente, pago con factura inexistente) • Registros sin ID de origen • Pagos que exceden el monto total de la factura asociada |
| **A criterio del candidato** | Decidir la estrategia y justificarla en el informe | • Registros duplicados entre fuentes (mismo tax_id/RFC) • Pagos duplicados a la misma factura |

**Importante:** Los defaults NO deben ocultar el problema. El informe de calidad debe detallar cuántos registros fueron modificados con defaults y cuántos fueron excluidos.

## Entregables Esperados

1. **Script DDL** para crear las tablas en SQL Server (puede usar el provisto en `sql/target_schema.sql` o crear el propio)
2. **Pipeline ETL** funcional en la tecnología de su preferencia (Python, SSIS, T-SQL, Spark, etc.)
3. **Informe de Calidad de Datos** que documente:
   - Hallazgos de calidad encontrados durante el proceso
   - Decisiones tomadas para cada tipo de problema
   - Cantidad de registros modificados con defaults
   - Cantidad de registros excluidos y motivos
   - Estrategia aplicada para resolución de duplicados y pagos conflictivos

## Criterios de Evaluación

1. **Mapeo de datos**: Correcta correspondencia entre columnas fuente y destino considerando los diferentes idiomas y formatos
2. **Transformación**: Manejo adecuado de formatos de fecha, decimales, monedas y normalización de strings
3. **Calidad de datos**: Detección y manejo de los problemas según las reglas de tolerancia definidas
4. **Integridad referencial**: Orden correcto de carga respetando las FK constraints
5. **Documentación**: Claridad del informe de calidad y justificación de decisiones
6. **Organización del código**: Estructura, legibilidad y buenas prácticas

## Inicialización de la Base de Datos (SQL Server)

El proyecto incluye un `docker-compose.yml` para levantar una instancia de SQL Server 2022 Developer con las tablas destino creadas automáticamente en la primera ejecución.

```bash
# Levantar el contenedor (crea la BD y el esquema si no existen)
docker compose up -d
```

**Variables de entorno opcionales:**

| Variable | Descripción | Default |
|----------|-------------|---------|
| `SA_PASSWORD` | Contraseña del usuario `sa` | `P@ssw0rd2025!` |
| `MSSQL_DB_NAME` | Nombre de la base de datos | `ETL_DATA` |

```bash
# Ejemplo con variables personalizadas
SA_PASSWORD=MiPassword123! MSSQL_DB_NAME=etl_produccion docker compose up -d
```

Para re-inicializar la base de datos desde cero:

```bash
docker compose down -v && docker compose up -d
```

**Conexión desde el host:**

```
Server: localhost,1433
User: sa
Password: P@ssw0rd2025!
Database: ETL_DATA
```

## Notas Técnicas

- Los archivos de SOURCE_B pueden requerir detección de encoding (Latin-1/ISO-8859-1)
- Las fechas en SOURCE_B están en formato `DD/MM/YYYY`, en SOURCE_C en `MM/DD/YYYY`
- Los montos en SOURCE_B y SOURCE_C requieren normalización (quitar `$`, convertir coma a punto, eliminar separadores de miles)
- Las FK se deben resolver después de cargar las dimensiones (Customers, Suppliers, Products)
- El orden de carga debe ser: Dimensions → Invoices → InvoiceLines / Payments
