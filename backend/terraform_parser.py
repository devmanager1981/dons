"""
Terraform and CloudFormation parser for DONS platform.
Extracts AWS resource definitions from infrastructure files.
"""
import json
import hcl2
import yaml
from typing import Dict, List, Any, Optional
from pydantic import BaseModel


class AWSResource(BaseModel):
    """AWS resource model."""
    resource_type: str  # e.g., "aws_instance"
    resource_name: str
    configuration: Dict[str, Any]
    dependencies: List[str] = []


class ParseResult(BaseModel):
    """Result of parsing infrastructure files."""
    resources: List[AWSResource]
    errors: List[str] = []
    file_type: str


def parse_terraform_file(file_content: str) -> ParseResult:
    """
    Parse .tf file and extract AWS resources.
    
    Args:
        file_content: Content of the Terraform file
        
    Returns:
        ParseResult with extracted resources and any errors
    """
    errors = []
    resources = []
    
    try:
        # Normalize line endings (Windows \r\n to Unix \n)
        file_content = file_content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Parse HCL2 format
        parsed = hcl2.loads(file_content)
        
        # Extract resources
        if 'resource' in parsed:
            for resource_block in parsed['resource']:
                for resource_type, resource_configs in resource_block.items():
                    # Only process AWS resources
                    if resource_type.startswith('aws_'):
                        for resource_name, config in resource_configs.items():
                            # Extract dependencies
                            dependencies = extract_dependencies(config)
                            
                            resources.append(AWSResource(
                                resource_type=resource_type,
                                resource_name=resource_name,
                                configuration=config,
                                dependencies=dependencies
                            ))
        
        return ParseResult(
            resources=resources,
            errors=errors,
            file_type="terraform"
        )
        
    except Exception as e:
        errors.append(f"Failed to parse Terraform file: {str(e)}")
        return ParseResult(
            resources=[],
            errors=errors,
            file_type="terraform"
        )


def parse_terraform_json(file_content: str) -> ParseResult:
    """
    Parse .tf.json file and extract AWS resources.
    
    Args:
        file_content: Content of the Terraform JSON file
        
    Returns:
        ParseResult with extracted resources and any errors
    """
    errors = []
    resources = []
    
    try:
        parsed = json.loads(file_content)
        
        # Extract resources from JSON format
        if 'resource' in parsed:
            for resource_type, resource_configs in parsed['resource'].items():
                # Only process AWS resources
                if resource_type.startswith('aws_'):
                    for resource_name, config in resource_configs.items():
                        # Extract dependencies
                        dependencies = extract_dependencies(config)
                        
                        resources.append(AWSResource(
                            resource_type=resource_type,
                            resource_name=resource_name,
                            configuration=config,
                            dependencies=dependencies
                        ))
        
        return ParseResult(
            resources=resources,
            errors=errors,
            file_type="terraform_json"
        )
        
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON at line {e.lineno}: {e.msg}")
        return ParseResult(
            resources=[],
            errors=errors,
            file_type="terraform_json"
        )
    except Exception as e:
        errors.append(f"Failed to parse Terraform JSON file: {str(e)}")
        return ParseResult(
            resources=[],
            errors=errors,
            file_type="terraform_json"
        )


def parse_terraform_state(file_content: str) -> ParseResult:
    """
    Parse .tfstate file and extract current resource state.
    
    Args:
        file_content: Content of the Terraform state file
        
    Returns:
        ParseResult with extracted resources and any errors
    """
    errors = []
    resources = []
    
    try:
        state = json.loads(file_content)
        
        # Extract resources from state file
        if 'resources' in state:
            for resource in state['resources']:
                resource_type = resource.get('type', '')
                resource_name = resource.get('name', '')
                
                # Only process AWS resources
                if resource_type.startswith('aws_'):
                    # Get instances (state file can have multiple instances)
                    instances = resource.get('instances', [])
                    for idx, instance in enumerate(instances):
                        attributes = instance.get('attributes', {})
                        
                        # Use index if multiple instances
                        name = f"{resource_name}_{idx}" if len(instances) > 1 else resource_name
                        
                        resources.append(AWSResource(
                            resource_type=resource_type,
                            resource_name=name,
                            configuration=attributes,
                            dependencies=resource.get('dependencies', [])
                        ))
        
        return ParseResult(
            resources=resources,
            errors=errors,
            file_type="terraform_state"
        )
        
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON at line {e.lineno}: {e.msg}")
        return ParseResult(
            resources=[],
            errors=errors,
            file_type="terraform_state"
        )
    except Exception as e:
        errors.append(f"Failed to parse Terraform state file: {str(e)}")
        return ParseResult(
            resources=[],
            errors=errors,
            file_type="terraform_state"
        )


