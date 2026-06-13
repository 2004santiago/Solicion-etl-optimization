-- ============================================================================
-- EJERCICIO 1: Reporte de Ventas Mensuales
-- ============================================================================
-- Contexto:
--   El CFO necesita un reporte de ventas por categoria y mes para el ultimo
--   ano. 
--
-- Objetivo:
--   Optimizar la consulta para que ejecute en el menor tiempo posible.
--
-- Entregable:
--   1. Ejecuta la consulta base y anota el tiempo con SET STATISTICS TIME ON
--   2. Analiza el plan de ejecucion real (incluye el XML o captura)
--   3. Implementa tu solucion (indices, reescritura, etc.)
--   4. Vuelve a ejecutar y anota el nuevo tiempo
--   5. Documenta tu razonamiento como comentarios en este archivo
-- ============================================================================

USE ECommerceDB;
GO

SET STATISTICS TIME ON;
SET STATISTICS IO ON;
GO

-- ===== CONSULTA BASE (NO MODIFICAR) =====
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
INNER JOIN dbo.Products p ON oi.ProductID = p.ProductID
INNER JOIN dbo.Categories c ON p.CategoryID = c.CategoryID
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

-- ===== TU SOLUCION ABAJO =====
-- PASO 1: Diagnostico del plan de ejecucion
--   (Explica que observas: table scans, key lookups, hash joins, etc.)
--
-- PASO 2: Indices creados (si aplica)
--
-- PASO 3: Consulta optimizada (si requiere reescritura)
--
-- PASO 4: Resultado (tiempo antes / tiempo despues)
--
