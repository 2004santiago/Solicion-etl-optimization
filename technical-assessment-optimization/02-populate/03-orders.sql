USE ECommerceDB;
GO

SET NOCOUNT ON;

DECLARE @target INT = 5000000;
DECLARE @batch_size INT = 100000;
DECLARE @inserted BIGINT = 0;
DECLARE @shipping_countries TABLE (code CHAR(2), idx INT);
INSERT INTO @shipping_countries VALUES
    ('US',0),('MX',1),('CA',2),('UK',3),('DE',4),('FR',5),('ES',6),('BR',7),('AR',8),('CO',9),
    ('PE',10),('CL',11),('JP',12),('AU',13),('IT',14),('NL',15);

PRINT '--- Poblando Orders: 5,000,000 filas ---';

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

    INSERT INTO dbo.Orders WITH (TABLOCK) (CustomerID, OrderDate, Status, TotalAmount, ShippingCountry, PaymentMethod, WarehouseID)
    SELECT
        ((n * 7919 + @inserted * 3571) % 1000000) + 1,
        DATEADD(MINUTE, -(n * 7 + @inserted * 11) % 1576800, GETUTCDATE()),
        CASE
            WHEN n % 100 < 55 THEN 4
            WHEN n % 100 < 85 THEN 3
            WHEN n % 100 < 95 THEN 2
            WHEN n % 100 < 98 THEN 5
            ELSE 1
        END,
        CAST((n * 7933 + 271) % 500000 / 100.0 AS DECIMAL(12,2)) + 10.00,
        (SELECT TOP 1 code FROM @shipping_countries WHERE idx = n % 16),
        1 + (n % 4),
        1 + (n % 10)
    FROM Nums;

    SET @inserted = @inserted + @@ROWCOUNT;
END;

PRINT '--- Orders: ' + CAST(@inserted AS VARCHAR) + ' filas insertadas ---';
GO
