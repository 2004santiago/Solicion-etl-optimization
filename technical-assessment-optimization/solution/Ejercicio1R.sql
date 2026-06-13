-- EJERCICIO 1: Reporte de Ventas Mensuales — SOLUCIÓN

USE ECommerceDB;
GO

-- ============================================================================
-- Diagnóstico
-- ----------------------------------------------------------------------------
-- La consulta base presentaba los siguientes problemas:
--
-- 1. FULL SCAN en Orders (5M filas, 26,522 reads):
--    Sin índice en OrderDate, el engine lee TODA la tabla para filtrar 2024.

-- 2. FULL SCAN en OrderItems (15M filas, 98,981 reads):
--    El join por OrderID sin índice fuerza un scan completo, este es el mayor costo de la consulta.

-- 3. FULL SCAN en Products (500K filas, 6,398 reads):
--    Sin índice cubriente, el engine accede a la tabla base para obtener el CategoryID después del join por ProductID.

-- 4. Compile time de 1,210 ms:
--    El optimizador tardó tanto porque no tenía estadísticas de índices para elegir un plan eficiente. Tuvo que evaluar más alternativas.

-- 5. Read-ahead reads ~119K:
--    SQL Server anticipó que necesitaría muchas páginas y las pre-cargó. Señal de scans masivos.

-- Estrategia: crear índices cubrientes que permitan seeks en lugar de scans, reduciendo el I/O sin modificar la consulta base.


-- ============================================================================
-- Índices
-- ============================================================================

-- Índice 1: Orders — soporta el filtro WHERE OrderDate y el join con OrderItems
-- OrderDate al frente → range seek solo sobre el año 2024
-- OrderID incluido  → el join downstream puede resolverse sin volver a la tabla
CREATE INDEX IX_Orders_OrderDate_OrderID
    ON dbo.Orders (OrderDate, OrderID);
GO

-- Índice 2: OrderItems — soporta el join por OrderID
-- Con las columnas del SELECT en INCLUDE, el engine no necesita tocar la tabla base después del seek
CREATE INDEX IX_OrderItems_OrderID_Covering
    ON dbo.OrderItems (OrderID)
    INCLUDE (ProductID, Quantity, LineTotal);
GO

-- Índice 3: Products — soporta el join por ProductID
-- INCLUDE CategoryID evita un key lookup al clustered index de Products para obtener la categoría que necesita el GROUP BY
CREATE INDEX IX_Products_ProductID_CategoryID
    ON dbo.Products (ProductID)
    INCLUDE (CategoryID);
GO

-- ============================================================================
-- Consulta base 
-- ============================================================================
SET STATISTICS TIME ON;
SET STATISTICS IO ON;
GO

SELECT
    p.CategoryID,
    c.CategoryName,
    YEAR(o.OrderDate)  AS OrderYear,
    MONTH(o.OrderDate) AS OrderMonth,
    SUM(oi.LineTotal)  AS TotalVentas,
    COUNT_BIG(DISTINCT o.OrderID) AS NumOrdenes,
    SUM(oi.Quantity)    AS UnidadesVendidas
FROM dbo.Orders o
INNER JOIN dbo.OrderItems oi ON o.OrderID = oi.OrderID
INNER JOIN dbo.Products p    ON oi.ProductID = p.ProductID
INNER JOIN dbo.Categories c  ON p.CategoryID = c.CategoryID
WHERE o.OrderDate >= '2024-01-01'
  AND o.OrderDate <  '2025-01-01'
GROUP BY
    p.CategoryID,
    c.CategoryName,
    YEAR(o.OrderDate),
    MONTH(o.OrderDate)
ORDER BY
    OrderYear,
    OrderMonth,
    p.CategoryID;
GO

SET STATISTICS TIME OFF;
SET STATISTICS IO OFF;
GO

-- ============================================================================
-- Resultados
-- ----------------------------------------------------------------------------
--  Métrica              Antes        Después      Reducción
--  -------------------- ------------ ------------ ----------
--  CPU time             5,933 ms     3,299 ms     -44%
--  Elapsed time         1,195 ms       457 ms     -62%
--  Compile time         1,210 ms        52 ms     -96%
--  Orders reads        26,522         3,777       -86%
--  OrderItems reads    98,981        65,821       -34%
--  Products reads       6,398           930       -85%
--  Read-ahead reads   ~119,000           ~46      -99.9%
--
-- El elapsed time pasó de 1,195 ms a 457 ms (-62%).
-- Orders y Products responden ahora con seeks en lugar de scans.
-- OrderItems sigue siendo el mayor costo porque el volumen de filas a agregar es intrínseco al query;
-- el índice cubriente elimina los key lookups pero no reduce las filas.
