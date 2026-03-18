"""
Direct test of the terraform parser to see what's failing
"""
import os
import sys

# Read the demosample.tf file
file_path = "../demosample.tf"
if not os.path.exists(file_path):
    file_path = "demosample.tf"

print("Reading file:", file_path)
with open(file_path, 'r') as f:
    content = f.read()

print("\n=== File Content ===")
print(content[:200] + "...")

# Test the parser
print("\n=== Testing Parser ===")
try:
    import terraform_parser
    
    file_ext = ".tf"
    print(f"Parsing with extension: {file_ext}")
    
    result = terraform_parser.parse_infrastructure_file(content, file_ext)
    
    print(f"\nParse Result:")
    print(f"  File Type: {result.file_type}")
    print(f"  Resources Found: {len(result.resources)}")
    print(f"  Errors: {len(result.errors)}")
    
    if result.errors:
        print("\n  Errors:")
        for error in result.errors:
            print(f"    - {error}")
    
    if result.resources:
        print("\n  Resources:")
        for r in result.resources[:3]:  # Show first 3
            print(f"    - {r.resource_type}.{r.resource_name}")
            print(f"      Config keys: {list(r.configuration.keys())}")
    
    # Test filter_supported_resources
    print("\n=== Testing Filter ===")
    supported, unsupported = terraform_parser.filter_supported_resources(result.resources)
    print(f"  Supported: {len(supported)}")
    print(f"  Unsupported types: {unsupported}")
    
    # Test conversion to dict
    print("\n=== Testing Dict Conversion ===")
    resources_dict = [
        {
            "name": r.resource_name,
            "type": r.resource_type,
            "config": r.configuration,
            "dependencies": r.dependencies
        }
        for r in result.resources
    ]
    print(f"  Converted {len(resources_dict)} resources to dict format")
    if resources_dict:
        print(f"  First resource: {resources_dict[0]['type']}.{resources_dict[0]['name']}")
    
    print("\n✅ Parser test passed!")
    
except Exception as e:
    print(f"\n❌ Parser test failed!")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
