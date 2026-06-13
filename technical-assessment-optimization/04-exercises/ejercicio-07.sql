-- ============================================================================
-- EJERCICIO 7: Diagnostico con DMVs
-- ============================================================================
-- Contexto:
--   La base de datos ECommerceDB ha estado degradandose con el tiempo.
--   Tu tarea es usar Dynamic Management Views (DMVs) para diagnosticar
--   los principales problemas de rendimiento.
--
-- Objetivo:
--   Escribir consultas contra las DMVs para identificar:
--     a) Las 5 consultas que mas CPU consumen
--     b) Los indices faltantes mas impactantes (missing index DMVs)
--     c) Los indices existentes que no se usan
--     d) Los waits mas significativos y su posible causa
--     e) (Opcional) Estadisticas desactualizadas
--
-- Entregable:
--   Para cada categoria anterior, escribe y ejecuta la consulta DMV.
--   Interpreta los resultados y propone acciones concretas.
-- ============================================================================

USE ECommerceDB;
GO

-- ===== PARTE A: Top 5 consultas por CPU =====
-- Escribe una consulta que use sys.dm_exec_query_stats y
-- sys.dm_exec_sql_text para obtener las 5 consultas con mayor
-- total_worker_time (CPU) en el plan cache.
--
-- Incluye: el texto de la consulta, CPU total, CPU promedio,
-- tiempo transcurrido, lecturas logicas, ejecuciones.

-- TU CONSULTA AQUI:


GO

-- ===== PARTE B: Indices faltantes =====
-- Escribe una consulta que use sys.dm_db_missing_index_details,
-- sys.dm_db_missing_index_groups, y sys.dm_db_missing_index_columns
-- para identificar los indices que SQL Server recomienda crear.
--
-- Ordena por impacto estimado (avg_total_user_cost * avg_user_impact).
-- Incluye: nombre de tabla, columnas equality, columnas inequality,
-- columnas INCLUDE sugeridas, impacto estimado.

-- TU CONSULTA AQUI:


GO

-- ===== PARTE C: Indices no usados =====
-- Escribe una consulta que use sys.dm_db_index_usage_stats para
-- encontrar indices que tengan cero o muy pocos seeks/scans pero
-- muchas actualizaciones (user_updates).
--
-- Estos son candidatos a ser eliminados porque solo generan costo
-- de mantenimiento sin beneficio de lectura.

-- TU CONSULTA AQUI:


GO

-- ===== PARTE D: Wait Statistics =====
-- Escribe una consulta que use sys.dm_os_wait_stats para identificar
-- los tipos de espera mas frecuentes.
--
-- Excluye waits de background (LAZYWRITER, SLEEP, etc.).
-- Interpreta los 3 waits mas altos y su posible causa.

-- TU CONSULTA AQUI:


GO

-- ===== PARTE E (Opcional): Estadisticas desactualizadas =====
-- Usa sys.dm_db_stats_properties para encontrar estadisticas que
-- no se han actualizado en mucho tiempo o tienen un porcentaje
-- alto de modificaciones sin actualizar.

-- TU CONSULTA AQUI:


GO

-- ===== RESUMEN DE HALLAZGOS =====
-- Basado en los resultados anteriores, resume:
--
-- 1. Cuales son los 3 problemas principales detectados
-- 2. Que acciones concretas propones para resolver cada uno
-- 3. Como medirias la mejora despues de aplicar los cambios
--
