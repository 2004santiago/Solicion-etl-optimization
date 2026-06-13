-- ============================================================================
-- PRUEBA TECNICA DATA ENGINEER - DDL TABLAS DESTINO
-- Motor: SQL Server
-- Esquema: etl
-- ============================================================================

-- Eliminar tablas si existen (para re-ejecucion)
IF OBJECT_ID('etl.Payments', 'U') IS NOT NULL DROP TABLE etl.Payments;
IF OBJECT_ID('etl.InvoiceLines', 'U') IS NOT NULL DROP TABLE etl.InvoiceLines;
IF OBJECT_ID('etl.Invoices', 'U') IS NOT NULL DROP TABLE etl.Invoices;
IF OBJECT_ID('etl.Products', 'U') IS NOT NULL DROP TABLE etl.Products;
IF OBJECT_ID('etl.Suppliers', 'U') IS NOT NULL DROP TABLE etl.Suppliers;
IF OBJECT_ID('etl.Customers', 'U') IS NOT NULL DROP TABLE etl.Customers;
IF SCHEMA_ID('etl') IS NULL EXEC('CREATE SCHEMA etl');
GO

-- ============================================================================
-- DIMENSION: Clientes
-- ============================================================================
CREATE TABLE etl.Customers (
    customer_id     INT IDENTITY(1,1) PRIMARY KEY,
    customer_code   VARCHAR(20)     NOT NULL,       -- ID original del sistema fuente
    first_name      VARCHAR(100)    NOT NULL,
    last_name       VARCHAR(100)    NOT NULL,
    full_name       VARCHAR(200)    NULL,           -- Nombre completo (para source_b)
    email           VARCHAR(255)    NOT NULL,
    phone           VARCHAR(30)     NULL,
    address         VARCHAR(300)    NULL,
    city            VARCHAR(100)    NULL,
    country         VARCHAR(100)    NULL,
    tax_id          VARCHAR(30)     NULL,
    registration_date DATE          NOT NULL,
    credit_limit    DECIMAL(18, 2)  NULL,
    is_active       BIT             NOT NULL DEFAULT 1,
    source_system   VARCHAR(20)     NOT NULL,       -- 'SOURCE_A' o 'SOURCE_B'
    source_id       VARCHAR(20)     NOT NULL,       -- ID en el sistema de origen
    created_at      DATETIME2       NOT NULL DEFAULT GETDATE(),
    updated_at      DATETIME2       NOT NULL DEFAULT GETDATE()
);
GO

-- ============================================================================
-- DIMENSION: Proveedores
-- ============================================================================
CREATE TABLE etl.Suppliers (
    supplier_id     INT IDENTITY(1,1) PRIMARY KEY,
    supplier_code   VARCHAR(20)     NOT NULL,
    company_name    VARCHAR(200)    NOT NULL,
    contact_name    VARCHAR(200)    NULL,
    email           VARCHAR(255)    NOT NULL,
    phone           VARCHAR(30)     NULL,
    address         VARCHAR(300)    NULL,
    city            VARCHAR(100)    NULL,
    country         VARCHAR(100)    NULL,
    tax_id          VARCHAR(30)     NULL,
    payment_terms   VARCHAR(50)     NULL,
    is_active       BIT             NOT NULL DEFAULT 1,
    source_system   VARCHAR(20)     NOT NULL,
    source_id       VARCHAR(20)     NOT NULL,
    created_at      DATETIME2       NOT NULL DEFAULT GETDATE(),
    updated_at      DATETIME2       NOT NULL DEFAULT GETDATE()
);
GO

