# DONS Platform - Testing Instructions

## Quick Start

### Step 1: Clear Python Cache
```powershell
cd backend
Remove-Item -Path __pycache__ -Recurse -Force
```

### Step 2: Restart the Server
1. If the server is running, press `Ctrl+C` to stop it
2. Start it fresh:
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
3. Wait for the message: `Application startup complete.`

### Step 3: Run End-to-End Tests
In a NEW terminal window:
```powershell
cd backend
python test_e2e_flow.py
```

## What the Tests Do

The test script will:
1. ✅ Check server health
2. ✅ Upload `demosample.tf`
3. ✅ Analyze the infrastructure
4. ✅ Generate migration plan (escape plan)
5. ✅ Calculate cost comparison
6. ✅ Generate Terraform code
7. ✅ Generate ROI report

## Expected Output

You should see:
- Green ✅ for passing tests
- Yellow ⚠️ for tests that need AI credentials
- Red ❌ for failing tests

## Common Issues

### Issue: "dict object has no attribute 'resource_type'"
**Solution**: Clear Python cache and restart server (Steps 1-2 above)

### Issue: "DOResource object has no attribute 'name'"
**Solution**: Clear Python cache and restart server (Steps 1-2 above)

### Issue: "Server not responding"
**Solution**: Make sure server is running on port 8000

### Issue: "Parse errors with demosample.tf"
**Solution**: This was fixed - the parser now handles Windows line endings

## Debugging

To see detailed debug output, check the server terminal. You should see:
- `[DEBUG]` messages showing the flow
- `[ERROR]` messages if something fails

## Files Modified

The following fixes were applied:
1. ✅ `terraform_parser.py` - Normalize Windows line endings
2. ✅ `main.py` - Fixed data type conversions
3. ✅ `schemas.py` - Added `TerraformGenerationRequest` schema
4. ✅ `test_e2e_flow.py` - Fixed endpoint paths and parameters
5. ✅ Python cache cleared

## Next Steps

After all tests pass:
1. Test the frontend at http://localhost:3001
2. Upload a file through the UI
3. Click through the workflow
4. Verify all features work end-to-end