def extract_dependencies(config: Dict[str, Any]) -> List[str]:
    """
    Extract resource dependencies from configuration.
    
    Args:
        config: Resource configuration dictionary
        
    Returns:
        List of dependency resource references
    """
    dependencies = []
    
    def find_references(obj, path=""):
        """Recursively find resource references in configuration."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                find_references(value, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for item in obj:
                find_references(item, path)
        elif isinstance(obj, str):
            # Look for Terraform references like ${aws_instance.web.id}
            if '${' in obj and '}' in obj:
                # Extract reference
                ref = obj[obj.index('${')+2:obj.index('}')]
                if '.' in ref:
                    dependencies.append(ref.split('.')[0] + '.' + ref.split('.')[1])
    
    find_references(config)
    return list(set(dependencies))  # Remove duplicates


def extract_aws_resources(parsed_data: Dict) -> List[AWSResource]:
    """
    Extract AWS resource definitions from parsed data.
    
    Args:
        parsed_data: Parsed infrastructure data
        
    Returns:
        List of AWSResource objects
    """
    resources = []
    
    # This is a helper function that can be used by other parsers
    # The main parsing logic is in the specific parser functions above
    
    return resources



def parse_cloudformation_yaml(file_content: str) -> ParseResult:
    """
    Parse CloudFormation YAML template and extract AWS resources.
    
    Args:
        file_content: Content of the CloudFormation YAML file
        
    Returns:
        ParseResult with extracted resources and any errors
    """
    errors = []
    resources = []
    
    try:
        template = yaml.safe_load(file_content)
        
        # Extract resources from CloudFormation template
        if 'Resources' in template:
            for resource_name, resource_def in template['Resources'].items():
                resource_type = resource_def.get('Type', '')
                
                # Convert CloudFormation type to Terraform-style
                # e.g., AWS::EC2::Instance -> aws_instance
                if resource_type.startswith('AWS::'):
                    # Convert AWS::EC2::Instance to aws_ec2_instance
                    parts = resource_type.split('::')
                    if len(parts) >= 3:
                        service = parts[1].lower()
                        resource = parts[2].lower()
                        tf_type = f"aws_{service}_{resource}"
                        
                        # Get properties
                        properties = resource_def.get('Properties', {})
                        
                        # Extract dependencies
                        depends_on = resource_def.get('DependsOn', [])
                        if isinstance(depends_on, str):
                            depends_on = [depends_on]
                        
                        resources.append(AWSResource(
                            resource_type=tf_type,
                            resource_name=resource_name,
                            configuration=properties,
                            dependencies=depends_on
                        ))
        
        return ParseResult(
            resources=resources,
            errors=errors,
            file_type="cloudformation_yaml"
        )
        
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML: {str(e)}")
        return ParseResult(
            resources=[],
            errors=errors,
            file_type="cloudformation_yaml"
        )
    except Exception as e:
        errors.append(f"Failed to parse CloudFormation YAML: {str(e)}")
        return ParseResult(
            resources=[],
            errors=errors,
            file_type="cloudformation_yaml"
        )


def parse_cloudformation_json(file_content: str) -> ParseResult:
    """
    Parse CloudFormation JSON template and extract AWS resources.
    
    Args:
        file_content: Content of the CloudFormation JSON file
        
    Returns:
        ParseResult with extracted resources and any errors
    """
    errors = []
    resources = []
    
    try:
        template = json.loads(file_content)
        
        # Extract resources from CloudFormation template
        if 'Resources' in template:
            for resource_name, resource_def in template['Resources'].items():
                resource_type = resource_def.get('Type', '')
                
                # Convert CloudFormation type to Terraform-style
                if resource_type.startswith('AWS::'):
                    parts = resource_type.split('::')
                    if len(parts) >= 3:
                        service = parts[1].lower()
                        resource = parts[2].lower()
                        tf_type = f"aws_{service}_{resource}"
                        
                        # Get properties
                        properties = resource_def.get('Properties', {})
                        
                        # Extract dependencies
                        depends_on = resource_def.get('DependsOn', [])
                        if isinstance(depends_on, str):
                            depends_on = [depends_on]
                        
                        resources.append(AWSResource(
                            resource_type=tf_type,
                            resource_name=resource_name,
                            configuration=properties,
                            dependencies=depends_on
                        ))
        
        return ParseResult(
            resources=resources,
            errors=errors,
            file_type="cloudformation_json"
        )
        
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON at line {e.lineno}: {e.msg}")
        return ParseResult(
            resources=[],
            errors=errors,
            file_type="cloudformation_json"
        )
    except Exception as e:
        errors.append(f"Failed to parse CloudFormation JSON: {str(e)}")
        return ParseResult(
            resources=[],
            errors=errors,
            file_type="cloudformation_json"
        )


def parse_infrastructure_file(file_content: str, file_extension: str) -> ParseResult:
    """
    Main entry point for parsing infrastructure files.
    Automatically detects file type and calls appropriate parser.
    
    Args:
        file_content: Content of the infrastructure file
        file_extension: File extension (.tf, .tf.json, .yaml, .yml, .json, .tfstate)
        
    Returns:
        ParseResult with extracted resources and any errors
    """
    file_extension = file_extension.lower()
    
    if file_extension == '.tf':
        return parse_terraform_file(file_content)
    elif file_extension == '.tf.json':
        return parse_terraform_json(file_content)
    elif file_extension == '.tfstate':
        return parse_terraform_state(file_content)
    elif file_extension in ['.yaml', '.yml']:
        # Try CloudFormation YAML
        return parse_cloudformation_yaml(file_content)
    elif file_extension == '.json':
        # Try to detect if it's CloudFormation or Terraform JSON
        try:
            data = json.loads(file_content)
            if 'AWSTemplateFormatVersion' in data or 'Resources' in data:
                return parse_cloudformation_json(file_content)
            else:
                return parse_terraform_json(file_content)
        except:
            return ParseResult(
                resources=[],
                errors=["Unable to determine file format"],
                file_type="unknown"
            )
    else:
        return ParseResult(
            resources=[],
            errors=[f"Unsupported file extension: {file_extension}"],
            file_type="unknown"
        )



def validate_file_extension(filename: str) -> tuple[bool, Optional[str]]:
    """
    Validate if file extension is supported.
    
    Args:
        filename: Name of the file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    supported_extensions = ['.tf', '.tf.json', '.yaml', '.yml', '.json', '.tfstate', '.zip']
    
    extension = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
    
    if extension not in supported_extensions:
        return False, f"Unsupported file type. Supported formats: {', '.join(supported_extensions)}"
    
    return True, None


