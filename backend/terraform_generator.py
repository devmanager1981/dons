"""
Terraform Generator Module

Generates DigitalOcean Terraform configuration from mapped resources.
Includes provider configuration, resource blocks, variables, and outputs.
"""

from typing import List, Dict, Optional
import re


def generate_provider_block(do_token_var: str = "do_token") -> str:
    """
    Generate DigitalOcean provider configuration block
    
    Args:
        do_token_var: Variable name for DO API token
        
    Returns:
        Terraform provider block as string
    """
    return f'''terraform {{
  required_providers {{
    digitalocean = {{
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }}
  }}
}}

provider "digitalocean" {{
  token = var.{do_token_var}
}}
'''


def generate_variables(sensitive_vars: Optional[List[str]] = None) -> str:
    """
    Generate Terraform variables block
    
    Args:
        sensitive_vars: List of sensitive variable names
        
    Returns:
        Terraform variables block as string
    """
    if sensitive_vars is None:
        sensitive_vars = ["do_token"]
    
    variables = []
    for var in sensitive_vars:
        variables.append(f'''variable "{var}" {{
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}}
''')
    
    variables.append('''variable "project_suffix" {
  description = "Unique suffix for globally-unique resource names (e.g. Spaces buckets)"
  type        = string
  default     = "dons"
}
''')
    
    return "\n".join(variables)


def generate_droplet_block(resource: Dict) -> str:
    """Generate Terraform block for DigitalOcean Droplet"""
    name = resource.get("name", "droplet")
    config = resource.get("config", {})

    size = config.get("size", "s-2vcpu-4gb")
    image = config.get("image", "ubuntu-22-04-x64")
    region = config.get("region", "nyc1")
    tags = config.get("tags", [])

    # Add mapping note as comment
    mapping_note = config.get("mapping_note", "")
    comment = f"  # {mapping_note}\n" if mapping_note else ""

    # Ensure tags is a list of strings (not individual characters)
    if isinstance(tags, str):
        tags = [tags]
    elif isinstance(tags, list) and tags and len(tags) > 1 and all(len(t) == 1 for t in tags):
        # Looks like a string was split into characters — rejoin it
        tags = ["".join(tags)]

    if tags:
        tag_items = [f'"{tag}"' for tag in tags]
        tags_str = f'[{", ".join(tag_items)}]'
    else:
        tags_str = f'["{name}"]'

    return f'''{comment}resource "digitalocean_droplet" "{name}" {{
  name   = "{name}"
  size   = "{size}"
  image  = "{image}"
  region = "{region}"
  tags   = {tags_str}
}}
'''



def generate_database_block(resource: Dict) -> str:
    """Generate Terraform block for DigitalOcean Managed Database"""
    name = resource.get("name", "database")
    config = resource.get("config", {})
    
    engine = config.get("engine", "pg")
    version = config.get("version", "15")
    size = config.get("size", "db-s-1vcpu-2gb")
    region = config.get("region", "nyc1")
    node_count = config.get("node_count", 1)
    
    mapping_note = config.get("mapping_note", "")
    comment = f"  # {mapping_note}\n" if mapping_note else ""
    
    return f'''{comment}resource "digitalocean_database_cluster" "{name}" {{
  name       = "{name}"
  engine     = "{engine}"
  version    = "{version}"
  size       = "{size}"
  region     = "{region}"
  node_count = {node_count}
}}
'''


def generate_spaces_block(resource: Dict) -> str:
    """Generate Terraform block for DigitalOcean Spaces bucket"""
    name = resource.get("name", "bucket")
    config = resource.get("config", {})
    
    region = config.get("region", "nyc3")
    acl = config.get("acl", "private")
    
    mapping_note = config.get("mapping_note", "")
    comment = f"  # {mapping_note}\n" if mapping_note else ""
    
    # Spaces bucket names must be globally unique — add a suffix
    bucket_name = name.replace("_", "-")
    
    return f'''{comment}resource "digitalocean_spaces_bucket" "{name}" {{
  name   = "{bucket_name}-${{var.project_suffix}}"
  region = "{region}"
  acl    = "{acl}"
}}
'''


