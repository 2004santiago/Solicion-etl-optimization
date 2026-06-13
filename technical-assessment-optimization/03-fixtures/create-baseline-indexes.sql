USE ECommerceDB;
GO

SET NOCOUNT ON;

PRINT '--- Aplicando indices baseline (intencionalmente suboptimos) ---';

IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Orders_Status_WarehouseID' AND object_id = OBJECT_ID('dbo.Orders'))
    DROP INDEX IX_Orders_Status_WarehouseID ON dbo.Orders;
IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_OrderItems_OrderID' AND object_id = OBJECT_ID('dbo.OrderItems'))
    DROP INDEX IX_OrderItems_OrderID ON dbo.OrderItems;
IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Inventory_ProductID' AND object_id = OBJECT_ID('dbo.Inventory'))
    DROP INDEX IX_Inventory_ProductID ON dbo.Inventory;
GO

-- Indice en Orders: solo Status, sin incluir columnas utiles para queries de reportes
CREATE NONCLUSTERED INDEX IX_Orders_Status_WarehouseID
    ON dbo.Orders (Status, WarehouseID);
GO

-- Indice en OrderItems: solo OrderID, sin ProductID ni LineTotal
CREATE NONCLUSTERED INDEX IX_OrderItems_OrderID
    ON dbo.OrderItems (OrderID);
GO

-- Indice en Inventory: solo ProductID, sin WarehouseID
CREATE NONCLUSTERED INDEX IX_Inventory_ProductID
    ON dbo.Inventory (ProductID);
GO

PRINT '--- Intencionalmente NO se crean los siguientes indices: ---';
PRINT '---   Orders: sin indice en OrderDate, CustomerID, ShippingCountry ---';
PRINT '---   OrderItems: sin indice compuesto en (OrderID, ProductID), sin LineTotal INCLUDE ---';
PRINT '---   Inventory: sin indice compuesto en (ProductID, WarehouseID) ---';
PRINT '---   OrderHistory: sin indice en ChangeDate ---';
PRINT '---   Customers: sin indice en Country, Status, Email ---';
PRINT '---   Products: sin indice en CategoryID ---';

-- Actualizar estadisticas despues del poblado
UPDATE STATISTICS dbo.Customers;
UPDATE STATISTICS dbo.Products;
UPDATE STATISTICS dbo.Categories;
UPDATE STATISTICS dbo.Orders;
UPDATE STATISTICS dbo.OrderItems;
UPDATE STATISTICS dbo.Inventory;
UPDATE STATISTICS dbo.OrderHistory;
GO

PRINT '--- Indices baseline aplicados ---';
GO
