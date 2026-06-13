-- ============================================================================
-- EJERCICIO 2: Top 3 Productos por Categoria
-- ============================================================================
-- Contexto:
--   Marketing necesita los 3 productos mas vendidos por categoria en el
--   ultimo trimestre (ultimos 3 meses). La consulta actual usa ROW_NUMBER().
--
-- Objetivo:
--   Optimizar la consulta para que disminuya el tiempo de ejecucion.
--
-- Entregable:
--   1. Ejecuta la consulta base y anota el tiempo
--   2. Analiza el plan de ejecucion
--   3. Implementa tu solucion
--   4. Documenta tu razonamiento
-- ============================================================================

USE ECommerceDB;
GO

SET STATISTICS TIME ON;
SET STATISTICS IO ON;
GO

-- ===== CONSULTA BASE (NO MODIFICAR) =====
WITH ProductSales AS (
    SELECT
        p.ProductID,
        p.ProductName,
        p.CategoryID,
        SUM(oi.Quantity)   AS TotalQuantity,
        SUM(oi.LineTotal)  AS TotalRevenue,
        ROW_NUMBER() OVER (
            PARTITION BY p.CategoryID
            ORDER BY SUM(oi.Quantity) DESC
        ) AS RankNum
    FROM dbo.Orders o
    INNER JOIN dbo.OrderItems oi ON o.OrderID = oi.OrderID
    INNER JOIN dbo.Products p ON oi.ProductID = p.ProductID
    WHERE o.OrderDate >= DATEADD(MONTH, -3, GETUTCDATE())
    GROUP BY p.ProductID, p.ProductName, p.CategoryID
)
SELECT
    ps.CategoryID,
    c.CategoryName,
    ps.RankNum,
    ps.ProductID,
    ps.ProductName,
    ps.TotalQuantity,
    ps.TotalRevenue
FROM ProductSales ps
INNER JOIN dbo.Categories c ON ps.CategoryID = c.CategoryID
WHERE ps.RankNum <= 3
ORDER BY ps.CategoryID, ps.RankNum;
GO

SET STATISTICS TIME OFF;
SET STATISTICS IO OFF;
GO

-- ===== TU SOLUCION ABAJO =====
-- PASO 1: Diagnostico
--
-- PASO 2: Indices creados
--
-- PASO 3: Consulta optimizada (si aplica)
--
-- PASO 4: Resultado
--
