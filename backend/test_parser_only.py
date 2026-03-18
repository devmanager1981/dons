"""
Quick test to verify the parser works correctly with demosample.tf
Run this to test just the parsing logic without the full API
"""
import terraform_parser
import os

def test_parser():
    print("="*60)
    print("  Testing Terraform Parser")
    print("="*60)
    print()
    
    # Read demosample.tf
    file_path = "../demosample.tf"
    if not os.path.exists(file_path):
        file_path = "demosample.tf"
    
    if not os.path.exists(file_path):
        print("❌ demosample.tf not found!")
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    print(f"✅ Read file: {len(content)} bytes")
    print()
    
    # Parse the file
    print("Parsing...")
    result = terraform_parser.parse_infrastructure_file(content, ".tf")
    
    print(f"✅ Parsed successfully!")
    print()
    print(f"Resources found: {len(result.resources)}")
    print(f"Errors: {len(result.errors)}")
    print()
    
    if result.errors:
        print("Parse Errors:")
        for error in result.errors:
            print(f"  ❌ {error}")
        print()
    
    if result.resources:
        print("Resources:")
        for r in result.resources:
            print(f"  ✅ {r.resource_type}.{r.resource_name}")
        print()
        
        # Test mapping
        print("Testing resource mapping...")
        import migration_mapper
        
        for r in result.resources[:3]:  # Test first 3
            try:
                do_resource = migration_mapper.map_aws_to_do(r)
                print(f"  ✅ {r.resource_type} → {do_resource.resource_type}")
            except Exception as e:
                print(f"  ❌ {r.resource_type} → Error: {e}")
        print()
    
    # Check for unsupported resources
    supported, unsupported = terraform_parser.filter_supported_resources(result.resources)
    print(f"Supported resources: {len(supported)}")
    print(f"Unsupported types: {len(unsupported)}")
    if unsupported:
        print("Unsupported types:")
        for u in unsupported:
            print(f"  ⚠️  {u}")
    print()
    
    print("="*60)
    if len(result.resources) == 7 and len(result.errors) == 0:
        print("🎉 Parser test PASSED!")
    else:
        print("⚠️  Parser test completed with issues")
    print("="*60)

if __name__ == "__main__":
    test_parser()
