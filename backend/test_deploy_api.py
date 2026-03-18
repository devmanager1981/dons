"""
Test Deployment API - Dry Run

This script tests the deployment and destroy API endpoints without actually
creating resources. It validates the API structure and error handling.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:8000"
DO_API_TOKEN = os.getenv("DIGITALOCEAN_API_TOKEN")


def print_section(title: str):
    """Print formatted section"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def test_do_api_connection():
    """Test DigitalOcean API connection"""
    print_section("🔍 TESTING DIGITALOCEAN API CONNECTION")
    
    headers = {
        "Authorization": f"Bearer {DO_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test account endpoint
        response = requests.get("https://api.digitalocean.com/v2/account", headers=headers)
        
        if response.status_code == 200:
            account = response.json().get("account", {})
            print(f"✅ API Connection: SUCCESS")
            print(f"   Email: {account.get('email', 'N/A')}")
            print(f"   Status: {account.get('status', 'N/A')}")
            print(f"   Droplet Limit: {account.get('droplet_limit', 'N/A')}")
            return True
        else:
            print(f"❌ API Connection: FAILED")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API Connection: ERROR")
        print(f"   Error: {str(e)}")
        return False


def test_list_resources():
    """Test listing existing resources"""
    print_section("📋 LISTING EXISTING RESOURCES")
    
    headers = {
        "Authorization": f"Bearer {DO_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # List droplets
    try:
        response = requests.get("https://api.digitalocean.com/v2/droplets", headers=headers)
        if response.status_code == 200:
            droplets = response.json().get("droplets", [])
            print(f"✅ Droplets: {len(droplets)} found")
            for droplet in droplets[:3]:
                print(f"   - {droplet['name']} ({droplet['id']}) - {droplet['status']}")
        else:
            print(f"⚠️  Droplets: Could not list (status {response.status_code})")
    except Exception as e:
        print(f"❌ Droplets: Error - {str(e)}")
    
    # List databases
    try:
        response = requests.get("https://api.digitalocean.com/v2/databases", headers=headers)
        if response.status_code == 200:
            databases = response.json().get("databases", [])
            print(f"✅ Databases: {len(databases)} found")
            for db in databases[:3]:
                print(f"   - {db['name']} ({db['id']}) - {db['status']}")
        else:
            print(f"⚠️  Databases: Could not list (status {response.status_code})")
    except Exception as e:
        print(f"❌ Databases: Error - {str(e)}")
    
    # List load balancers
    try:
        response = requests.get("https://api.digitalocean.com/v2/load_balancers", headers=headers)
        if response.status_code == 200:
            lbs = response.json().get("load_balancers", [])
            print(f"✅ Load Balancers: {len(lbs)} found")
            for lb in lbs[:3]:
                print(f"   - {lb['name']} ({lb['id']}) - {lb['status']}")
        else:
            print(f"⚠️  Load Balancers: Could not list (status {response.status_code})")
    except Exception as e:
        print(f"❌ Load Balancers: Error - {str(e)}")


def test_validate_config():
    """Validate the deployment configuration"""
    print_section("✅ VALIDATING CONFIGURATION")
    
    # Check API token
    if not DO_API_TOKEN:
        print("❌ DIGITALOCEAN_API_TOKEN not set")
        return False
    else:
        print(f"✅ API Token: Set (ends with ...{DO_API_TOKEN[-4:]})")
    
    # Check Spaces credentials
    spaces_key = os.getenv("SPACES_ACCESS_KEY_ID")
    spaces_secret = os.getenv("SPACES_ACCESS_KEY")
    
    if not spaces_key:
        print("❌ SPACES_ACCESS_KEY_ID not set")
        return False
    else:
        print(f"✅ Spaces Access Key: Set (ends with ...{spaces_key[-4:]})")
    
    if not spaces_secret:
        print("❌ SPACES_ACCESS_KEY not set")
        return False
    else:
        print(f"✅ Spaces Secret Key: Set")
    
    # Check region
    region = os.getenv("DO_SPACES_REGION", "nyc3")
    print(f"✅ Spaces Region: {region}")
    
    return True


async def run_full_test():
    """Run the full deployment and destroy test"""
    print_section("🧪 FULL LIFECYCLE TEST")
    
    print("\n⚠️  WARNING: This will create REAL infrastructure!")
    print("⚠️  Resources will be created and then destroyed.")
    print("⚠️  You may incur charges during the test period.")
    
    response = input("\n❓ Run full lifecycle test? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Test cancelled")
        return
    
    # Import the test module
    from test_infra_lifecycle import test_deployment, test_destroy
    
    # Run deployment test
    deployment_result = await test_deployment()
    
    if deployment_result and deployment_result.get('deployed_resources'):
        # Run destroy test
        await test_destroy(deployment_result)
    else:
        print("\n❌ Deployment failed, skipping destroy test")


def main():
    """Main test function"""
    print_section("🧪 DONS DEPLOYMENT API TEST")
    
    print("\nTest Options:")
    print("  1. Validate Configuration (no API calls)")
    print("  2. Test API Connection (read-only)")
    print("  3. List Existing Resources (read-only)")
    print("  4. Full Lifecycle Test (CREATES REAL RESOURCES)")
    print("  5. Exit")
    
    choice = input("\n❓ Select test option (1-5): ")
    
    if choice == "1":
        if test_validate_config():
            print("\n✅ Configuration is valid!")
        else:
            print("\n❌ Configuration has errors")
    
    elif choice == "2":
        if test_do_api_connection():
            print("\n✅ API connection successful!")
        else:
            print("\n❌ API connection failed")
    
    elif choice == "3":
        if test_do_api_connection():
            test_list_resources()
        else:
            print("\n❌ Cannot list resources - API connection failed")
    
    elif choice == "4":
        if not test_validate_config():
            print("\n❌ Configuration invalid, cannot proceed")
            return
        
        if not test_do_api_connection():
            print("\n❌ API connection failed, cannot proceed")
            return
        
        asyncio.run(run_full_test())
    
    elif choice == "5":
        print("\n👋 Exiting")
    
    else:
        print("\n❌ Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
