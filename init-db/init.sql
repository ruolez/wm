-- Warehouse Management - Database Initialization Script
-- Creates DB_admin database with all required tables for initial setup

-- Create DB_admin database
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'DB_admin')
BEGIN
    CREATE DATABASE DB_admin;
END
GO

USE DB_admin;
GO

-- AdminUserProject_admin: Admin users table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[AdminUserProject_admin]') AND type = 'U')
BEGIN
    CREATE TABLE [dbo].[AdminUserProject_admin] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [username] NVARCHAR(255) NOT NULL,
        [full_name] NVARCHAR(255) NULL,
        [password] NVARCHAR(255) NOT NULL,
        [accessmenu] NVARCHAR(MAX) NULL,
        [accessdb] NVARCHAR(255) NULL,
        [dop1] NVARCHAR(255) NULL,
        [dop2] NVARCHAR(255) NULL,
        [dop3] NVARCHAR(255) NULL,
        [activated] BIT DEFAULT 1,
        [email] NVARCHAR(255) NULL,
        [statususer] NVARCHAR(255) NULL,
        [default_home_page] NVARCHAR(255) NULL
    );
END
GO

-- AdminDBs_admin: Database connections configuration
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[AdminDBs_admin]') AND type = 'U')
BEGIN
    CREATE TABLE [dbo].[AdminDBs_admin] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [TypeDB] NVARCHAR(255) NULL,
        [Username] NVARCHAR(255) NULL,
        [Password] NVARCHAR(255) NULL,
        [ipAddress] NVARCHAR(255) NULL,
        [ShareName] NVARCHAR(255) NULL DEFAULT '',
        [Port] INT NULL DEFAULT 1433,
        [NameDB] NVARCHAR(255) NULL,
        [Nick] NVARCHAR(255) NULL,
        [dop1] NVARCHAR(255) NULL,
        [dop2] NVARCHAR(255) NULL,
        [dop3] NVARCHAR(255) NULL,
        [dop4] NVARCHAR(255) NULL,
        [interval_1] NVARCHAR(255) NULL,
        [interval_2] NVARCHAR(255) NULL,
        [interval_3] NVARCHAR(255) NULL,
        [interval_4] NVARCHAR(255) NULL,
        [time_1] NVARCHAR(255) NULL,
        [time_2] NVARCHAR(255) NULL,
        [time_3] NVARCHAR(255) NULL,
        [time_4] NVARCHAR(255) NULL,
        [activated_shed] BIT DEFAULT 1,
        [activated_shed_1] BIT DEFAULT 1,
        [activated_dop] BIT DEFAULT 0,
        [activated_dop_1] BIT DEFAULT 0
    );
END
GO

-- admin_menu_list: Navigation menu items (auto-populated by app)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[admin_menu_list]') AND type = 'U')
BEGIN
    CREATE TABLE [dbo].[admin_menu_list] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [menu] NVARCHAR(255) NULL DEFAULT '',
        [status] NVARCHAR(255) NULL DEFAULT '',
        [description] NVARCHAR(255) NULL DEFAULT '',
        [flag] BIT DEFAULT 0
    );
END
GO

-- admin_menu: Menu configuration
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[admin_menu]') AND type = 'U')
BEGIN
    CREATE TABLE [dbo].[admin_menu] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [model] NVARCHAR(255) NULL DEFAULT '',
        [label] NVARCHAR(255) NULL DEFAULT '',
        [users] NVARCHAR(255) NULL DEFAULT '',
        [status] NVARCHAR(255) NULL DEFAULT '',
        [description] NVARCHAR(255) NULL DEFAULT '',
        [flag] BIT DEFAULT 0
    );
END
GO

-- UsersSessions: Session tracking
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[UsersSessions]') AND type = 'U')
BEGIN
    CREATE TABLE [dbo].[UsersSessions] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [session_id] NVARCHAR(255) NULL,
        [user_id] NVARCHAR(255) NULL,
        [user_name] NVARCHAR(255) NULL,
        [created_at] DATETIME NULL,
        [updated_at] DATETIME NULL,
        [expires_at] DATETIME NULL,
        [browser_info] NVARCHAR(MAX) NULL,
        [data] NVARCHAR(MAX) NULL,
        [Comment] NVARCHAR(255) NULL,
        [Notes] NVARCHAR(255) NULL,
        [Flag1] BIT DEFAULT 1,
        [Flag2] BIT NULL,
        [Flag3] BIT NULL,
        [Dop1] NVARCHAR(255) NULL,
        [Dop2] NVARCHAR(255) NULL,
        [Dop3] NVARCHAR(255) NULL
    );
END
GO