def generate_kubernetes_block(resource: Dict) -> str:
    """Generate Terraform block for DigitalOcean Kubernetes cluster"""
    name = resource.get("name", "k8s-cluster")
    config = resource.get("config", {})
    
    region = config.get("region", "nyc1")
    version = config.get("version", "1.28.2-do.0")
    node_pool = config.get("node_pool", {})
    
    node_name = node_pool.get("name", "worker-pool")
    node_size = node_pool.get("size", "s-2vcpu-4gb")
    node_count = node_pool.get("node_count", 2)
    auto_scale = node_pool.get("auto_scale", True)
    min_nodes = node_pool.get("min_nodes", 1)
    max_nodes = node_pool.get("max_nodes", 5)
    
    mapping_note = config.get("mapping_note", "")
    comment = f"  # {mapping_note}\n" if mapping_note else ""
    
    auto_scale_block = ""
    if auto_scale:
        auto_scale_block = f'''
    auto_scale = true
    min_nodes  = {min_nodes}
    max_nodes  = {max_nodes}'''
    
    return f'''{comment}resource "digitalocean_kubernetes_cluster" "{name}" {{
  name    = "{name}"
  region  = "{region}"
  version = "{version}"
  
  node_pool {{
    name       = "{node_name}"
    size       = "{node_size}"
    node_count = {node_count}{auto_scale_block}
  }}
}}
'''


def generate_loadbalancer_block(resource: Dict, droplet_names: List[str] = None) -> str:
    """Generate Terraform block for DigitalOcean Load Balancer"""
    name = resource.get("name", "lb")
    config = resource.get("config", {})
    
    region = config.get("region", "nyc1")
    forwarding_rules = config.get("forwarding_rules", [])
    
    mapping_note = config.get("mapping_note", "")
    comment = f"  # {mapping_note}\n" if mapping_note else ""
    
    # Generate forwarding rules
    rules_blocks = []
    for rule in forwarding_rules:
        entry_protocol = rule.get("entry_protocol", "http")
        entry_port = rule.get("entry_port", 80)
        target_protocol = rule.get("target_protocol", "http")
        target_port = rule.get("target_port", 80)
        
        rules_blocks.append(f'''  forwarding_rule {{
    entry_protocol  = "{entry_protocol}"
    entry_port      = {entry_port}
    target_protocol = "{target_protocol}"
    target_port     = {target_port}
  }}''')
    
    rules_str = "\n".join(rules_blocks) if rules_blocks else '''  forwarding_rule {
    entry_protocol  = "http"
    entry_port      = 80
    target_protocol = "http"
    target_port     = 80
  }'''
    
    # Reference droplet IDs from other resources in the config
    if droplet_names:
        refs = [f"digitalocean_droplet.{dn}.id" for dn in droplet_names]
        droplet_ids_str = "[\n    " + ",\n    ".join(refs) + "\n  ]"
    else:
        droplet_ids_str = "[]"
    
    return f'''{comment}resource "digitalocean_loadbalancer" "{name}" {{
  name   = "{name}"
  region = "{region}"
  
{rules_str}
  
  droplet_ids = {droplet_ids_str}
}}
'''


def generate_resource_block(resource: Dict) -> str:
    """
    Generate Terraform resource block based on resource type
    
    Args:
        resource: Resource dictionary with type and configuration
        
    Returns:
        Terraform resource block as string
    """
    resource_type = resource.get("type", "")
    
    if resource_type == "digitalocean_droplet":
        return generate_droplet_block(resource)
    elif resource_type == "digitalocean_database_cluster":
        return generate_database_block(resource)
    elif resource_type == "digitalocean_spaces_bucket":
        return generate_spaces_block(resource)
    elif resource_type == "digitalocean_kubernetes_cluster":
        return generate_kubernetes_block(resource)
    elif resource_type == "digitalocean_loadbalancer":
        return generate_loadbalancer_block(resource)
    else:
        return f"# Unsupported resource type: {resource_type}\n"


def generate_outputs(resources: List[Dict]) -> str:
    """
    Generate Terraform outputs for resource IDs
    
    Args:
        resources: List of resources
        
    Returns:
        Terraform outputs block as string
    """
    outputs = []
    
    for resource in resources:
        resource_type = resource.get("type", "")
        name = resource.get("name", "resource")
        
        if resource_type == "digitalocean_droplet":
            outputs.append(f'''output "{name}_id" {{
  description = "ID of {name} droplet"
  value       = digitalocean_droplet.{name}.id
}}

output "{name}_ip" {{
  description = "IP address of {name} droplet"
  value       = digitalocean_droplet.{name}.ipv4_address
}}
''')
        elif resource_type == "digitalocean_database_cluster":
            outputs.append(f'''output "{name}_id" {{
  description = "ID of {name} database cluster"
  value       = digitalocean_database_cluster.{name}.id
}}

output "{name}_uri" {{
  description = "Connection URI for {name} database"
  value       = digitalocean_database_cluster.{name}.uri
  sensitive   = true
}}
''')
        elif resource_type == "digitalocean_kubernetes_cluster":
            outputs.append(f'''output "{name}_id" {{
  description = "ID of {name} Kubernetes cluster"
  value       = digitalocean_kubernetes_cluster.{name}.id
}}

output "{name}_endpoint" {{
  description = "Endpoint of {name} Kubernetes cluster"
  value       = digitalocean_kubernetes_cluster.{name}.endpoint
}}
''')
        elif resource_type == "digitalocean_loadbalancer":
            outputs.append(f'''output "{name}_id" {{
  description = "ID of {name} load balancer"
  value       = digitalocean_loadbalancer.{name}.id
}}

output "{name}_ip" {{
  description = "IP address of {name} load balancer"
  value       = digitalocean_loadbalancer.{name}.ip
}}
''')
    
    return "\n".join(outputs)


