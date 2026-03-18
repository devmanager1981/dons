"""
Test script to check API endpoints and see detailed errors
"""
import requests
import json
import os

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_upload():
    """Test file upload"""
    print("\n=== Testing Upload Endpoint ===")
    try:
        # Use the demosample.tf file
        file_path = "../demosample.tf"
        if not os.path.exists(file_path):
            file_path = "demosample.tf"
        
        with open(file_path, 'rb') as f:
            files = {'file': ('demosample.tf', f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/api/upload", files=files)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            return response.json()['upload_id']
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_analyze(upload_id):
    """Test analyze endpoint"""
    print("\n=== Testing Analyze Endpoint ===")
    try:
        payload = {"upload_id": upload_id}
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            print(f"Error Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Starting API Tests...")
    
    # Test health
    if not test_health():
        print("\n❌ Health check failed!")
        return
    
    print("\n✅ Health check passed!")
    
    # Test upload
    upload_id = test_upload()
    if not upload_id:
        print("\n❌ Upload failed!")
        return
    
    print(f"\n✅ Upload passed! Upload ID: {upload_id}")
    
    # Test analyze
    if not test_analyze(upload_id):
        print("\n❌ Analyze failed!")
        return
    
    print("\n✅ Analyze passed!")
    print("\n🎉 All tests passed!")

if __name__ == "__main__":
    main()
