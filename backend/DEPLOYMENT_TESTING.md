# Deployment Testing Guide

This guide explains how to test the infrastructure deployment and destruction functionality.

## Overview

The DONS platform can deploy infrastructure to DigitalOcean using the API. This guide covers:
- Testing API connectivity
- Deploying test infrastructure
- Destroying deployed infrastructure
- Troubleshooting common issues

## Prerequisites

1. **DigitalOcean Account** with:
   - Valid API token
   - Sufficient quota for resources (droplets, databases, load balancers)
   - Billing enabled

2. **Environment Variables** in `.env`:
   ```
   DIGITALOCEAN_API_TOKEN=dop_v1_...
   SPACES_ACCESS_KEY_ID=DO00...
   SPACES_ACCESS_KEY=...
   DO_SPACES_REGION=nyc3
   DO_SPACES_BUCKET=1donsspaces
   ```

3. **Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Test Scripts

### 1. API Validation Test (Safe - No Resources Created)

```bash
python test_deploy_api.py
```

**Options:**
- Option 1: Validate Configuration - Checks environment variables
- Option 2: Test API Connection - Verifies DigitalOcean API access
- Option 3: List Existing Resources - Shows current resources in your account
- Option 4: Full Lifecycle Test - Creates and destroys real resources
- Option 5: Exit

**Recommended**: Start with options 1-3 to validate setup before creating resources.

### 2. Full Lifecycle Test (Creates Real Resources)

```bash
python test_infra_lifecycle.py
```

**What it does:**
1. Deploys 4 resources to DigitalOcean:
   - 1 Droplet (web server)
   - 1 MySQL Database
   - 1 Spaces Bucket
   - 1 Load Balancer

2. Waits for resources to become active

3. Destroys all deployed resources

**Cost Estimate**: ~$0.50-$1.00 for the test duration (typically 5-10 minutes)

**PowerShell shortcut:**
```powershell
.\test_lifecycle.ps1
```

## Test Resources

The test uses these resources from `Samplecreatetf.tf`:

| Resource Type | Name | Size | Region | Est. Cost |
|--------------|------|------|--------|-----------|
| Droplet | web-server-test | s-1vcpu-1gb | nyc1 | $6/month |
| Database | app-db-test | db-s-1vcpu-1gb | nyc1 | $15/month |
| Spaces Bucket | dons-test-assets | - | nyc3 | $5/month |
| Load Balancer | app-lb-test | - | nyc1 | $12/month |

**Total**: ~$38/month (prorated during test)

## Expected Output

### Successful Deployment
```
============================================================
🚀 TESTING INFRASTRUCTURE DEPLOYMENT
============================================================

📦 Resources to deploy: 4
  - digitalocean_droplet: web_server
  - digitalocean_database_cluster: app_db
  - digitalocean_spaces_bucket: app_assets
  - digitalocean_loadbalancer: app_lb

⏳ Starting deployment...

============================================================
📊 DEPLOYMENT RESULTS
============================================================

✅ Status: completed
📈 Total Resources: 4
✅ Deployed: 4
❌ Failed: 0

✅ Successfully Deployed Resources:
  - digitalocean_droplet: web_server
    ID: 123456789
    Status: active
  ...
```

### Successful Destruction
```
============================================================
🗑️  TESTING INFRASTRUCTURE DESTRUCTION
============================================================

📦 Resources to destroy: 4
  - digitalocean_droplet: web_server (ID: 123456789)
  ...

⏳ Starting destruction...

============================================================
📊 DESTRUCTION RESULTS
============================================================

✅ Status: completed
✅ Deleted: 4
❌ Failed: 0

✅ Successfully Deleted Resources:
  - web_server
  - app_db
  - app_assets
  - app_lb
```

## Troubleshooting

### Issue: "401 Unauthorized"
**Cause**: Invalid or expired API token  
**Fix**: Check `DIGITALOCEAN_API_TOKEN` in `.env`

### Issue: "429 Too Many Requests"
**Cause**: Rate limit exceeded  
**Fix**: Wait 60 seconds and try again

### Issue: "422 Unprocessable Entity"
**Cause**: Invalid resource configuration  
**Fix**: Check resource sizes and regions are valid

### Issue: Deployment timeout
**Cause**: Resources taking too long to provision  
**Fix**: This is normal for databases and Kubernetes clusters (can take 5-10 minutes)

### Issue: "Insufficient quota"
**Cause**: Account limits reached  
**Fix**: Delete existing resources or request quota increase

### Issue: Spaces bucket creation fails
**Cause**: Bucket name already exists globally  
**Fix**: Bucket names must be globally unique - the script uses `dons-test-assets`

## Manual Cleanup

If the test fails and resources are not destroyed automatically:

1. **List resources**:
   ```bash
   python test_deploy_api.py
   # Select option 3
   ```

2. **Delete via DigitalOcean Console**:
   - Go to https://cloud.digitalocean.com
   - Navigate to each resource type
   - Delete resources with "dons-test" or "test" in the name

3. **Delete via API** (if you have resource IDs):
   ```bash
   curl -X DELETE \
     -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
     https://api.digitalocean.com/v2/droplets/{droplet_id}
   ```

## Integration with Main Application

The test scripts use the same `do_deployer.py` module as the main application:

- `deploy_infrastructure()` - Deploys resources in dependency order
- `rollback_deployment()` - Destroys resources in reverse order
- `track_deployment_progress()` - Polls resource status until active

The main application endpoints (`/api/deploy`, `/api/destroy`) wrap these functions with:
- Database persistence
- Error handling
- Progress tracking
- API response formatting

## Safety Features

1. **Confirmation prompts** - User must type "yes" to proceed
2. **Dry-run option** - Test API without creating resources
3. **Automatic cleanup** - Destroy test runs after deployment
4. **Resource tagging** - Test resources tagged with "dons-test"
5. **Timeout protection** - Resources that fail to provision are not charged

## Next Steps

After successful testing:

1. Test the full web application flow:
   - Upload `Samplecreatetf.tf` via UI
   - Generate migration plan
   - Deploy infrastructure
   - Monitor deployment
   - Destroy infrastructure

2. Test with your actual AWS infrastructure files

3. Validate cost estimates match actual billing

## Support

For issues:
- Check backend logs: `python main.py` output
- Check DigitalOcean API status: https://status.digitalocean.com
- Review API documentation: https://docs.digitalocean.com/reference/api/
