@echo off
REM Script to start the Multi-Agent Lead Processing System on Windows
setlocal enabledelayedexpansion

REM Navigate to script directory
cd /d "%~dp0"

REM Display banner
echo.
echo ======================================================
echo           MULTI-AGENT LEAD PROCESSING SYSTEM          
echo ======================================================
echo.

REM Check if .env file exists
if not exist .env (
    echo Error: .env file not found!
    echo Please create a .env file with the required credentials.
    exit /b 1
)

REM Default parameters
set DOCKER_MODE=false
set RESET_DB=false
set API_ONLY=false
set API_PORT=8000
set VOICE_BATCH=5
set ENTRY_BATCH=3

REM Parse command line arguments
:parse_args
if "%~1"=="" goto end_parse_args
if "%~1"=="--docker" (
    set DOCKER_MODE=true
    shift
    goto parse_args
)
if "%~1"=="--reset-db" (
    set RESET_DB=true
    shift
    goto parse_args
)
if "%~1"=="--api-only" (
    set API_ONLY=true
    shift
    goto parse_args
)
if "%~1"=="--api-port" (
    set API_PORT=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="--voice-batch" (
    set VOICE_BATCH=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="--entry-batch" (
    set ENTRY_BATCH=%~2
    shift
    shift
    goto parse_args
)
echo Unknown parameter: %~1
exit /b 1

:end_parse_args

REM Start the system
if "%DOCKER_MODE%"=="true" (
    echo Starting in Docker mode...
    
    REM Check if Docker is installed
    where docker >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo Error: Docker not found!
        echo Please install Docker to use this mode.
        exit /b 1
    )
    
    echo Building and starting containers...
    docker-compose up -d
    
    echo System started in Docker mode. API available at http://localhost:%API_PORT%
    echo Use 'docker-compose logs -f' to view logs.
) else (
    echo Starting in local mode...
    
    REM Check if Python is installed
    where python >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo Error: Python not found!
        echo Please install Python 3.9 or higher.
        exit /b 1
    )
    
    REM Check if virtualenv exists, if not create it
    if not exist venv (
        echo Creating virtual environment...
        python -m venv venv
    )
    
    REM Activate virtual environment
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    
    REM Install dependencies if not already installed
    if not exist venv\.deps_installed (
        echo Installing dependencies...
        pip install -r requirements.txt
        playwright install
        echo. > venv\.deps_installed
    )
    
    REM Build command with arguments
    set CMD=python run.py --api --api-port %API_PORT% --voice-batch %VOICE_BATCH% --entry-batch %ENTRY_BATCH%
    
    if "%RESET_DB%"=="true" (
        set CMD=!CMD! --reset-db
    )
    
    if "%API_ONLY%"=="true" (
        set CMD=!CMD! --api-only
    )
    
    echo Running command: !CMD!
    !CMD!
)

endlocal 