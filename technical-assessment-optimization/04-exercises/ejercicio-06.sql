-- ============================================================================
-- EJERCICIO 6: Auditoria en Tabla Masiva (20M filas)
-- ============================================================================
-- Contexto:
--   La tabla OrderHistory tiene 20 millones de registros de cambios de
--   estado de ordenes. El equipo de auditoria necesita consultar cambios
--   en un rango de fechas. Actualmente la consulta hace un Scan sobre toda la tabla.
--
-- Objetivo:
--   Reducir el tiempo de consulta para un rango
--   de 6 meses. Considera tanto soluciones de indices como cambios
--   estructurales (particionamiento, columnstore).
--
-- Entregable:
--   1. Ejecuta la consulta base y anota el tiempo
--   2. Analiza el plan de ejecucion
--   3. Implementa tu solucion
--   4. Discute por que elegiste ese approach y que alternativas consideraste
-- ============================================================================

USE ECommerceDB;
GO

SET STATISTICS TIME ON;
SET STATISTICS IO ON;
GO

-- ===== CONSULTA BASE (NO MODIFICAR) =====
DECLARE @StartDate DATETIME2 = '2024-01-01';
DECLARE @EndDate   DATETIME2 = '2024-07-01';

SELECT
    OrderID,
    OldStatus,
    NewStatus,
    ChangedBy,
    ChangeDate,
    Notes
FROM dbo.OrderHistory
WHERE ChangeDate >= @StartDate
  AND ChangeDate <  @EndDate
ORDER BY ChangeDate DESC;
GO

SET STATISTICS TIME OFF;
SET STATISTICS IO OFF;
GO

-- ===== CONSULTA DE AGREGACION (tambien lenta) =====
SET STATISTICS TIME ON;
SET STATISTICS IO ON;
GO

SELECT
    ChangedBy,
    COUNT_BIG(*)       AS TotalChanges,
    MIN(ChangeDate)    AS FirstChange,
    MAX(ChangeDate)    AS LastChange
FROM dbo.OrderHistory
WHERE ChangeDate >= '2024-01-01'
  AND ChangeDate <  '2025-01-01'
GROUP BY ChangedBy
ORDER BY TotalChanges DESC;
GO

SET STATISTICS TIME OFF;
SET STATISTICS IO OFF;
GO

-- ===== TU SOLUCION ABAJO =====
-- PASO 1: Diagnostico
--   (Que tipo de scan ocurre? Que indice(s) hacen falta?)
--
-- PASO 2: Solucion con indice(s)
--   (Que indice(s) crearias? Por que elegiste covering vs filtered?)
--
-- PASO 3: Solucion con particionamiento (si aplica)
--   (Como partirias la tabla? Que funcion de particion usarias?)
--
-- PASO 4: Solucion con Columnstore (si aplica)
--   (Cuando conviene un CCI vs NCC vs indices rowstore?)
--
-- PASO 5: Estrategia de archivado/purga a largo plazo
--
-- PASO 6: Medir mejora y comparar approaches
--