def validate_terraform_syntax(terraform_code: str) -> tuple[bool, List[str]]:
    """
    Validate Terraform syntax using basic regex patterns
    
    Args:
        terraform_code: Terraform code to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check for balanced braces
    open_braces = terraform_code.count("{")
    close_braces = terraform_code.count("}")
    if open_braces != close_braces:
        errors.append(f"Unbalanced braces: {open_braces} opening, {close_braces} closing")
    
    # Check for required provider block
    if "provider \"digitalocean\"" not in terraform_code:
        errors.append("Missing DigitalOcean provider block")
    
    # Check for resource blocks
    if not re.search(r'resource\s+"[\w_]+"', terraform_code):
        errors.append("No resource blocks found")
    
    # Check for invalid characters in resource names
    resource_names = re.findall(r'resource\s+"[\w_]+"\s+"([\w-]+)"', terraform_code)
    for name in resource_names:
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            errors.append(f"Invalid resource name: {name}")
    
    return len(errors) == 0, errors


def format_terraform_code(terraform_code: str) -> str:
    """
    Format Terraform code according to style guidelines
    
    Args:
        terraform_code: Unformatted Terraform code
        
    Returns:
        Formatted Terraform code
    """
    # Basic formatting (in production, use `terraform fmt`)
    lines = terraform_code.split("\n")
    formatted_lines = []
    
    for line in lines:
        # Remove trailing whitespace
        line = line.rstrip()
        formatted_lines.append(line)
    
    # Remove multiple consecutive blank lines
    result = []
    prev_blank = False
    for line in formatted_lines:
        if line.strip() == "":
            if not prev_blank:
                result.append(line)
            prev_blank = True
        else:
            result.append(line)
            prev_blank = False
    
    return "\n".join(result)


def generate_terraform_code(resources: List[Dict], include_outputs: bool = True, include_ai_stack: bool = False) -> str:
    """
    Generate complete Terraform configuration for DigitalOcean resources
    
    Args:
        resources: List of DigitalOcean resources
        include_outputs: Whether to include output blocks
        include_ai_stack: Whether to include AI agent stack
        
    Returns:
        Complete Terraform configuration as string
    """
    # Generate sections
    provider = generate_provider_block()
    variables = generate_variables()
    
    # Collect droplet resource names for load balancer references
    droplet_names = [
        r.get("name", "droplet")
        for r in resources
        if r.get("type") == "digitalocean_droplet"
    ]
    
    resource_blocks = []
    for resource in resources:
        resource_type = resource.get("type", "")
        if resource_type == "digitalocean_loadbalancer":
            block = generate_loadbalancer_block(resource, droplet_names=droplet_names)
        else:
            block = generate_resource_block(resource)
        resource_blocks.append(block)
    
    outputs = generate_outputs(resources) if include_outputs else ""
    
    # Combine all sections
    terraform_code = f"""{provider}

{variables}

# Resources
{chr(10).join(resource_blocks)}
"""
    
    if outputs:
        terraform_code += f"\n# Outputs\n{outputs}"
    
    # Add AI stack note if not included
    if not include_ai_stack:
        terraform_code += f"""

# ============================================================================
# AI Agent Stack (Optional)
# ============================================================================
# 
# To enable the DONS AI Agent Stack, generate the AI stack Terraform:
# - Cloud Migration Architect Agent
# - DevOps Agent with Self-Healing
# - AI Enablement Agent with RAG
# 
# The AI stack includes:
# - Managed OpenSearch for vector storage
# - Spaces bucket for Knowledge Base
# - App Platform deployment for agents
# 
# Estimated cost: $101-161/month
# 
# To generate AI stack configuration, use the AI stack generator
# or enable it in the DONS platform UI.
# ============================================================================
"""
    
    # Format and validate
    terraform_code = format_terraform_code(terraform_code)
    is_valid, errors = validate_terraform_syntax(terraform_code)
    
    if not is_valid:
        # Add validation errors as comments
        error_comments = "\n".join([f"# VALIDATION ERROR: {err}" for err in errors])
        terraform_code = f"{error_comments}\n\n{terraform_code}"
    
    return terraform_code
