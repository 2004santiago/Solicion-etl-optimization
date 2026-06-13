USE ECommerceDB;
GO

SET NOCOUNT ON;

DECLARE @target INT = 15000000;
DECLARE @batch_size INT = 100000;
DECLARE @inserted BIGINT = 0;

PRINT '--- Poblando OrderItems: 15,000,000 filas ---';

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

    INSERT INTO dbo.OrderItems WITH (TABLOCK) (OrderID, ProductID, Quantity, UnitPrice, Discount, LineTotal)
    SELECT
        ((n * 6343 + @inserted * 2713) % 5000000) + 1,
        ((n * 7103 + @inserted * 1399) % 500000) + 1,
        1 + (n % 10),
        CAST((n * 503 + 199) % 99900 / 100.0 + 1.99 AS DECIMAL(10,2)),
        CASE WHEN n % 7 = 0 THEN CAST((n % 50) AS DECIMAL(5,2)) ELSE 0.00 END,
        CAST(
            (1 + (n % 10)) *
            CAST((n * 503 + 199) % 99900 / 100.0 + 1.99 AS DECIMAL(10,2)) *
            (1.0 - CASE WHEN n % 7 = 0 THEN (n % 50) / 100.0 ELSE 0.0 END)
        AS DECIMAL(12,2))
    FROM Nums;

    SET @inserted = @inserted + @@ROWCOUNT;
END;

PRINT '--- OrderItems: ' + CAST(@inserted AS VARCHAR) + ' filas insertadas ---';
GO
