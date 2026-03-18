"""
Comprehensive connectivity test for DONS platform.
Tests DigitalOcean API, Gradient AI, and Spaces.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_do_api():
    """Test DigitalOcean API connectivity."""
    print("\n" + "="*60)
    print("TEST 1: DigitalOcean API")
    print("="*60)
    
    api_token = os.getenv("DIGITALOCEAN_API_TOKEN")
    
    if not api_token:
        print("❌ ERROR: DIGITALOCEAN_API_TOKEN not found")
        return False
    
    try:
        import requests
        
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Test account endpoint
        print("📡 Testing account endpoint...")
        response = requests.get(
            "https://api.digitalocean.com/v2/account",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            account = response.json().get("account", {})
            print(f"✅ SUCCESS: Connected to DigitalOcean API")
            print(f"   Email: {account.get('email')}")
            print(f"   Status: {account.get('status')}")
            return True
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_gradient_ai():
    """Test Gradient AI connectivity with new OpenAI SDK."""
    print("\n" + "="*60)
    print("TEST 2: Gradient AI")
    print("="*60)
    
    # Try both variable names
    api_key = os.getenv("GRADIENT_API_KEY") or os.getenv("GRADIENT_AI_MODEL_KEY")
    model = os.getenv("GRADIENT_MODEL") or os.getenv("GRADIENT_AI_MODELNAME", "openai-gpt-4o-mini")
    
    if not api_key:
        print("❌ ERROR: GRADIENT_API_KEY not found")
        return False
    
    try:
        from openai import OpenAI
        
        print(f"📡 Testing Gradient AI with model: {model}")
        
        # Create OpenAI client configured for Gradient AI
        client = OpenAI(
            api_key=api_key,
            base_url="https://inference.do-ai.run/v1/"
        )
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello from DONS!' in one sentence."}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        message = response.choices[0].message.content
        print(f"✅ SUCCESS: Gradient AI responded")
        print(f"   Response: {message}")
        print(f"   Model: {response.model}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print(f"   Make sure you have the correct GRADIENT_API_KEY")
        return False


def test_spaces():
    """Test DigitalOcean Spaces connectivity."""
    print("\n" + "="*60)
    print("TEST 3: DigitalOcean Spaces")
    print("="*60)
    
    # Try both variable names
    access_key = os.getenv("DO_SPACES_ACCESS_KEY") or os.getenv("SPACES_ACCESS_KEY_ID")
    secret_key = os.getenv("DO_SPACES_SECRET_KEY") or os.getenv("SPACES_ACCESS_KEY")
    region = os.getenv("DO_SPACES_REGION", "nyc3")
    bucket = os.getenv("DO_SPACES_BUCKET", "dons-uploads")
    
    if not all([access_key, secret_key]):
        print("❌ ERROR: Spaces credentials not found")
        print("   Need: DO_SPACES_ACCESS_KEY, DO_SPACES_SECRET_KEY")
        return False
    
    try:
        import boto3
        from botocore.client import Config
        
        print(f"📡 Testing Spaces in region: {region}")
        
        # Create S3 client for Spaces
        s3_client = boto3.client(
            's3',
            region_name=region,
            endpoint_url=f'https://{region}.digitaloceanspaces.com',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4')
        )
        
        # List buckets
        response = s3_client.list_buckets()
        buckets = response.get('Buckets', [])
        
        print(f"✅ SUCCESS: Connected to Spaces")
        print(f"   Found {len(buckets)} bucket(s):")
        for b in buckets:
            print(f"   - {b.get('Name')}")
            if b.get('Name') == bucket:
                print(f"     ✅ Found configured bucket: {bucket}")
        
        # Test if we can access the configured bucket
        try:
            s3_client.head_bucket(Bucket=bucket)
            print(f"✅ Bucket '{bucket}' is accessible")
        except:
            print(f"⚠️  Bucket '{bucket}' not found - will be created on first upload")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print(f"   Check your Spaces credentials and region")
        return False


def test_database():
    """Test PostgreSQL database connectivity."""
    print("\n" + "="*60)
    print("TEST 4: PostgreSQL Database")
    print("="*60)
    
    db_host = os.getenv("POSTGRES_DB_HOST", "localhost")
    db_port = os.getenv("POSTGRES_DB_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB_NAME", "dons")
    db_user = os.getenv("POSTGRES_DB_USER", "dons")
    db_pass = os.getenv("POSTGRES_DB_PASSWORD")
    
    if not db_pass:
        print("⚠️  WARNING: POSTGRES_DB_PASSWORD not set")
        print("   Skipping database test")
        return None
    
    try:
        import psycopg2
        
        print(f"📡 Testing connection to {db_host}:{db_port}/{db_name}")
        
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_pass,
            connect_timeout=5
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        print(f"✅ SUCCESS: Connected to PostgreSQL")
        print(f"   Version: {version.split(',')[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"⚠️  WARNING: Could not connect to database")
        print(f"   Error: {e}")
        print(f"   This is OK if database is not running yet")
        return None


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" "*20 + "DONS CONNECTIVITY TEST")
    print("="*70)
    
    # Run all tests
    results = {
        "DigitalOcean API": test_do_api(),
        "Gradient AI": test_gradient_ai(),
        "Spaces": test_spaces(),
        "Database": test_database(),
    }
    
    # Summary
    print("\n" + "="*70)
    print(" "*25 + "TEST SUMMARY")
    print("="*70)
    
    for service, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️  SKIP"
        print(f"{service:20} {status}")
    
    print("="*70)
    
    # Check critical services
    critical_pass = results["DigitalOcean API"] and results["Gradient AI"] and results["Spaces"]
    
    if critical_pass:
        print("\n🎉 All critical services are working!")
        print("✅ Ready to run DONS platform")
        sys.exit(0)
    else:
        print("\n⚠️  Some critical services failed")
        print("Please check your environment variables in .env file")
        sys.exit(1)