-- ============================================================================
-- DIMENSION: Productos
-- ============================================================================
CREATE TABLE etl.Products (
    product_id      INT IDENTITY(1,1) PRIMARY KEY,
    product_code    VARCHAR(20)     NOT NULL,
    product_name    VARCHAR(200)    NOT NULL,
    category        VARCHAR(100)    NULL,
    unit_price      DECIMAL(18, 4)  NOT NULL,
    supplier_id     INT             NULL REFERENCES etl.Suppliers(supplier_id),
    supplier_code   VARCHAR(20)     NULL,           -- ID del proveedor en sistema fuente
    sku             VARCHAR(50)     NULL,
    description     VARCHAR(500)    NULL,
    uom             VARCHAR(20)     NULL DEFAULT 'UNIDAD',
    is_active       BIT             NOT NULL DEFAULT 1,
    created_date    DATE            NULL,
    source_system   VARCHAR(20)     NOT NULL,
    source_id       VARCHAR(20)     NOT NULL,
    created_at      DATETIME2       NOT NULL DEFAULT GETDATE(),
    updated_at      DATETIME2       NOT NULL DEFAULT GETDATE()
);
GO

-- ============================================================================
-- FACT: Cabeceras de Factura
-- ============================================================================
CREATE TABLE etl.Invoices (
    invoice_id      INT IDENTITY(1,1) PRIMARY KEY,
    invoice_number  VARCHAR(30)     NOT NULL,       -- Numero/ID de origen
    customer_id     INT             NULL REFERENCES etl.Customers(customer_id),
    customer_code   VARCHAR(20)     NULL,           -- ID del cliente en sistema fuente
    invoice_date    DATE            NOT NULL,
    due_date        DATE            NULL,
    subtotal        DECIMAL(18, 4)  NOT NULL DEFAULT 0,
    tax_amount      DECIMAL(18, 4)  NOT NULL DEFAULT 0,
    total_amount    DECIMAL(18, 4)  NOT NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'PENDING',
    payment_method  VARCHAR(50)     NULL,
    source_system   VARCHAR(20)     NOT NULL,
    source_id       VARCHAR(20)     NOT NULL,
    created_at      DATETIME2       NOT NULL DEFAULT GETDATE(),
    updated_at      DATETIME2       NOT NULL DEFAULT GETDATE()
);
GO

-- ============================================================================
-- FACT: Lineas de Factura
-- ============================================================================
CREATE TABLE etl.InvoiceLines (
    line_id         INT IDENTITY(1,1) PRIMARY KEY,
    invoice_id      INT             NOT NULL REFERENCES etl.Invoices(invoice_id),
    product_id      INT             NULL REFERENCES etl.Products(product_id),
    product_code    VARCHAR(20)     NULL,
    quantity        DECIMAL(18, 4)  NOT NULL,
    unit_price      DECIMAL(18, 4)  NOT NULL,
    discount_pct    DECIMAL(5, 2)   NULL DEFAULT 0,
    line_total      DECIMAL(18, 4)  NOT NULL,
    source_system   VARCHAR(20)     NOT NULL,
    source_id       VARCHAR(20)     NOT NULL,
    created_at      DATETIME2       NOT NULL DEFAULT GETDATE(),
    updated_at      DATETIME2       NOT NULL DEFAULT GETDATE()
);
GO

-- ============================================================================
-- FACT: Pagos
-- ============================================================================
CREATE TABLE etl.Payments (
    payment_id      INT IDENTITY(1,1) PRIMARY KEY,
    payment_number  VARCHAR(30)     NOT NULL,
    invoice_id      INT             NULL REFERENCES etl.Invoices(invoice_id),
    invoice_code    VARCHAR(30)     NULL,           -- ID factura en sistema fuente
    payment_date    DATE            NOT NULL,
    amount          DECIMAL(18, 4)  NOT NULL,
    payment_method  VARCHAR(50)     NULL,
    reference_number VARCHAR(100)   NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'COMPLETED',
    source_system   VARCHAR(20)     NOT NULL,
    source_id       VARCHAR(20)     NOT NULL,
    created_at      DATETIME2       NOT NULL DEFAULT GETDATE(),
    updated_at      DATETIME2       NOT NULL DEFAULT GETDATE()
);
GO
