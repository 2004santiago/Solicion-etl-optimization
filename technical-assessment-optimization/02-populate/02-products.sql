USE ECommerceDB;
GO

SET NOCOUNT ON;

PRINT '--- Poblando Categories: 50 filas ---';

INSERT INTO dbo.Categories WITH (TABLOCK) (CategoryName)
VALUES
    ('Electronics'),('Clothing'),('Home & Garden'),('Sports'),('Books'),
    ('Toys & Games'),('Health & Beauty'),('Automotive'),('Food & Beverages'),('Office Supplies'),
    ('Pet Supplies'),('Jewelry'),('Music'),('Movies'),('Tools'),
    ('Baby Products'),('Furniture'),('Grocery'),('Shoes'),('Accessories'),
    ('Outdoor'),('Kitchen'),('Bedding'),('Lighting'),('Stationery'),
    ('Cleaning'),('Hardware'),('Paint'),('Garden'),('Pool'),
    ('Camping'),('Fitness'),('Bikes'),('Gaming'),('Software'),
    ('Cameras'),('Phones'),('Tablets'),('Laptops'),('Desktops'),
    ('Monitors'),('Printers'),('Networking'),('Storage'),('Cables'),
    ('Audio'),('Video'),('Wearables'),('Drones'),('Smart Home');

PRINT '--- Categories: listo ---';
GO

PRINT '--- Poblando Products: 500,000 filas ---';

DECLARE @target INT = 500000;
DECLARE @batch_size INT = 50000;
DECLARE @inserted INT = 0;
DECLARE @max_cat INT;
SELECT @max_cat = MAX(CategoryID) FROM dbo.Categories;

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

    INSERT INTO dbo.Products WITH (TABLOCK) (SKU, ProductName, CategoryID, UnitPrice, CostPrice, IsActive, Weight, CreatedDate)
    SELECT
        CONCAT('SKU-', RIGHT('0000000000' + CAST(@inserted + n AS VARCHAR), 10)),
        CONCAT('Product ', @inserted + n),
        ((n * 31 + 7) % @max_cat) + 1,
        CAST((n * 503 + 199) % 99900 / 100.0 + 1.99 AS DECIMAL(10,2)),
        CAST((n * 503 + 199) % 99900 / 200.0 + 0.99 AS DECIMAL(10,2)),
        CASE WHEN n % 20 = 0 THEN 0 ELSE 1 END,
        CAST((n * 13 + 77) % 50000 / 1000.0 AS DECIMAL(8,3)),
        DATEADD(DAY, -(n % 1825), DATEADD(DAY, -1, GETUTCDATE()))
    FROM Nums;

    SET @inserted = @inserted + @@ROWCOUNT;
END;

PRINT '--- Products: ' + CAST(@inserted AS VARCHAR) + ' filas insertadas ---';
GO
