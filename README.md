# Warehouse Management

## Table of Contents

1. [Introduction](#introduction)  
2. [Local Development Setup](#local-development-setup)  
    - [1. Set Up Microsoft SQL Server Using Docker](#1-set-up-microsoft-sql-server-using-docker)  
        - [1.1. Install SQL Server Management Studio (SSMS) (Optional)](#11-install-sql-server-management-studio-ssms-optional)  
    - [2. Restore the `DB_admin` Database Backup](#2-restore-the-db_admin-database-backup)  
    - [3. Create Additional Databases](#3-create-additional-databases)  
    - [4. Configure and Launch Docker Containers](#4-configure-and-launch-docker-containers)  
        - [4.1. Docker Compose Configuration](#41-docker-compose-configuration)  
        - [4.2. Docker Network Configuration](#42-docker-network-configuration)  
    - [5. Launch Application Services](#5-launch-application-services)  
    - [6. (Optional) Load User Data Backup](#6-optional-load-user-data-backup)  
3. [Production Environment Setup](#production-environment-setup)  
4. [Environment Variables](#environment-variables)  
5. [Troubleshooting](#troubleshooting)  

---

## Introduction

The **Warehouse Management** application is designed to facilitate efficient warehouse operations, including inventory management, order tracking, and reporting. This document provides detailed instructions for setting up the required environment and deploying the application using Docker. Instructions are divided into **Local Development Setup** and **Production Environment Setup**.

---

## Local Development Setup

### 1. Set Up Microsoft SQL Server Using Docker

#### 1.1. Create a Docker Network

```bash
docker network create warehouse-network
```

#### 1.2. Deploy Microsoft SQL Server Container

```bash
docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=YourStrongPassword123" \
   --name sqlserver \
   --network warehouse-network \
   -p 1433:1433 \
   -d mcr.microsoft.com/mssql/server:2022-latest
```

- **Parameters**:
  - `ACCEPT_EULA=Y`: Accepts the End User License Agreement.
  - `SA_PASSWORD`: Replace with a secure password.
  - `--name`: Container name `sqlserver`.
  - `--network`: Attaches the container to the `warehouse-network`.
  - `-p 1433:1433`: Maps container port 1433 to host port 1433.
  - `-d`: Detached mode.
  - `mcr.microsoft.com/mssql/server:2022-latest`: SQL Server image.

#### 1.3. Verify SQL Server Container Status

```bash
docker ps
```

#### 1.4. Install SQL Server Management Studio (Optional)

1. Download SSMS from [official website](https://docs.microsoft.com/en-us/sql/ssms/download-sql-server-management-studio-ssms).  
2. Install and connect to `localhost` using `SA` credentials.

---

### 2. Restore the `DB_admin` Database Backup

#### 2.1. Copy the Backup File to the Container

```bash
docker cp /path/to/backup/DB_admin.bak sqlserver:/var/opt/mssql/backup/
```

#### 2.2. Access the SQL Server Container

```bash
docker exec -it sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P "YourStrongPassword123"
```

#### 2.3. Restore the Database

```sql
RESTORE DATABASE DB_admin
FROM DISK = '/var/opt/mssql/backup/DB_admin.bak'
WITH MOVE 'DB_admin_Data' TO '/var/opt/mssql/data/DB_admin.mdf',
MOVE 'DB_admin_Log' TO '/var/opt/mssql/data/DB_admin.ldf';
GO
EXIT
```

---

### 3. Create Additional Databases

```sql
CREATE DATABASE PrimeWholesale;
GO
CREATE DATABASE Rand;
GO
CREATE DATABASE S2S;
GO
EXIT
```

---

### 4. Configure and Launch Docker Containers

#### 4.1. Verify Docker Network

```bash
docker network ls
```

If missing:

```bash
docker network create warehouse-network
```

---

### 5. Launch Application Services

```bash
docker build -f Dockerfile.base -t base .
docker-compose build
docker-compose up -d
```

#### 5.1. Access Services

- **API Admin Service** → [http://127.0.0.1:5000](http://127.0.0.1:5000)  
- **API Service** → [http://127.0.0.1:8000](http://127.0.0.1:8000)  

---

### 6. (Optional) Load User Data Backup

After DB setup, you can import **user data backup** from development or production environments:

```bash
docker cp /path/to/backup/UserData.bak sqlserver:/var/opt/mssql/backup/
```

Restore similarly to step [2.3](#23-restore-the-database).

---

## Production Environment Setup

**Note**: Do not manually deploy SQL Server in production. A database server is already provisioned.

### 1. Ensure Git Access via SSH

1. Verify you have an SSH key:  
   ```bash
   ls ~/.ssh/id_rsa.pub
   ```
2. If not, generate one:  
   ```bash
   ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
   ```
3. Add the SSH key to your Git repository provider.  

### 2. Pull Latest Changes

```bash
git pull origin main
```

### 3. Configure Environment Variables

Create `.env` with **production credentials** (different from local dev).

---

### 4. Configure and Launch Docker Containers

```bash
docker build -f Dockerfile.base -t base .
docker-compose build
docker-compose up -d
```

#### 4.1. Access Services

- **API Admin Service** → [http://127.0.0.1:5000](http://127.0.0.1:5000)  
- **API Service** → [http://127.0.0.1:8000](http://127.0.0.1:8000)  

---

## Environment Variables

Configure the `.env` file with the following values:

```env
DATABASE_URL1=mssql+pyodbc://<username>:<password>@<host>:<port>/<database>?driver=ODBC+Driver+17+for+SQL+Server
sr=127.0.0.1
pr=127.0.0.1
SECRET="SECRET"
SECRET1="SECRET1"
EXPIRED_DAYS=1
EXPIRED_MINUTES=1
X_TOKEN="X_TOKEN"
MODE=DEV
SMTP_USER="name@gmail.com"
SMTP_SENDER_EMAIL="name@gmail.com"
SMTP_PASSWORD="PASSWORD"
```

## Troubleshooting

If you encounter issues:

1. **Verify Docker Services**:
   ```bash
   docker ps
   ```
1.1 **In case of issues with Base image, run the following command**:
   # Failed to solve: base: failed to resolve source metadata for docker.io/library/base:latest: pull access denied, repository does not exist or may require authorization: server message: insufficient_scope: authorization failed.
   ```bash
   docker build -f Dockerfile.base -t base .
   ```
2. **Check SQL Server Logs**:
   ```bash
   docker logs sqlserver
   ```
3. **Ensure Correct Environment Variables**: Verify `.env` settings.
4. **Network Connectivity**:
   ```bash
   docker network inspect warehouse-network
   ```
5. **Recreate Containers**:
   ```bash
   docker-compose down
   docker-compose up --build -d
   ```
