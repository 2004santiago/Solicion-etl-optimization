-- ============================================================================
-- EJERCICIO 3: Busqueda Parcial de Clientes por Email
-- ============================================================================
-- Contexto:
--   El equipo de soporte frecuentemente busca clientes con busqueda parcial
--   de email: WHERE Email LIKE '%gmail%'. Aunque existe un indice en la PK
--   (CustomerID).
--
-- Objetivo:
--   Reducir el tiempo de busqueda. Justifica por que
--   la solucion elegida es la mas adecuada para este caso.
--
-- Entregable:
--   1. Ejecuta la consulta base y anota el tiempo
--   2. Explica por que LIKE '%...%' no puede usar indices B-tree
--   3. Implementa al menos una solucion (puede incluir cambios de schema)
--   4. Discute alternativas y sus tradeoffs
-- ============================================================================

USE ECommerceDB;
GO

SET STATISTICS TIME ON;
SET STATISTICS IO ON;
GO

-- ===== CONSULTA BASE (NO MODIFICAR) =====
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

-- ===== TU SOLUCION ABAJO =====
-- PASO 1: Diagnostico - Por que LIKE '%text%' no es SARGable?
--
-- PASO 2: Solucion(es) propuesta(s)
--   (Puede incluir FULLTEXT INDEX, computed columns + indice,
--    re-diseno de la tabla, uso de herramientas externas, etc.)
--
-- PASO 3: Implementacion y medicion del nuevo tiempo
--
-- PASO 4: Discusion de alternativas y tradeoffs
--
