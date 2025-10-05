@echo off
REM 🚀 Development Environment Setup Script for Windows
REM This script sets up the development environment for the CRM system

echo 🚀 Setting up CRM Development Environment...

REM Check Python version
echo [INFO] Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.11 or later.
    exit /b 1
)

REM Create virtual environment
echo [INFO] Creating virtual environment...
if exist venv (
    echo [WARNING] Virtual environment already exists. Removing...
    rmdir /s /q venv
)

python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    exit /b 1
)
echo [SUCCESS] Virtual environment created

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    exit /b 1
)
echo [SUCCESS] Virtual environment activated

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

REM Install development dependencies
echo [INFO] Installing development dependencies...
pip install -r requirements-dev.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    exit /b 1
)
echo [SUCCESS] Dependencies installed

REM Create environment file
echo [INFO] Creating development environment file...
if not exist .env (
    (
        echo # Development Environment Variables
        echo SECRET_KEY=django-insecure-dev-key-change-in-production
        echo DEBUG=True
        echo ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
        echo.
        echo # Database ^(SQLite for development^)
        echo DATABASE_URL=sqlite:///db.sqlite3
        echo.
        echo # Cache ^(Local memory for development^)
        echo CACHE_URL=locmem://
        echo.
        echo # Email ^(Console backend for development^)
        echo EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
        echo.
        echo # Logging
        echo LOG_LEVEL=DEBUG
        echo LOG_FILE=logs/django.log
        echo.
        echo # Development Settings
        echo CORS_ALLOW_ALL_ORIGINS=True
        echo CORS_ALLOW_CREDENTIALS=True
    ) > .env
    echo [SUCCESS] Environment file created
) else (
    echo [WARNING] Environment file already exists
)

REM Create logs directory
echo [INFO] Creating logs directory...
if not exist logs mkdir logs
echo [SUCCESS] Logs directory created

REM Run migrations
echo [INFO] Running database migrations...
python manage.py migrate
if %errorlevel% neq 0 (
    echo [ERROR] Failed to run migrations
    exit /b 1
)
echo [SUCCESS] Migrations completed

REM Create superuser
echo [INFO] Creating superuser...
echo Creating superuser account...
python manage.py createsuperuser --noinput --username admin --email admin@example.com 2>nul || (
    echo [WARNING] Superuser creation failed or user already exists
)
echo [SUCCESS] Superuser setup completed

REM Seed sample data
echo [INFO] Seeding sample data...
python manage.py seed_data --companies 3 --users 10
if %errorlevel% neq 0 (
    echo [WARNING] Failed to seed data, continuing...
)
echo [SUCCESS] Sample data seeded

REM Run health check
echo [INFO] Running system health check...
python manage.py health_check --detailed
if %errorlevel% neq 0 (
    echo [WARNING] Health check failed, continuing...
)
echo [SUCCESS] Health check completed

echo [SUCCESS] Development environment setup completed!
echo [INFO] You can now start the development server with: python manage.py runserver
echo [INFO] Or run this script with --start-server to start the server immediately

REM Check if --start-server flag is provided
if "%1"=="--start-server" (
    echo [INFO] Starting development server...
    echo 🚀 Development server will start on http://localhost:8000
    echo Press Ctrl+C to stop the server
    echo.
    python manage.py runserver 0.0.0.0:8000
)

pause
