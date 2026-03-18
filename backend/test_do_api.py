"""
Test script to verify DigitalOcean API connectivity.
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_do_api():
    """Test DigitalOcean API connectivity."""
    api_token = os.getenv("DIGITALOCEAN_API_TOKEN")
    
    if not api_token:
        print("❌ ERROR: DIGITALOCEAN_API_TOKEN not found in environment variables")
        return False
    
    print("🔍 Testing DigitalOcean API connectivity...")
    print(f"   Using token: {api_token[:20]}...")
    
    # Test 1: Get account information
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        print("\n📡 Test 1: Fetching account information...")
        response = requests.get(
            "https://api.digitalocean.com/v2/account",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            account = response.json().get("account", {})
            print(f"   ✅ SUCCESS: Connected to DigitalOcean API")
            print(f"   Account Email: {account.get('email')}")
            print(f"   Account Status: {account.get('status')}")
            print(f"   Droplet Limit: {account.get('droplet_limit')}")
        else:
            print(f"   ❌ FAILED: Status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ ERROR: {e}")
        return False
    
    # Test 2: List projects
    try:
        print("\n📡 Test 2: Fetching projects...")
        response = requests.get(
            "https://api.digitalocean.com/v2/projects",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            projects = response.json().get("projects", [])
            print(f"   ✅ SUCCESS: Found {len(projects)} project(s)")
            for project in projects:
                print(f"   - {project.get('name')} (ID: {project.get('id')})")
                if project.get('name') == os.getenv('DO_PROJECT_NAME', 'DONS'):
                    print(f"     ✅ Found DONS project!")
        else:
            print(f"   ⚠️  WARNING: Status {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ ERROR: {e}")
    
    # Test 3: List regions
    try:
        print("\n📡 Test 3: Fetching available regions...")
        response = requests.get(
            "https://api.digitalocean.com/v2/regions",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            regions = response.json().get("regions", [])
            available_regions = [r for r in regions if r.get('available')]
            print(f"   ✅ SUCCESS: Found {len(available_regions)} available region(s)")
            
            # Check for nyc1
            nyc1 = next((r for r in regions if r.get('slug') == 'nyc1'), None)
            if nyc1:
                print(f"   ✅ NYC1 region is available: {nyc1.get('available')}")
        else:
            print(f"   ⚠️  WARNING: Status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ ERROR: {e}")
    
    print("\n" + "="*60)
    print("✅ DigitalOcean API connectivity test completed successfully!")
    print("="*60)
    return True


def test_gradient_ai():
    """Test Gradient AI API connectivity."""
    api_key = os.getenv("GRADIENT_AI_MODEL_KEY")
    model_name = os.getenv("GRADIENT_AI_MODELNAME", "openai-gpt-4o-mini")
    
    if not api_key:
        print("\n⚠️  WARNING: GRADIENT_AI_MODEL_KEY not found in environment variables")
        print("   Skipping Gradient AI test")
        return False
    
    print("\n🔍 Testing Gradient AI connectivity...")
    print(f"   Using model: {model_name}")
    
    try:
        import openai
        
        # Configure OpenAI client for Gradient AI
        openai.api_key = api_key
        openai.api_base = "https://api.gradient.ai/v1"
        
        print("\n📡 Sending test request to Gradient AI...")
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[
                {"role": "user", "content": "Say 'Hello from DONS!' in one sentence."}
            ],
            max_tokens=50
        )
        
        message = response.choices[0].message.content
        print(f"   ✅ SUCCESS: Gradient AI responded")
        print(f"   Response: {message}")
        
        print("\n" + "="*60)
        print("✅ Gradient AI connectivity test completed successfully!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        print("\n" + "="*60)
        print("⚠️  Gradient AI test failed - check your API key")
        print("="*60)
        return False


def test_spaces():
    """Test DigitalOcean Spaces connectivity."""
    access_key = os.getenv("SPACES_ACCESS_KEY_ID")
    secret_key = os.getenv("SPACES_ACCESS_KEY")
    spaces_url = os.getenv("SPACES_ACCESS_URL")
    
    if not all([access_key, secret_key, spaces_url]):
        print("\n⚠️  WARNING: Spaces credentials not found in environment variables")
        print("   Skipping Spaces test")
        return False
    
    print("\n🔍 Testing DigitalOcean Spaces connectivity...")
    print(f"   Spaces URL: {spaces_url}")
    
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        # Extract region from URL (e.g., nyc3 from https://1donsspaces.nyc3.digitaloceanspaces.com)
        region = spaces_url.split('.')[1] if '.' in spaces_url else 'nyc3'
        
        # Create S3 client for Spaces
        s3_client = boto3.client(
            's3',
            region_name=region,
            endpoint_url=f'https://{region}.digitaloceanspaces.com',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        print("\n📡 Listing Spaces buckets...")
        response = s3_client.list_buckets()
        
        buckets = response.get('Buckets', [])
        print(f"   ✅ SUCCESS: Found {len(buckets)} bucket(s)")
        for bucket in buckets:
            print(f"   - {bucket.get('Name')}")
        
        print("\n" + "="*60)
        print("✅ Spaces connectivity test completed successfully!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        print("\n" + "="*60)
        print("⚠️  Spaces test failed - check your credentials")
        print("="*60)
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("DONS - DigitalOcean API Connectivity Test")
    print("="*60)
    
    # Run all tests
    do_success = test_do_api()
    gradient_success = test_gradient_ai()
    spaces_success = test_spaces()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"DigitalOcean API: {'✅ PASS' if do_success else '❌ FAIL'}")
    print(f"Gradient AI:      {'✅ PASS' if gradient_success else '⚠️  SKIP/FAIL'}")
    print(f"Spaces:           {'✅ PASS' if spaces_success else '⚠️  SKIP/FAIL'}")
    print("="*60)
    
    if do_success:
        print("\n🎉 Core connectivity verified! Ready to build DONS.")
    else:
        print("\n⚠️  Please check your DigitalOcean API token and try again.")
