# Ejercicio 3: Busqueda Parcial de Clientes por Email

## 1. Consulta base y tiempo inicial

```sql
USE ECommerceDB;
GO

SET STATISTICS TIME ON;
SET STATISTICS IO ON;
GO

DECLARE @search NVARCHAR(50) = N'%gmail%';

SELECT
    CustomerID,
    Email,
    FullName,
    Country,
    City,
    SignupDate,
    Status
FROM dbo.Customers
WHERE Email LIKE @search
OPTION (RECOMPILE);
GO

SET STATISTICS TIME OFF;
SET STATISTICS IO OFF;
GO
```

**Resultados:**

| Métrica        | Valor      |
|----------------|------------|
| Elapsed time   | 207 ms     |
| CPU time       | 1,863 ms   |
| Logical reads  | 20,600     |
| Scan count     | 13         |

---

## 2. Por qué `LIKE '%...%'` no puede usar índices B-tree

Un índice B-tree ordena los valores de izquierda a derecha. SQL Server solo puede hacer un *seek* cuando conoce el **prefijo** del valor buscado.

```sql
-- SARGable: prefijo conocido → Index Seek
WHERE Email LIKE 'john%'

-- No SARGable: prefijo desconocido → Full Scan
WHERE Email LIKE '%gmail%'
```

Con `'%gmail%'` el motor no sabe en qué rama del árbol empezar, por lo que descarta el índice y lee cada fila de la tabla. La condición **no es SARGable** (*Search ARGument Able*) porque no puede traducirse a un rango de valores en el índice.

---

## 3. Solución implementada: Columna computada persistida + índice B-tree


El caso de uso real es buscar clientes por **dominio de email** (`gmail`, `hotmail`, etc.). El email tiene estructura predecible: `usuario@dominio.com`. Extraer el dominio como columna persistida convierte la búsqueda en una búsqueda por prefijo (`'gmail%'`), que sí es SARGable.


### Implementación

**#1 Agregar columna computada persistida:**

```sql
ALTER TABLE dbo.Customers
ADD EmailDomain AS LOWER(
    SUBSTRING(Email, CHARINDEX('@', Email) + 1, LEN(Email))
) PERSISTED;
GO
```

- `CHARINDEX('@', Email) + 1` ubica el inicio del dominio.
- `PERSISTED` hace que el valor se calcule una sola vez y se almacene físicamente, permitiendo indexarlo.

**#2 Crear índice covering sobre EmailDomain:**

```sql
CREATE INDEX IX_Customers_EmailDomain
    ON dbo.Customers(EmailDomain)
    INCLUDE (CustomerID, Email, FullName, Country, City, SignupDate, Status);
GO
```

El `INCLUDE` agrega todas las columnas del `SELECT` al índice, permitiendo que SQL Server resuelva la consulta solo desde el índice sin volver a la tabla (covering index).

**#3 Consulta optimizada:**

```sql
SELECT
    CustomerID, Email, FullName, Country, City, SignupDate, Status
FROM dbo.Customers
WHERE EmailDomain LIKE 'gmail%';
```

---

## 4. Resultados comparativos

| Métrica       | Base        | Optimizada | Mejora   |
|---------------|-------------|------------|----------|
| Elapsed time  | 207 ms      | ~0 ms      | >99%     |
| CPU time      | 1,863 ms    | 0 ms       | >99%     |
| Logical reads | 20,600      | **4**      | 99.98%   |
| Scan count    | 13 (paralelo) | 1        | Index Seek |


---

## 5. Alternativas y tradeoffs

| Solución | Caso que resuelve | Ventajas | Desventajas |
|---|---|---|---|
| **Columna computada + índice** *(implementada)* | Búsqueda por dominio de email | Sin infraestructura extra, SARGable, covering index | Solo funciona si la búsqueda sigue la estructura `@dominio` |
| **Full-Text Index** | Búsqueda por cualquier token dentro del texto | Resuelve el caso general de `LIKE '%texto%'`, nativo en SQL Server | Requiere el componente `mssql-server-fts` instalado; no disponible en este entorno |
| **Índice B-tree en Email** | Búsqueda por prefijo (`'john%'`) | Simple, sin cambios de schema | No resuelve `LIKE '%texto%'` en absoluto |
| **Motor externo (Elasticsearch)** | Búsqueda de texto completo a escala | Más potente, soporta fuzzy search, ranking por relevancia | Alta complejidad operacional, sincronización de datos, infraestructura adicional |
