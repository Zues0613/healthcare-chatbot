# PowerShell script to run SQL injection tests from any directory
# This avoids the 'cd api' error when already in api directory

Write-Host "Running SQL Injection Test Suite..." -ForegroundColor Cyan
Write-Host ""

# Check if we're in the api directory
if (Test-Path "test_sql_injection_comprehensive.py") {
    Write-Host "Already in api directory, running tests..." -ForegroundColor Green
    python test_sql_injection_comprehensive.py
} else {
    Write-Host "Changing to api directory..." -ForegroundColor Yellow
    if (Test-Path "api") {
        Set-Location api
        python test_sql_injection_comprehensive.py
    } else {
        Write-Host "Error: Cannot find api directory or test_sql_injection_comprehensive.py" -ForegroundColor Red
        exit 1
    }
}

