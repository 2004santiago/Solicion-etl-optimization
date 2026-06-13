USE ECommerceDB;
GO

SET NOCOUNT ON;

DECLARE @target INT = 2000000;
DECLARE @batch_size INT = 100000;
DECLARE @inserted BIGINT = 0;

PRINT '--- Poblando Inventory: 2,000,000 filas ---';

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

    INSERT INTO dbo.Inventory WITH (TABLOCK) (ProductID, WarehouseID, QuantityOnHand, ReorderLevel, LastRestockDate)
    SELECT
        ((n * 7103 + @inserted * 1399) % 500000) + 1,
        1 + (n % 10),
        50 + (n % 950),
        CASE WHEN n % 5 < 2 THEN 20 ELSE 50 END,
        CASE WHEN n % 3 = 0 THEN DATEADD(DAY, -(n % 60), GETUTCDATE()) ELSE DATEADD(DAY, -(n % 180), GETUTCDATE()) END
    FROM Nums;

    SET @inserted = @inserted + @@ROWCOUNT;
END;

PRINT '--- Inventory: ' + CAST(@inserted AS VARCHAR) + ' filas insertadas ---';
GO
