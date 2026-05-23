USE [Jarvis_dev];
GO

IF OBJECT_ID('[dbo].[Sales_Order]', 'U') IS NOT NULL
    DROP TABLE [dbo].[Sales_Order];
GO

IF OBJECT_ID('[dbo].[Product_Master]', 'U') IS NOT NULL
    DROP TABLE [dbo].[Product_Master];
GO

CREATE TABLE [dbo].[Product_Master] (
    [Product_ID] INT NOT NULL PRIMARY KEY,
    [Product_Name] NVARCHAR(100) NOT NULL,
    [Category] NVARCHAR(50) NOT NULL,
    [Unit_Price] DECIMAL(12, 2) NOT NULL,
    [Is_Active] BIT NOT NULL DEFAULT 1
);
GO

CREATE TABLE [dbo].[Sales_Order] (
    [Order_ID] INT NOT NULL PRIMARY KEY,
    [Customer_ID] INT NOT NULL,
    [Product_ID] INT NOT NULL,
    [Order_Date] DATE NOT NULL,
    [Quantity] INT NOT NULL,
    [Sales_Amount] DECIMAL(12, 2) NOT NULL,
    [Sales_Channel] NVARCHAR(50) NOT NULL,
    [Region] NVARCHAR(50) NOT NULL,
    CONSTRAINT [FK_Sales_Order_Product_Master]
        FOREIGN KEY ([Product_ID])
        REFERENCES [dbo].[Product_Master] ([Product_ID])
);
GO

INSERT INTO [dbo].[Product_Master]
    ([Product_ID], [Product_Name], [Category], [Unit_Price], [Is_Active])
VALUES
    (1, N'Laptop Pro 14', N'Electronics', 85000.00, 1),
    (2, N'Wireless Mouse', N'Accessories', 1500.00, 1),
    (3, N'Office Chair', N'Furniture', 12500.00, 1),
    (4, N'Noise Cancelling Headset', N'Accessories', 7800.00, 1),
    (5, N'Standing Desk', N'Furniture', 28000.00, 1);
GO

INSERT INTO [dbo].[Sales_Order]
    ([Order_ID], [Customer_ID], [Product_ID], [Order_Date], [Quantity], [Sales_Amount], [Sales_Channel], [Region])
VALUES
    (1001, 101, 1, '2026-01-05', 1, 85000.00, N'Online', N'West'),
    (1002, 102, 2, '2026-01-08', 2, 3000.00, N'Retail', N'South'),
    (1003, 103, 3, '2026-01-12', 1, 12500.00, N'Partner', N'West'),
    (1004, 104, 4, '2026-02-01', 1, 7800.00, N'Online', N'North'),
    (1005, 105, 5, '2026-02-14', 1, 28000.00, N'Retail', N'West'),
    (1006, 106, 2, '2026-03-03', 3, 4500.00, N'Online', N'South'),
    (1007, 107, 1, '2026-03-15', 1, 85000.00, N'Partner', N'North'),
    (1008, 108, 4, '2026-03-28', 2, 15600.00, N'Online', N'West');
GO

SELECT TOP 10 * FROM [dbo].[Product_Master];
SELECT TOP 10 * FROM [dbo].[Sales_Order];
GO
