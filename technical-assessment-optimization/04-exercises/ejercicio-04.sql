-- ============================================================================
-- EJERCICIO 4: Parameter Sniffing en Stored Procedure
-- ============================================================================
-- Contexto:
--   El SP GetOrdersByStatus se usa para filtrar ordenes por estado.
--   Con @Status = 1 (pending, ~2% de las filas) ejecuta en <1s usando
--   Index Seek. Con @Status = 4 (delivered, ~55% de las filas) tarda >20s
--   porque reutiliza el plan cacheado que asume pocas filas.
--
-- Objetivo:
--   Diagnosticar el problema de parameter sniffing y proponer al menos
--   2 soluciones distintas. Implementar la mas adecuada para este SP.
--
-- Entregable:
--   1. Crear el SP base y ejecutarlo con ambos parametros
--   2. Ejecutar varias veces alternando parametros para reproducir el bug
--   3. Explicar por que ocurre el parameter sniffing
--   4. Implementar al menos 2 soluciones y compararlas
-- ============================================================================

USE ECommerceDB;
GO

-- Limpiar planes cacheados para este SP
IF OBJECT_ID('dbo.GetOrdersByStatus', 'P') IS NOT NULL
    DROP PROCEDURE dbo.GetOrdersByStatus;
GO

-- ===== STORED PROCEDURE BASE (NO MODIFICAR) =====
CREATE PROCEDURE dbo.GetOrdersByStatus
    @Status TINYINT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        o.OrderID,
        o.CustomerID,
        o.OrderDate,
        o.TotalAmount,
        o.ShippingCountry
    FROM dbo.Orders o
    WHERE o.Status = @Status
    ORDER BY o.OrderDate DESC;
END;
GO

-- ===== REPRODUCIR EL PROBLEMA =====
-- PASO 1: Ejecutar con un valor que devuelva pocas filas primero
--         (esto cachea un plan con Index Seek)
DBCC FREEPROCCACHE;
GO
EXEC dbo.GetOrdersByStatus @Status = 1;   -- pending: ~2% de filas → Index Seek
GO

-- PASO 2: Ejecutar con un valor que devuelva muchas filas
--         (reutiliza el plan cacheado incorrecto)
EXEC dbo.GetOrdersByStatus @Status = 4;   -- delivered: ~55% de filas → deberia ser Scan
GO

-- ===== TU SOLUCION ABAJO =====
-- PASO 3: Explica que ocurre con el plan cacheado
--
-- PASO 4: Solucion 1 con OPTION RECOMPILE - ventajas y desventajas
--
-- PASO 5: Solucion 2 con OPTIMIZE FOR UNKNOWN - ventajas y desventajas
--
-- PASO 6: Comparacion de tiempos entre ambas soluciones
--
-- PASO 7: Que otras alternativas existen? (Query Store, plan guides, IF/ELSE)
--
