USE ECommerceDB;
GO

SET NOCOUNT ON;

DECLARE @target INT = 20000000;
DECLARE @batch_size INT = 100000;
DECLARE @inserted BIGINT = 0;
DECLARE @total_orders INT = 5000000;

PRINT '--- Poblando OrderHistory: 20,000,000 filas (~10 min) ---';

WHILE @inserted < @target
BEGIN
    WITH
    L0   AS (SELECT 1 AS c UNION ALL SELECT 1),
    L1   AS (SELECT 1 AS c FROM L0 A CROSS JOIN L0 B),
    L2   AS (SELECT 1 AS c FROM L1 A CROSS JOIN L1 B),
    L3   AS (SELECT 1 AS c FROM L2 A CROSS JOIN L2 B),
    L4   AS (SELECT 1 AS c FROM L3 A CROSS JOIN L3 B),
    L5   AS (SELECT 1 AS c FROM L4 A CROSS JOIN L4 B),
    Nums AS (SELECT TOP(@batch_size) ROW_NUMBER() OVER(ORDER BY (SELECT NULL)) AS n FROM L5)

    INSERT INTO dbo.OrderHistory WITH (TABLOCK) (OrderID, OldStatus, NewStatus, ChangedBy, ChangeDate, Notes)
    SELECT
        ((n * 6343 + @inserted * 2713) % @total_orders) + 1,
        CASE (n % 5)
            WHEN 0 THEN NULL
            WHEN 1 THEN 1
            WHEN 2 THEN 2
            WHEN 3 THEN 3
            ELSE 4
        END,
        CASE (n % 5)
            WHEN 0 THEN 1
            WHEN 1 THEN 2
            WHEN 2 THEN 3
            WHEN 3 THEN 4
            ELSE 5
        END,
        CASE (n % 6)
            WHEN 0 THEN 'system'
            WHEN 1 THEN 'warehouse_admin'
            WHEN 2 THEN 'shipping_api'
            WHEN 3 THEN 'cs_agent'
            WHEN 4 THEN 'payment_gateway'
            ELSE 'auto_cancel'
        END,
        DATEADD(MINUTE, -(n * 13 + 7) % 1576800, GETUTCDATE()),
        CASE WHEN n % 3 = 0 THEN CONCAT('Status transition for order batch ', n % 1000) ELSE NULL END
    FROM Nums;

    SET @inserted = @inserted + @@ROWCOUNT;
END;

PRINT '--- OrderHistory: ' + CAST(@inserted AS VARCHAR) + ' filas insertadas ---';
GO
