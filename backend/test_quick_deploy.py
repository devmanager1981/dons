"""
Quick Deployment Test - Fast resources only

This script tests deployment with only fast-provisioning resources:
- Droplet (1-2 minutes)
- Spaces Bucket (instant)
- Load Balancer (1-2 minutes)

Skips database which takes 5-10 minutes.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

load_dotenv()
import do_deployer


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


async def test_quick_deployment():
    """Test deploying fast resources only"""
    print_section("🚀 QUICK DEPLOYMENT TEST (Fast Resources Only)")
    
    # Define only fast resources
    resources = [
        {
            "name": "web_server",
            "type": "digitalocean_droplet",
            "config": {
                "name": "dons-quick-test",
                "size": "s-1vcpu-1gb",
                "image": "ubuntu-22-04-x64",
                "region": "nyc1",
                "tags": ["dons-test", "quick-test"]
            }
        },
        {
            "name": "app_assets",
            "type": "digitalocean_spaces_bucket",
            "config": {
                "name": "dons-quick-test-bucket",
                "region": "nyc3",
                "acl": "private"
            }
        },
        {
            "name": "app_lb",
            "type": "digitalocean_loadbalancer",
            "config": {
                "name": "dons-quick-test-lb",
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
    
    print("\n⏱️  Estimated time: 2-3 minutes")
    print("⚠️  This will create REAL resources in your DigitalOcean account!")
    
    response = input("\n❓ Proceed with deployment? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Deployment cancelled")
        return None
    
    try:
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
        print(f"\n❌ Deployment failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_destroy(deployment_result):
    """Test destroying deployed infrastructure"""
    if not deployment_result or not deployment_result.get('deployed_resources'):
        print("\n⚠️  No resources to destroy")
        return
    
    print_section("🗑️  TESTING INFRASTRUCTURE DESTRUCTION")
    
    deployed_resources = deployment_result['deployed_resources']
    print(f"\n📦 Resources to destroy: {len(deployed_resources)}")
    for resource in deployed_resources:
        print(f"  - {resource['type']}: {resource['name']} (ID: {resource['id']})")
    
    response = input("\n❓ Proceed with destruction? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Destruction cancelled")
        print("\n⚠️  Resources are still running! Delete them manually to avoid charges.")
        return
    
    try:
        result = await do_deployer.rollback_deployment(deployed_resources)
        
        print_section("📊 DESTRUCTION RESULTS")
        print(f"\n✅ Status: {result['status']}")
        print(f"✅ Deleted: {len(result['deleted_resources'])}")
        print(f"❌ Failed: {len(result['failed_deletions'])}")
        
        if result['deleted_resources']:
            print("\n✅ Successfully Deleted:")
            for name in result['deleted_resources']:
                print(f"  - {name}")
        
        if result['failed_deletions']:
            print("\n❌ Failed Deletions:")
            for name in result['failed_deletions']:
                print(f"  - {name}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Destruction failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main test function"""
    print_section("🧪 DONS QUICK DEPLOYMENT TEST")
    print("\nThis test deploys only fast-provisioning resources:")
    print("  ✅ Droplet (1-2 min)")
    print("  ✅ Spaces Bucket (instant)")
    print("  ✅ Load Balancer (1-2 min)")
    print("\n⏱️  Total time: ~3 minutes")
    print("💰 Cost: ~$0.05 for test duration")
    
    # Check environment
    print_section("🔍 CHECKING ENVIRONMENT")
    
    required_vars = ["DIGITALOCEAN_API_TOKEN", "SPACES_ACCESS_KEY_ID", "SPACES_ACCESS_KEY"]
    missing = [v for v in required_vars if not os.getenv(v)]
    
    if missing:
        print(f"❌ Missing: {', '.join(missing)}")
        sys.exit(1)
    
    print("✅ All required environment variables set")
    
    # Deploy
    deployment_result = await test_quick_deployment()
    
    if not deployment_result:
        print("\n❌ Deployment failed")
        sys.exit(1)
    
    # Wait before destroying
    if deployment_result.get('deployed_resources'):
        print("\n⏳ Waiting 5 seconds before destruction...")
        await asyncio.sleep(5)
        
        # Destroy
        destroy_result = await test_destroy(deployment_result)
        
        if destroy_result:
            print_section("✅ TEST COMPLETE")
            print(f"\n✅ Deployed: {deployment_result['deployed_count']} resources")
            print(f"✅ Destroyed: {len(destroy_result['deleted_resources'])} resources")
        else:
            print_section("⚠️  CLEANUP NEEDED")
            print("\n⚠️  Please delete resources manually from DigitalOcean console!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        print("⚠️  Check DigitalOcean console for deployed resources!")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
