# BI System Architecture Design

## 1. System Overview
This project is a Business Intelligence (BI) system based on **Python (Django)** and **MSSQL**. It provides data connection management, dataset definition, report visualization (PC/Mobile), and a comprehensive permission system.

## 2. Technical Stack
- **Backend Language**: Python 3.9+
- **Web Framework**: Django 4.2 + Django REST Framework (DRF)
- **Database**: Microsoft SQL Server (MSSQL)
- **ORM**: Django ORM (with `mssql-django`)
- **Asynchronous Tasks**: Celery + Redis (for query execution & scheduling)
- **Frontend**: Recommended React/Vue (SPA)

## 3. Directory Structure
```
BI_System/
├── manage.py                # Entry point
├── requirements.txt         # Dependencies
├── config/                  # Project Config
│   ├── settings.py          # Settings (DB, Apps, Middleware)
│   └── urls.py              # Main Routing
├── apps/                    # Core Modules
│   ├── system/              # Auth & Permissions (RBAC)
│   ├── datasource/          # Data Connection Management
│   ├── dataset/             # SQL Execution & Data Logic
│   ├── report/              # Report Templates & Mapping
│   └── scheduler/           # Task Scheduling (Optional)
├── logs/                    # Application Logs
└── frontend/                # Frontend Source Code (Placeholder)
```

## 4. Core Functionalities

### 4.1 Data Connection (DataSource)
- **Goal**: Define public database connections.
- **Features**: 
  - Support MSSQL (primary), MySQL, PostgreSQL, etc.
  - Connection pooling and connectivity testing.
  - Encrypted password storage.
- **Model**: `DataSource` (host, port, user, password, db_name).

### 4.2 Dataset Management (DataSet)
- **Goal**: Execute SQL via connections to read data.
- **Features**:
  - SQL Editor with parameter support (e.g., `SELECT * FROM table WHERE date > {start_date}`).
  - Data preview and metadata extraction (column types).
  - Caching results (Redis) for performance.
- **Model**: `DataSet` (sql_script, params_config, metadata).

### 4.3 Report Engine (Report)
- **Goal**: Display templates for PC and Mobile.
- **Features**:
  - **PC Template**: Grid layout, high density, complex charts.
  - **Mobile Template**: Vertical flow, responsive, simplified interactions.
  - **Visual Config**: Stored as JSON (`template_config`) allowing dynamic rendering by frontend.
- **Model**: `Report` (platform_type='pc'/'mobile', template_config).

### 4.4 Report Mapping (ReportMapping)
- **Goal**: Map report pages to backend execution functions.
- **Features**:
  - Allows overriding standard generic data fetching with custom Python logic.
  - Maps a report ID to a specific python path (e.g., `apps.custom.finance_handler`).
- **Model**: `ReportFunctionMapping` (report_id, function_path).

### 4.5 Permission System (System)
- **Goal**: RBAC + Data Scope + Directory Permissions.
- **Features**:
  - **Role Permission**: Users assigned to Roles.
  - **Directory Permission**: Roles assigned to Menus/Directories (`SysMenu`).
  - **Data Permission**: Row Level Security (RLS) defined by SQL filters in `SysDataPermission` (e.g., `dept_id = 101`).
  - **Loader**: Permissions are loaded directly from DB tables (`sys_menu`, `sys_role`) at runtime.

## 5. Industry Standard Supplements
To make this a complete enterprise BI solution, the following have been added to the architecture:
1.  **Task Scheduler**: For email delivery of reports and periodic cache warming (implemented in `apps/scheduler`).
2.  **Audit Logs**: Tracking who accessed which report and executed which SQL (middleware/decorators needed).
3.  **Export Engine**: Capability to export report results to Excel/PDF.
4.  **Dashboarding**: Ability to combine multiple reports/widgets into a single view.

## 6. Setup Instructions
1.  Install dependencies: `pip install -r requirements.txt`
2.  Configure DB in `config/settings.py` (Update MSSQL credentials).
3.  Run migrations: `python manage.py makemigrations` && `python manage.py migrate`
4.  Start server: `python manage.py runserver`
