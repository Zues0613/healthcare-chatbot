@echo off
REM Batch script to run SQL injection tests from any directory
REM This avoids the PowerShell 'cd api' error when already in api directory

echo Running SQL Injection Test Suite...
echo.

REM Check if we're in the api directory
if exist "test_sql_injection_comprehensive.py" (
    echo Already in api directory, running tests...
    python test_sql_injection_comprehensive.py
) else (
    echo Changing to api directory...
    cd api
    python test_sql_injection_comprehensive.py
)

pause