-- shed_admin: Scheduler configuration
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[shed_admin]') AND type = 'U')
BEGIN
    CREATE TABLE [dbo].[shed_admin] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [Description] NVARCHAR(255) NOT NULL,
        [Status] NVARCHAR(255) NOT NULL,
        [Number] INT NOT NULL DEFAULT 1433,
        [Name] NVARCHAR(255) NOT NULL,
        [Nick] NVARCHAR(255) NOT NULL,
        [dop1] NVARCHAR(255) NOT NULL,
        [dop2] NVARCHAR(255) NOT NULL,
        [dop3] NVARCHAR(255) NOT NULL,
        [dop4] NVARCHAR(255) NOT NULL,
        [interval_1] NVARCHAR(255) NOT NULL,
        [interval_2] NVARCHAR(255) NOT NULL,
        [interval_3] NVARCHAR(255) NOT NULL,
        [interval_4] NVARCHAR(255) NOT NULL,
        [time_1] NVARCHAR(255) NOT NULL,
        [time_2] NVARCHAR(255) NOT NULL,
        [time_3] NVARCHAR(255) NOT NULL,
        [time_4] NVARCHAR(255) NOT NULL,
        [activated_shed] BIT DEFAULT 1,
        [activated_shed_1] BIT DEFAULT 1,
        [activated_dop] BIT DEFAULT 0,
        [activated_dop_1] BIT DEFAULT 0
    );
END
GO

-- admin_query: Query aliases
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[admin_query]') AND type = 'U')
BEGIN
    CREATE TABLE [dbo].[admin_query] (
        [alias] NVARCHAR(255) PRIMARY KEY,
        [data] NVARCHAR(MAX) NULL
    );
END
GO

-- account_sync_settings: Account sync configuration
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[account_sync_settings]') AND type = 'U')
BEGIN
    CREATE TABLE [dbo].[account_sync_settings] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [db_name] NVARCHAR(50) NOT NULL,
        [source_user_id] INT NOT NULL,
        [target_user_id] INT NOT NULL,
        [target_username] NVARCHAR(255) NOT NULL,
        [sync_enabled] BIT NOT NULL DEFAULT 0,
        [created_at] DATETIME NOT NULL DEFAULT GETDATE(),
        [updated_at] DATETIME NOT NULL DEFAULT GETDATE()
    );
    CREATE UNIQUE INDEX ix_account_sync_source_target_db
    ON [dbo].[account_sync_settings] ([db_name], [source_user_id], [target_user_id]);
END
GO

-- QuotationsTemp: Temporary quotation storage
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[QuotationsTemp]') AND type = 'U')
BEGIN
    CREATE TABLE [dbo].[QuotationsTemp] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [SessionID] NVARCHAR(255) NULL,
        [SourceDB] NVARCHAR(255) NULL,
        [AccountNo] NVARCHAR(255) NULL,
        [BusinessName] NVARCHAR(255) NULL,
        [ProductDescription] NVARCHAR(255) NULL,
        [SKU] NVARCHAR(255) NULL,
        [QTY] INT NULL,
        [Price] INT NULL,
        [Total] INT NULL
    );
END
GO

-- AccountNo_crons_admin: Account cron jobs tracking
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[AccountNo_crons_admin]') AND type = 'U')
BEGIN
    CREATE TABLE [dbo].[AccountNo_crons_admin] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [DateCreated] DATETIME NOT NULL DEFAULT GETDATE(),
        [AccountNo] NVARCHAR(255) NOT NULL,
        [Description] NVARCHAR(255) NULL DEFAULT '',
        [status] NVARCHAR(255) NULL DEFAULT '',
        [cron1] BIT DEFAULT 0,
        [cron2] BIT DEFAULT 0,
        [cron3] BIT DEFAULT 0,
        [cron4] BIT DEFAULT 0
    );
END
GO

-- Article: Sample/test articles table (required by alembic)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Article]') AND type = 'U')
BEGIN
    CREATE TABLE [dbo].[Article] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [title] NVARCHAR(100) NOT NULL,
        [body] NVARCHAR(MAX) NOT NULL,
        [status] NVARCHAR(50) NULL
    );
END
GO

-- Insert default admin user (password: admin)
-- Password is plain text 'admin' - should be changed after first login
IF NOT EXISTS (SELECT * FROM [dbo].[AdminUserProject_admin] WHERE username = 'admin')
BEGIN
    INSERT INTO [dbo].[AdminUserProject_admin]
    (username, full_name, password, accessmenu, accessdb, activated, email, statususer, default_home_page)
    VALUES
    ('admin', 'Administrator', 'admin', '*', '*', 1, 'admin@localhost', 'Admin', NULL);
END
GO

PRINT 'DB_admin database initialized successfully!';
GO
