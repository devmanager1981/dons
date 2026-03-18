#!/usr/bin/env pwsh
# Test Infrastructure Lifecycle Script

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "DONS Infrastructure Lifecycle Test" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will test deploying and destroying infrastructure" -ForegroundColor Yellow
Write-Host "using the DigitalOcean API." -ForegroundColor Yellow
Write-Host ""
Write-Host "WARNING: This creates REAL resources that may incur charges!" -ForegroundColor Red
Write-Host ""

# Run the test
python test_infra_lifecycle.py

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Test Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
