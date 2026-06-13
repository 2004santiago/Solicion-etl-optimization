USE ECommerceDB;
GO

SET NOCOUNT ON;

DECLARE @target INT = 1000000;
DECLARE @batch_size INT = 100000;
DECLARE @inserted INT = 0;
DECLARE @countries TABLE (code CHAR(2), idx INT);
INSERT INTO @countries VALUES
    ('US',0),('MX',1),('CA',2),('UK',3),('DE',4),('FR',5),('ES',6),('BR',7),('AR',8),('CO',9),
    ('PE',10),('CL',11),('JP',12),('AU',13),('IT',14),('NL',15);

PRINT '--- Poblando Customers: 1,000,000 filas ---';

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

    INSERT INTO dbo.Customers WITH (TABLOCK) (Email, FullName, Country, Region, City, SignupDate, Status, CreditLimit, LoyaltyTier)
    SELECT
        CONCAT('user', @inserted + n, '@domain', n % 7, '.com'),
        CONCAT('Customer Name ', @inserted + n),
        (SELECT TOP 1 code FROM @countries WHERE idx = n % 16),
        CONCAT('Region ', n % 50),
        CONCAT('City ', n % 500),
        DATEADD(DAY, -(n % 2190), DATEADD(DAY, -1, GETUTCDATE())),
        1 + (n % 3),
        CAST((n * 17 + 523) % 500000 / 100.0 AS DECIMAL(12,2)),
        CASE WHEN n % 10 < 3 THEN NULL ELSE 1 + (n % 5) END
    FROM Nums;

    SET @inserted = @inserted + @@ROWCOUNT;
END;

PRINT '--- Customers: ' + CAST(@inserted AS VARCHAR) + ' filas insertadas ---';
GO
