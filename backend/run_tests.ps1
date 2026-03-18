# DONS Platform - Test Runner Script
# This script helps restart the server and run end-to-end tests

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  DONS Platform - Test Runner" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Clear Python cache
Write-Host "[1/4] Clearing Python bytecode cache..." -ForegroundColor Yellow
if (Test-Path "__pycache__") {
    Remove-Item -Path "__pycache__" -Recurse -Force
    Write-Host "      Cache cleared!" -ForegroundColor Green
} else {
    Write-Host "      No cache found (already clean)" -ForegroundColor Green
}
Write-Host ""

# Step 2: Check if server is running
Write-Host "[2/4] Checking if server is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 2 -ErrorAction Stop
    Write-Host "      Server is running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "      IMPORTANT: Please restart the server manually:" -ForegroundColor Red
    Write-Host "      1. Press Ctrl+C in the server terminal" -ForegroundColor Red
    Write-Host "      2. Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Red
    Write-Host "      3. Wait for 'Application startup complete'" -ForegroundColor Red
    Write-Host "      4. Then run this script again" -ForegroundColor Red
    Write-Host ""
    exit 1
} catch {
    Write-Host "      Server is not running" -ForegroundColor Yellow
    Write-Host ""
}

# Step 3: Start server
Write-Host "[3/4] Starting server..." -ForegroundColor Yellow
Write-Host "      Please start the server manually in another terminal:" -ForegroundColor Cyan
Write-Host "      cd backend" -ForegroundColor Cyan
Write-Host "      uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "      Waiting for server to start..." -ForegroundColor Yellow

$maxAttempts = 30
$attempt = 0
$serverReady = $false

while ($attempt -lt $maxAttempts -and -not $serverReady) {
    $attempt++
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 2 -ErrorAction Stop
        $serverReady = $true
        Write-Host "      Server is ready!" -ForegroundColor Green
    } catch {
        Write-Host "      Attempt $attempt/$maxAttempts..." -ForegroundColor Gray
    }
}

if (-not $serverReady) {
    Write-Host "      Server did not start in time" -ForegroundColor Red
    Write-Host "      Please start it manually and run: python test_e2e_flow.py" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 4: Run tests
Write-Host "[4/4] Running end-to-end tests..." -ForegroundColor Yellow
Write-Host ""
python test_e2e_flow.py

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Test run complete!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
