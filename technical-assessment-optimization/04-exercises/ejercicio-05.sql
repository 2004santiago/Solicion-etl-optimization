-- ============================================================================
-- EJERCICIO 5: Deadlock en Actualizacion de Inventario
-- ============================================================================
-- Contexto:
--   El sistema de inventario ejecuta UPDATEs concurrentes desde multiples
--   sesiones. Cuando dos sesiones procesan productos con warehouses en
--   distinto orden, se produce un deadlock.
--
-- Objetivo:
--   Reproducir el deadlock, analizar el deadlock graph, y proponer al menos
--   2 soluciones distintas (a nivel de query y a nivel de base de datos).
--
-- Entregable:
--   1. Reproducir el deadlock abriendo 2 sesiones en SSMS/ADS
--   2. Capturar el deadlock graph (trace flag 1222 o Extended Events)
--   3. Proponer al menos 2 soluciones y explicar cual recomiendas y por que
-- ============================================================================

USE ECommerceDB;
GO

-- ===== REPRODUCIR EL DEADLOCK =====
-- Abre DOS sesiones separadas en tu cliente SQL.
--
-- En la SESION A ejecuta:
/*
BEGIN TRANSACTION;
UPDATE dbo.Inventory
SET QuantityOnHand = QuantityOnHand - 10
WHERE ProductID = 500 AND WarehouseID = 1;

WAITFOR DELAY '00:00:05';

UPDATE dbo.Inventory
SET QuantityOnHand = QuantityOnHand - 20
WHERE ProductID = 500 AND WarehouseID = 2;
COMMIT;
*/
--
-- En la SESION B ejecuta (inmediatamente despues de la A):
/*
BEGIN TRANSACTION;
UPDATE dbo.Inventory
SET QuantityOnHand = QuantityOnHand - 15
WHERE ProductID = 500 AND WarehouseID = 2;

WAITFOR DELAY '00:00:05';

UPDATE dbo.Inventory
SET QuantityOnHand = QuantityOnHand - 25
WHERE ProductID = 500 AND WarehouseID = 1;
COMMIT;
*/
--
-- Una de las sesiones sera victima del deadlock.

-- ===== HABILITAR CAPTURA DE DEADLOCKS =====
-- Para capturar el deadlock graph, ejecuta en UNA sesion aparte:
/*
DBCC TRACEON(1222, -1);
GO
*/
-- Luego de reproducir el deadlock, lee el error log:
/*
EXEC sp_readerrorlog;
GO
*/

-- ===== TU SOLUCION ABAJO =====
-- PASO 1: Descripcion de la causa del deadlock
--   (Explica el grafo de deadlock: que recursos se bloquean y en que orden)
--
-- PASO 2: Solucion 1 - Ordenar los UPDATEs consistentemente
--   (Siempre actualizar por WarehouseID ASC en todas las sesiones)
--   Escribe la version corregida de la transaccion.
--
-- PASO 3: Solucion 2 - Usar lock hints (UPDLOCK, ROWLOCK)
--   (Adquirir locks temprano para evitar conversion de lock)
--
-- PASO 4: Solucion 3 - Cambiar el isolation level de la base de datos
--   (READ_COMMITTED_SNAPSHOT ON)
--   Explica ventajas (elimina deadlocks de lectura) y desventajas (tempdb).
--
-- PASO 5: Solucion 4 - Usar sp_getapplock para serializar
--   (Bloquear a nivel de aplicacion por ProductID)
--
-- PASO 6: Recomendacion final - cual solucion elegirias y por que?
--