def validate_file_size(file_size_bytes: int, max_size_mb: int = 50) -> tuple[bool, Optional[str]]:
    """
    Validate if file size is within limits.
    
    Args:
        file_size_bytes: Size of file in bytes
        max_size_mb: Maximum allowed size in MB
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size_bytes > max_size_bytes:
        return False, f"File size exceeds {max_size_mb}MB limit. Please upload a smaller file."
    
    return True, None


def get_supported_aws_resources() -> List[str]:
    """
    Get list of supported AWS resource types for migration.
    
    Returns:
        List of supported AWS resource types
    """
    return [
        'aws_instance',
        'aws_db_instance',
        'aws_s3_bucket',
        'aws_eks_cluster',
        'aws_lb',
        'aws_elb',
        'aws_alb'
    ]


def filter_supported_resources(resources: List[AWSResource]) -> tuple[List[AWSResource], List[str]]:
    """
    Filter resources to only include supported types.
    
    Args:
        resources: List of all parsed resources
        
    Returns:
        Tuple of (supported_resources, unsupported_resource_types)
    """
    supported_types = get_supported_aws_resources()
    supported = []
    unsupported = set()
    
    for resource in resources:
        if resource.resource_type in supported_types:
            supported.append(resource)
        else:
            unsupported.add(resource.resource_type)
    
    return supported, list(unsupported)
