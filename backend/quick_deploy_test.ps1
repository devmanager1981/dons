#!/usr/bin/env pwsh
# Quick Deployment Test - Safe validation only

Write-Host ""
Write-Host "🧪 DONS Quick Deployment Test" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script runs SAFE tests only (no resources created)" -ForegroundColor Green
Write-Host ""

# Check if .env exists
if (-not (Test-Path "../.env")) {
    Write-Host "❌ Error: .env file not found" -ForegroundColor Red
    Write-Host "   Please create .env file in the root directory" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Found .env file" -ForegroundColor Green
Write-Host ""

# Run validation tests
Write-Host "Running validation tests..." -ForegroundColor Cyan
Write-Host ""

python -c @"
import os
from dotenv import load_dotenv
load_dotenv('../.env')

print('🔍 Checking Environment Variables:')
print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

vars_to_check = {
    'DIGITALOCEAN_API_TOKEN': 'DigitalOcean API Token',
    'SPACES_ACCESS_KEY_ID': 'Spaces Access Key ID',
    'SPACES_ACCESS_KEY': 'Spaces Secret Key',
    'DO_SPACES_REGION': 'Spaces Region',
    'DO_SPACES_BUCKET': 'Spaces Bucket'
}

all_set = True
for var, desc in vars_to_check.items():
    value = os.getenv(var)
    if value:
        if 'TOKEN' in var or 'KEY' in var:
            print(f'✅ {desc}: Set (ends with ...{value[-4:]})')
        else:
            print(f'✅ {desc}: {value}')
    else:
        print(f'❌ {desc}: NOT SET')
        all_set = False

print()
if all_set:
    print('✅ All environment variables are set!')
else:
    print('❌ Some environment variables are missing')
    print('   Please check your .env file')
"@

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Run 'python test_deploy_api.py' for interactive testing" -ForegroundColor White
Write-Host "  2. Run 'python test_infra_lifecycle.py' to test full deployment" -ForegroundColor White
Write-Host "  3. Use the web UI at http://localhost:3001 for end-to-end testing" -ForegroundColor White
Write-Host ""
