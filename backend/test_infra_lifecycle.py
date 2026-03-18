"""
Test Infrastructure Lifecycle - Deploy and Destroy

This script tests the full lifecycle of infrastructure deployment and destruction
using the DigitalOcean API directly with the resources from Samplecreatetf.tf
"""

import os
import sys
import time
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the deployer module
import do_deployer


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


async def test_deployment():
    """Test deploying infrastructure"""
    print_section("🚀 TESTING INFRASTRUCTURE DEPLOYMENT")
    
    # Define resources from Samplecreatetf.tf
    resources = [
        {
            "name": "web_server",
            "type": "digitalocean_droplet",
            "config": {
                "name": "web-server-test",
                "size": "s-1vcpu-1gb",
                "image": "ubuntu-22-04-x64",
                "region": "nyc1",
                "tags": ["dons-test", "web-server"]
            }
        },
        {
            "name": "app_db",
            "type": "digitalocean_database_cluster",
            "config": {
                "name": "app-db-test",
                "engine": "mysql",
                "version": "8",
                "size": "db-s-1vcpu-1gb",
                "region": "nyc1",
                "node_count": 1,
                "storage_size_mib": 20480
            }
        },
        {
            "name": "app_assets",
            "type": "digitalocean_spaces_bucket",
            "config": {
                "name": "dons-test-assets",
                "region": "nyc3",
                "acl": "private"
            }
        },
        {
            "name": "app_lb",
            "type": "digitalocean_loadbalancer",
            "config": {
                "name": "app-lb-test",
                "region": "nyc1",
                "forwarding_rules": [
                    {
                        "entry_protocol": "http",
                        "entry_port": 80,
                        "target_protocol": "http",
                        "target_port": 80
                    }
                ],
                "droplet_ids": []
            }
        }
    ]
    
    print(f"\n📦 Resources to deploy: {len(resources)}")
    for resource in resources:
        print(f"  - {resource['type']}: {resource['name']}")
    
    print("\n⏳ Starting deployment...")
    print("⚠️  Note: This will create REAL resources in your DigitalOcean account!")
    print("⚠️  Make sure you have sufficient quota and billing enabled.")
    
    # Confirm before proceeding
    response = input("\n❓ Proceed with deployment? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Deployment cancelled by user")
        return None
    
    try:
        # Deploy infrastructure
        result = await do_deployer.deploy_infrastructure(resources)
        
        print_section("📊 DEPLOYMENT RESULTS")
        print(f"\n✅ Status: {result['status']}")
        print(f"📈 Total Resources: {result['total_resources']}")
        print(f"✅ Deployed: {result['deployed_count']}")
        print(f"❌ Failed: {result['failed_count']}")
        
        if result['deployed_resources']:
            print("\n✅ Successfully Deployed Resources:")
            for resource in result['deployed_resources']:
                print(f"  - {resource['type']}: {resource['name']}")
                print(f"    ID: {resource['id']}")
                print(f"    Status: {resource['status']}")
        
        if result['failed_resources']:
            print("\n❌ Failed Resources:")
            for resource in result['failed_resources']:
                print(f"  - {resource['type']}: {resource['name']}")
                print(f"    Error: {resource['error']}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Deployment failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_destroy(deployment_result):
    """Test destroying deployed infrastructure"""
    if not deployment_result:
        print("\n⚠️  No deployment result available, skipping destroy test")
        return
    
    if not deployment_result.get('deployed_resources'):
        print("\n⚠️  No resources were deployed, skipping destroy test")
        return
    
    print_section("🗑️  TESTING INFRASTRUCTURE DESTRUCTION")
    
    deployed_resources = deployment_result['deployed_resources']
    print(f"\n📦 Resources to destroy: {len(deployed_resources)}")
    for resource in deployed_resources:
        print(f"  - {resource['type']}: {resource['name']} (ID: {resource['id']})")
    
    print("\n⚠️  WARNING: This will DELETE all deployed resources!")
    response = input("\n❓ Proceed with destruction? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Destruction cancelled by user")
        print("\n⚠️  Resources are still running in your DigitalOcean account!")
        print("⚠️  Please delete them manually to avoid charges.")
        return
    
    try:
        print("\n⏳ Starting destruction...")
        
        # Destroy infrastructure
        result = await do_deployer.rollback_deployment(deployed_resources)
        
        print_section("📊 DESTRUCTION RESULTS")
        print(f"\n✅ Status: {result['status']}")
        print(f"✅ Deleted: {len(result['deleted_resources'])}")
        print(f"❌ Failed: {len(result['failed_deletions'])}")
        
        if result['deleted_resources']:
            print("\n✅ Successfully Deleted Resources:")
            for resource_name in result['deleted_resources']:
                print(f"  - {resource_name}")
        
        if result['failed_deletions']:
            print("\n❌ Failed Deletions:")
            for resource_name in result['failed_deletions']:
                print(f"  - {resource_name}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Destruction failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main test function"""
    print_section("🧪 DONS INFRASTRUCTURE LIFECYCLE TEST")
    print("\nThis script will:")
    print("  1. Deploy infrastructure to DigitalOcean")
    print("  2. Wait for resources to become active")
    print("  3. Destroy all deployed infrastructure")
    print("\n⚠️  This creates REAL resources that may incur charges!")
    
    # Check environment variables
    print_section("🔍 CHECKING ENVIRONMENT")
    
    required_vars = [
        "DIGITALOCEAN_API_TOKEN",
        "DO_SPACES_REGION",
        "SPACES_ACCESS_KEY_ID",
        "SPACES_ACCESS_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 10}{value[-4:]}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file")
        sys.exit(1)
    
    # Test deployment
    deployment_result = await test_deployment()
    
    if not deployment_result:
        print("\n❌ Deployment test failed, exiting")
        sys.exit(1)
    
    # Wait a bit before destroying
    if deployment_result.get('deployed_resources'):
        print("\n⏳ Waiting 10 seconds before destruction test...")
        await asyncio.sleep(10)
        
        # Test destruction
        destroy_result = await test_destroy(deployment_result)
        
        if destroy_result:
            print_section("✅ TEST COMPLETE")
            print("\n✅ Infrastructure lifecycle test completed successfully!")
            print(f"   - Deployed: {deployment_result['deployed_count']} resources")
            print(f"   - Destroyed: {len(destroy_result['deleted_resources'])} resources")
        else:
            print_section("⚠️  TEST INCOMPLETE")
            print("\n⚠️  Deployment succeeded but destruction failed or was cancelled")
            print("⚠️  Please check your DigitalOcean account and delete resources manually!")
    else:
        print_section("⚠️  TEST INCOMPLETE")
        print("\n⚠️  No resources were deployed successfully")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        print("⚠️  Please check your DigitalOcean account for any deployed resources!")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
