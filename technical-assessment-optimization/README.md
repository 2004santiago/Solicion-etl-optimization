# Prueba Tecnica — Data Engineer: Optimizacion SQL Server

## Requisitos

- Docker y Docker Compose instalados
- Un cliente SQL para conectarse (SSMS, Azure Data Studio, DBeaver, sqlcmd)
- ~15 GB de espacio libre en disco para los datos generados

## Levantar el entorno

```bash
# 1. Iniciar SQL Server
docker compose up -d

# 2. Esperar a que el contenedor este saludable (~30s)
docker compose ps

# 3. Crear esquema de base de datos
docker exec -i sqlserver_test /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'PruebaT3cnica!' -C -i /schema/ddl.sql

# 4. Poblar tablas con datos de prueba (~10-15 min)
for f in 01-customers 02-products 03-orders 04-order-items 05-inventory 06-order-history; do
  echo "Poblando ${f}..."
  docker exec -i sqlserver_test /opt/mssql-tools18/bin/sqlcmd \
    -S localhost -U sa -P 'PruebaT3cnica!' -C -i "/populate/${f}.sql"
done

# 5. Aplicar indices baseline
docker exec -i sqlserver_test /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'PruebaT3cnica!' -C -i /fixtures/create-baseline-indexes.sql
```

## Conexion

| Parametro     | Valor                  |
|---------------|------------------------|
| Server        | `localhost,1433`       |
| Usuario       | `sa`                   |
| Contrasena    | `PruebaT3cnica!`       |
| Base de datos | `ECommerceDB`          |
| Cifrado       | Desactivar / TrustServerCertificate=true |

## Tablas y volumenes

| Tabla          | Filas aprox. |
|----------------|--------------|
| Customers      | 1,000,000    |
| Products       | 500,000      |
| Orders         | 5,000,000    |
| OrderItems     | 15,000,000   |
| Inventory      | 2,000,000    |
| OrderHistory   | 20,000,000   |

## Ejercicios

Los ejercicios estan en la carpeta `04-exercises/`. Cada archivo contiene el enunciado y la consulta base a optimizar.

1. Reporte de ventas mensuales
2. Top 3 productos por categoria
3. Busqueda parcial de clientes por email
4. Parameter sniffing en stored procedure
5. Deadlock en actualizacion de inventario
6. Auditoria en tabla masiva (20M filas)
7. Diagnostico con DMVs

Para cada ejercicio debes:

1. Ejecutar la consulta base y medir el tiempo con `SET STATISTICS TIME ON`
2. Analizar el plan de ejecucion con `SET STATISTICS XML ON` o mostrar plan grafico
3. Diagnosticar el problema de rendimiento
4. Implementar la solucion (indices, reescritura, configuracion)
5. Medir el tiempo mejorado y documentar la solucion como comentario en el mismo archivo .sql

## Limpiar

```bash
docker compose down -v
```
