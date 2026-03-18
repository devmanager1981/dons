"""
End-to-end test of the complete migration workflow
"""
import requests
import json
import os
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_health():
    """Test health endpoint"""
    print_section("1. Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Status: {response.status_code}")
        data = response.json()
        print(f"   Database: {data.get('database', 'unknown')}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_upload():
    """Test file upload"""
    print_section("2. Upload Infrastructure File")
    try:
        file_path = "../demosample.tf"
        if not os.path.exists(file_path):
            file_path = "demosample.tf"
        
        with open(file_path, 'rb') as f:
            files = {'file': ('demosample.tf', f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/api/upload", files=files)
        
        print(f"✅ Status: {response.status_code}")
        data = response.json()
        upload_id = data['upload_id']
        print(f"   Upload ID: {upload_id}")
        print(f"   Filename: {data['filename']}")
        print(f"   Size: {data['file_size']} bytes")
        return upload_id
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_analyze(upload_id):
    """Test analyze endpoint"""
    print_section("3. Analyze Infrastructure")
    try:
        payload = {"upload_id": upload_id}
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"✅ Status: {response.status_code}")
        data = response.json()
        print(f"   Resources Detected: {data['resources_detected']}")
        print(f"   Parse Errors: {len(data['parse_errors'])}")
        print(f"   Unsupported Resources: {len(data['unsupported_resources'])}")
        
        if data['resources']:
            print(f"\n   Sample Resources:")
            for r in data['resources'][:3]:
                print(f"     - {r['type']}.{r['name']}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_escape_plan(upload_id):
    """Test migration plan generation"""
    print_section("4. Generate Migration Plan")
    try:
        payload = {
            "upload_id": upload_id,
            "include_ai_enablement": True
        }
        response = requests.post(
            f"{BASE_URL}/api/escape-plan",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60  # AI calls can take time
        )
        
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            plan_id = data['plan_id']
            print(f"   Plan ID: {plan_id}")
            print(f"   Deployment Steps: {len(data.get('deployment_steps', []))}")
            print(f"   Risks: {len(data.get('risks', []))}")
            print(f"   Total Resources: {data.get('total_resources', 0)}")
            return plan_id
        else:
            print(f"❌ Error Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_cost_calculation(upload_id):
    """Test cost calculation"""
    print_section("5. Calculate Costs")
    try:
        payload = {"upload_id": upload_id}
        response = requests.post(
            f"{BASE_URL}/api/cost",  # Changed from /api/costs
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   AWS Monthly: ${data['aws_monthly_cost']:.2f}")
            print(f"   DO Monthly: ${data['do_monthly_cost']:.2f}")
            print(f"   Monthly Savings: ${data['monthly_savings']:.2f}")
            print(f"   Savings %: {data['savings_percentage']:.1f}%")
            return True
        else:
            print(f"❌ Error Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_terraform_generation(plan_id):
    """Test Terraform generation"""
    print_section("6. Generate Terraform")
    try:
        payload = {"plan_id": plan_id}
        response = requests.post(
            f"{BASE_URL}/api/generate-terraform",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Validation: {data['validation_status']}")
            print(f"   Resource Count: {data['resource_count']}")
            print(f"   Terraform Size: {len(data['terraform_code'])} chars")
            return True
        else:
            print(f"❌ Error Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_roi_report(plan_id):
    """Test ROI report generation"""
    print_section("7. Generate ROI Report")
    try:
        response = requests.get(
            f"{BASE_URL}/api/roi-report?plan_id={plan_id}",
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Monthly Savings: ${data.get('monthly_savings', 0):.2f}")
            print(f"   Annual Savings: ${data.get('annual_savings', 0):.2f}")
            print(f"   Savings %: {data.get('savings_percentage', 0):.1f}%")
            return True
        else:
            print(f"❌ Error Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*60)
    print("  DONS Platform - End-to-End API Test")
    print("="*60)
    
    results = {
        "health": False,
        "upload": False,
        "analyze": False,
        "escape_plan": False,
        "costs": False,
        "terraform": False,
        "roi_report": False
    }
    
    # Test health
    if not test_health():
        print("\n❌ Health check failed! Is the server running?")
        return
    results["health"] = True
    
    # Test upload
    upload_id = test_upload()
    if not upload_id:
        print("\n❌ Upload failed!")
        return
    results["upload"] = True
    
    # Test analyze
    if not test_analyze(upload_id):
        print("\n❌ Analyze failed!")
        return
    results["analyze"] = True
    
    # Test escape plan (migration plan)
    plan_id = test_escape_plan(upload_id)
    if not plan_id:
        print("\n⚠️  Migration plan generation failed (may need AI credentials)")
        # Continue with other tests
    else:
        results["escape_plan"] = True
    
    # Test cost calculation
    if test_cost_calculation(upload_id):
        results["costs"] = True
    else:
        print("\n⚠️  Cost calculation failed")
    
    # Test Terraform generation
    if plan_id and test_terraform_generation(plan_id):
        results["terraform"] = True
    else:
        print("\n⚠️  Terraform generation failed or no plan_id available")
    
    # Test ROI report (only if we have a plan_id)
    if plan_id:
        if test_roi_report(plan_id):
            results["roi_report"] = True
        else:
            print("\n⚠️  ROI report failed")
    
    # Summary
    print_section("Test Summary")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {test}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    elif passed >= total - 2:
        print("\n⚠️  Most tests passed (some may require AI credentials)")
    else:
        print("\n❌ Multiple tests failed - check the logs above")

if __name__ == "__main__":
    main()
