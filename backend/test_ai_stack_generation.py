"""
Test AI Stack Terraform Generation

Quick test to see what the AI stack Terraform looks like.
"""

from ai_stack_generator import generate_complete_ai_stack_terraform


def test_ai_stack_generation():
    """Test generating AI stack Terraform"""
    print("=" * 80)
    print("DONS AI Stack Terraform Generation Test")
    print("=" * 80)
    
    # Generate AI stack Terraform
    terraform_code = generate_complete_ai_stack_terraform(
        region="nyc1",
        github_repo="your-org/dons",
        github_branch="main"
    )
    
    print("\n✅ Generated AI Stack Terraform:")
    print(f"   Length: {len(terraform_code)} characters")
    print(f"   Lines: {len(terraform_code.split(chr(10)))} lines")
    
    # Count resources
    resource_count = terraform_code.count("resource \"")
    output_count = terraform_code.count("output \"")
    variable_count = terraform_code.count("variable \"")
    
    print(f"\n📊 Resource Counts:")
    print(f"   Resources: {resource_count}")
    print(f"   Outputs: {output_count}")
    print(f"   Variables: {variable_count}")
    
    # Show first 50 lines
    lines = terraform_code.split("\n")
    print(f"\n📄 First 50 lines:")
    print("-" * 80)
    for i, line in enumerate(lines[:50], 1):
        print(f"{i:3d} | {line}")
    print("-" * 80)
    
    # Save to file
    output_file = "ai_stack_sample.tf"
    with open(output_file, "w") as f:
        f.write(terraform_code)
    
    print(f"\n✅ Saved complete Terraform to: {output_file}")
    print(f"\n💡 To view the full file:")
    print(f"   cat {output_file}")
    print(f"\n💡 To deploy:")
    print(f"   terraform init")
    print(f"   terraform plan -var='enable_ai_stack=true'")
    print(f"   terraform apply -var='enable_ai_stack=true'")
    
    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    test_ai_stack_generation()
