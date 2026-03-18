# Quick Test Script - Run this after restarting the server

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DONS Platform - Quick Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if server is running
Write-Host "Checking server..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 3
    Write-Host "✅ Server is running!" -ForegroundColor Green
    Write-Host "   Database: $($response.database)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Server is not running!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start the server first:" -ForegroundColor Yellow
    Write-Host "  cd backend" -ForegroundColor Cyan
    Write-Host "  uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "Running end-to-end tests..." -ForegroundColor Yellow
Write-Host ""

# Run the test script
python test_e2e_flow.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Done!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
