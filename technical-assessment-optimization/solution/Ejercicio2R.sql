-- Diagnóstico
-- Sin índices de soporte, Orders y OrderItems hacían table scans completos.
-- Evidencia: scan count 13 (paralelo), 99K + 26K logical reads.

-- Índices creados
CREATE INDEX IX_Orders_OrderDate_OrderID
ON dbo.Orders (OrderDate)
INCLUDE (OrderID);
-- Permite seek directo por el filtro WHERE OrderDate >= DATEADD(MONTH,-3,...)

CREATE INDEX IX_OrderItems_OrderID
ON dbo.OrderItems (OrderID)
INCLUDE (ProductID, Quantity, LineTotal);
-- Permite resolver el JOIN con Orders y cubrir las columnas del SUM() sin tocar el clustered

-- Resultado
-- Elapsed time: 919ms → 274ms  (-70%)
-- Orders logical reads: 26,522 → 937  (-96%)
-- OrderItems logical reads: 99,045 → 65,821  (-34%)
-- La consulta base (ROW_NUMBER) no requirió modificación.