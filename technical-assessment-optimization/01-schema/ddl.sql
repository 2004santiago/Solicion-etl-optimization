IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'ECommerceDB')
BEGIN
    CREATE DATABASE ECommerceDB;
END
GO

USE ECommerceDB;
GO

ALTER DATABASE ECommerceDB SET RECOVERY SIMPLE;
GO

IF OBJECT_ID('dbo.OrderHistory', 'U') IS NOT NULL DROP TABLE dbo.OrderHistory;
IF OBJECT_ID('dbo.OrderItems', 'U') IS NOT NULL DROP TABLE dbo.OrderItems;
IF OBJECT_ID('dbo.Inventory', 'U') IS NOT NULL DROP TABLE dbo.Inventory;
IF OBJECT_ID('dbo.Orders', 'U') IS NOT NULL DROP TABLE dbo.Orders;
IF OBJECT_ID('dbo.Products', 'U') IS NOT NULL DROP TABLE dbo.Products;
IF OBJECT_ID('dbo.Categories', 'U') IS NOT NULL DROP TABLE dbo.Categories;
IF OBJECT_ID('dbo.Customers', 'U') IS NOT NULL DROP TABLE dbo.Customers;
GO

CREATE TABLE dbo.Customers (
    CustomerID    INT IDENTITY(1,1) NOT NULL,
    Email         NVARCHAR(255) NOT NULL,
    FullName      NVARCHAR(200) NOT NULL,
    Country       CHAR(2) NOT NULL,
    Region        NVARCHAR(100) NULL,
    City          NVARCHAR(100) NULL,
    SignupDate    DATETIME2 NOT NULL,
    Status        TINYINT NOT NULL,
    CreditLimit   DECIMAL(12,2) NULL,
    LoyaltyTier   TINYINT NULL,
    CONSTRAINT PK_Customers PRIMARY KEY CLUSTERED (CustomerID)
);
GO

CREATE TABLE dbo.Categories (
    CategoryID    INT IDENTITY(1,1) NOT NULL,
    CategoryName  NVARCHAR(100) NOT NULL,
    IsActive      BIT NOT NULL DEFAULT 1,
    CONSTRAINT PK_Categories PRIMARY KEY CLUSTERED (CategoryID)
);
GO

CREATE TABLE dbo.Products (
    ProductID     INT IDENTITY(1,1) NOT NULL,
    SKU           VARCHAR(20) NOT NULL,
    ProductName   NVARCHAR(300) NOT NULL,
    CategoryID    INT NOT NULL,
    UnitPrice     DECIMAL(10,2) NOT NULL,
    CostPrice     DECIMAL(10,2) NOT NULL,
    IsActive      BIT NOT NULL DEFAULT 1,
    Weight        DECIMAL(8,3) NULL,
    CreatedDate   DATETIME2 NOT NULL,
    CONSTRAINT PK_Products PRIMARY KEY CLUSTERED (ProductID)
);
GO

CREATE TABLE dbo.Orders (
    OrderID       INT IDENTITY(1,1) NOT NULL,
    CustomerID    INT NOT NULL,
    OrderDate     DATETIME2 NOT NULL,
    Status        TINYINT NOT NULL,
    TotalAmount   DECIMAL(12,2) NOT NULL,
    ShippingCountry CHAR(2) NOT NULL,
    PaymentMethod TINYINT NOT NULL,
    WarehouseID   INT NOT NULL,
    CONSTRAINT PK_Orders PRIMARY KEY CLUSTERED (OrderID)
);
GO

CREATE TABLE dbo.OrderItems (
    OrderItemID   BIGINT IDENTITY(1,1) NOT NULL,
    OrderID       INT NOT NULL,
    ProductID     INT NOT NULL,
    Quantity      INT NOT NULL,
    UnitPrice     DECIMAL(10,2) NOT NULL,
    Discount      DECIMAL(5,2) NOT NULL DEFAULT 0,
    LineTotal     DECIMAL(12,2) NOT NULL,
    CONSTRAINT PK_OrderItems PRIMARY KEY CLUSTERED (OrderItemID)
);
GO

CREATE TABLE dbo.Inventory (
    InventoryID   BIGINT IDENTITY(1,1) NOT NULL,
    ProductID     INT NOT NULL,
    WarehouseID   INT NOT NULL,
    QuantityOnHand INT NOT NULL,
    ReorderLevel  INT NOT NULL,
    LastRestockDate DATETIME2 NULL,
    CONSTRAINT PK_Inventory PRIMARY KEY CLUSTERED (InventoryID)
);
GO

CREATE TABLE dbo.OrderHistory (
    HistoryID     BIGINT IDENTITY(1,1) NOT NULL,
    OrderID       INT NOT NULL,
    OldStatus     TINYINT NULL,
    NewStatus     TINYINT NOT NULL,
    ChangedBy     NVARCHAR(100) NOT NULL,
    ChangeDate    DATETIME2 NOT NULL,
    Notes         NVARCHAR(500) NULL,
    CONSTRAINT PK_OrderHistory PRIMARY KEY CLUSTERED (HistoryID)
);
GO
