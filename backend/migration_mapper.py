"""
AWS to DigitalOcean resource mapping for DONS platform.
Maps AWS resources to equivalent DigitalOcean resources.
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from terraform_parser import AWSResource


class DOResource(BaseModel):
    """DigitalOcean resource model."""
    resource_type: str  # e.g., "digitalocean_droplet"
    resource_name: str
    configuration: Dict[str, Any]
    original_aws_type: str
    mapping_notes: Optional[str] = None
    is_supported: bool = True


def map_instance_to_droplet(aws_instance: AWSResource) -> DOResource:
    """
    Map aws_instance to DigitalOcean Droplet.
    
    Args:
        aws_instance: AWS EC2 instance resource
        
    Returns:
        DOResource for DigitalOcean Droplet
    """
    config = aws_instance.configuration
    
    # Map instance type to Droplet size
    instance_type = config.get('instance_type', 't2.micro')
    droplet_size = map_instance_type_to_size(instance_type)
    
    # Map AMI to Droplet image
    ami = config.get('ami', '')
    droplet_image = map_ami_to_image(ami)
    
    # Build Droplet configuration
    droplet_config = {
        'name': aws_instance.resource_name.replace('_', '-'),
        'size': droplet_size,
        'image': droplet_image,
        'region': 'nyc1',  # Default region
        'ipv6': config.get('ipv6_address_count', 0) > 0,
        'monitoring': True,  # Enable monitoring by default
    }

    # Tags must be a list of strings
    raw_tags = config.get('tags', {})
    if isinstance(raw_tags, dict):
        droplet_config['tags'] = list(raw_tags.values()) if raw_tags else [aws_instance.resource_name]
    elif isinstance(raw_tags, list):
        droplet_config['tags'] = raw_tags
    else:
        droplet_config['tags'] = [str(raw_tags)] if raw_tags else [aws_instance.resource_name]
    
    # Add SSH keys if specified
    if 'key_name' in config:
        droplet_config['ssh_keys'] = [config['key_name']]
    
    # Add user data if specified
    if 'user_data' in config:
        droplet_config['user_data'] = config['user_data']
    
    notes = f"Mapped from {instance_type} to {droplet_size}"
    
    return DOResource(
        resource_type='digitalocean_droplet',
        resource_name=aws_instance.resource_name,
        configuration=droplet_config,
        original_aws_type=aws_instance.resource_type,
        mapping_notes=notes,
        is_supported=True
    )


def map_rds_to_managed_db(aws_db: AWSResource) -> DOResource:
    """
    Map aws_db_instance to DigitalOcean Managed Database.
    
    Args:
        aws_db: AWS RDS instance resource
        
    Returns:
        DOResource for DigitalOcean Managed Database
    """
    config = aws_db.configuration
    
    # Map engine
    engine = config.get('engine', 'postgres')
    do_engine = map_db_engine(engine)
    
    # Map instance class to size
    instance_class = config.get('instance_class', 'db.t2.micro')
    db_size = map_db_instance_class_to_size(instance_class)
    
    # Build database configuration
    db_config = {
        'name': aws_db.resource_name.replace('_', '-'),  # DO uses hyphens
        'engine': do_engine,
        'version': map_db_version(engine, config.get('engine_version', '')),
        'size': db_size,
        'region': 'nyc1',
        'node_count': 1,  # Start with single node
    }
    
    notes = f"Mapped from {instance_class} to {db_size}."
    
    return DOResource(
        resource_type='digitalocean_database_cluster',
        resource_name=aws_db.resource_name,
        configuration=db_config,
        original_aws_type=aws_db.resource_type,
        mapping_notes=notes,
        is_supported=True
    )


def map_s3_to_spaces(aws_s3: AWSResource) -> DOResource:
    """
    Map aws_s3_bucket to DigitalOcean Spaces.
    
    Args:
        aws_s3: AWS S3 bucket resource
        
    Returns:
        DOResource for DigitalOcean Spaces
    """
    config = aws_s3.configuration
    
    # Build Spaces configuration
    spaces_config = {
        'name': aws_s3.resource_name.lower().replace('_', '-'),  # Spaces requires lowercase, hyphens only
        'region': 'nyc3',  # Spaces region
        'acl': config.get('acl', 'private')
    }
    
    # Add CORS if specified
    if 'cors_rule' in config:
        spaces_config['cors_rule'] = config['cors_rule']
    
    # Add lifecycle rules if specified
    if 'lifecycle_rule' in config:
        spaces_config['lifecycle_rule'] = config['lifecycle_rule']
    
    notes = "Mapped to DigitalOcean Spaces (S3-compatible)"
    
    return DOResource(
        resource_type='digitalocean_spaces_bucket',
        resource_name=aws_s3.resource_name,
        configuration=spaces_config,
        original_aws_type=aws_s3.resource_type,
        mapping_notes=notes,
        is_supported=True
    )


def map_eks_to_doks(aws_eks: AWSResource) -> DOResource:
    """
    Map aws_eks_cluster to DigitalOcean Kubernetes.
    
    Args:
        aws_eks: AWS EKS cluster resource
        
    Returns:
        DOResource for DigitalOcean Kubernetes
    """
    config = aws_eks.configuration
    
    # Build DOKS configuration
    doks_config = {
        'name': aws_eks.resource_name,
        'region': 'nyc1',
        'version': map_k8s_version(config.get('version', '1.28')),
        'node_pool': {
            'name': 'default-pool',
            'size': 's-2vcpu-4gb',  # Default node size
            'node_count': 2,  # Start with 2 nodes
            'auto_scale': True,
            'min_nodes': 1,
            'max_nodes': 5
        },
        'tags': [aws_eks.resource_name]
    }
    
    notes = "Mapped to DigitalOcean Kubernetes with auto-scaling enabled"
    
    return DOResource(
        resource_type='digitalocean_kubernetes_cluster',
        resource_name=aws_eks.resource_name,
        configuration=doks_config,
        original_aws_type=aws_s3.resource_type,
        mapping_notes=notes,
        is_supported=True
    )


def map_elb_to_lb(aws_lb: AWSResource) -> DOResource:
    """
    Map aws_lb/aws_elb to DigitalOcean Load Balancer.
    
    Args:
        aws_lb: AWS Load Balancer resource
        
    Returns:
        DOResource for DigitalOcean Load Balancer
    """
    config = aws_lb.configuration
    
    # Build Load Balancer configuration
    lb_config = {
        'name': aws_lb.resource_name.replace('_', '-'),
        'region': 'nyc1',
        'algorithm': 'round_robin',  # Default algorithm
        'forwarding_rules': [],
        'healthcheck': {
            'protocol': 'http',
            'port': 80,
            'path': '/',
            'check_interval_seconds': 10,
            'response_timeout_seconds': 5,
            'healthy_threshold': 5,
            'unhealthy_threshold': 3
        },
    }
    
    # Map listeners to forwarding rules
    listeners = config.get('listener', [])
    if not isinstance(listeners, list):
        listeners = [listeners]
    
    for listener in listeners:
        rule = {
            'entry_protocol': listener.get('protocol', 'http').lower(),
            'entry_port': listener.get('port', 80),
            'target_protocol': listener.get('protocol', 'http').lower(),
            'target_port': listener.get('port', 80)
        }
        
        # Handle HTTPS
        if rule['entry_protocol'] == 'https':
            rule['certificate_id'] = 'your-certificate-id'  # Placeholder
        
        lb_config['forwarding_rules'].append(rule)
    
    notes = "Mapped to DigitalOcean Load Balancer"
    
    return DOResource(
        resource_type='digitalocean_loadbalancer',
        resource_name=aws_lb.resource_name,
        configuration=lb_config,
        original_aws_type=aws_lb.resource_type,
        mapping_notes=notes,
        is_supported=True
    )


# Helper mapping functions

def map_instance_type_to_size(instance_type: str) -> str:
    """Map AWS instance type to DO Droplet size."""
    mapping = {
        't2.micro': 's-1vcpu-1gb',
        't2.small': 's-1vcpu-2gb',
        't2.medium': 's-2vcpu-2gb',
        't2.large': 's-2vcpu-4gb',
        't3.micro': 's-1vcpu-1gb',
        't3.small': 's-1vcpu-2gb',
        't3.medium': 's-2vcpu-2gb',
        't3.large': 's-2vcpu-4gb',
        'm5.large': 's-2vcpu-4gb',
        'm5.xlarge': 's-4vcpu-8gb',
        'm5.2xlarge': 's-8vcpu-16gb',
        'c5.large': 'c-2',
        'c5.xlarge': 'c-4',
        'c5.2xlarge': 'c-8'
    }
    return mapping.get(instance_type, 's-2vcpu-4gb')  # Default


def map_ami_to_image(ami: str) -> str:
    """Map AWS AMI to DO image."""
    # For now, use Ubuntu as default
    # In production, would analyze AMI details
    return 'ubuntu-22-04-x64'


def map_db_engine(engine: str) -> str:
    """Map AWS RDS engine to DO database engine."""
    mapping = {
        'postgres': 'pg',
        'postgresql': 'pg',
        'mysql': 'mysql',
        'redis': 'redis',
        'mongodb': 'mongodb'
    }
    return mapping.get(engine.lower(), 'pg')


def map_db_instance_class_to_size(instance_class: str) -> str:
    """Map AWS RDS instance class to DO database size."""
    mapping = {
        'db.t2.micro': 'db-s-1vcpu-1gb',
        'db.t2.small': 'db-s-1vcpu-2gb',
        'db.t2.medium': 'db-s-2vcpu-4gb',
        'db.t3.micro': 'db-s-1vcpu-1gb',
        'db.t3.small': 'db-s-1vcpu-2gb',
        'db.t3.medium': 'db-s-2vcpu-4gb',
        'db.m5.large': 'db-s-4vcpu-8gb',
        'db.m5.xlarge': 'db-s-8vcpu-16gb'
    }
    return mapping.get(instance_class, 'db-s-2vcpu-4gb')


def map_db_version(engine: str, version: str) -> str:
    """Map database version to DO supported version."""
    # Simplified version mapping
    if engine.lower() in ['postgres', 'postgresql']:
        return '15'  # Latest stable
    elif engine.lower() == 'mysql':
        return '8'
    elif engine.lower() == 'redis':
        return '7'
    elif engine.lower() == 'mongodb':
        return '6'
    return version


def map_k8s_version(version: str) -> str:
    """Map Kubernetes version to DO supported version."""
    # Map to latest stable DO version
    return '1.28.2-do.0'


def map_aws_to_do(aws_resource: AWSResource) -> DOResource:
    """
    Main mapping function - routes to specific mapper based on resource type.
    
    Args:
        aws_resource: AWS resource to map
        
    Returns:
        DOResource with DigitalOcean equivalent
    """
    resource_type = aws_resource.resource_type
    
    if resource_type == 'aws_instance':
        return map_instance_to_droplet(aws_resource)
    elif resource_type == 'aws_db_instance':
        return map_rds_to_managed_db(aws_resource)
    elif resource_type == 'aws_s3_bucket':
        return map_s3_to_spaces(aws_resource)
    elif resource_type == 'aws_eks_cluster':
        return map_eks_to_doks(aws_resource)
    elif resource_type in ['aws_lb', 'aws_elb', 'aws_alb']:
        return map_elb_to_lb(aws_resource)
    else:
        # Unsupported resource
        return DOResource(
            resource_type='unsupported',
            resource_name=aws_resource.resource_name,
            configuration={},
            original_aws_type=resource_type,
            mapping_notes=f"No DigitalOcean equivalent for {resource_type}",
            is_supported=False
        )


def identify_unsupported_resources(resources: List[AWSResource]) -> List[str]:
    """
    Identify resources that don't have DigitalOcean equivalents.
    
    Args:
        resources: List of AWS resources
        
    Returns:
        List of unsupported resource types
    """
    supported_types = [
        'aws_instance',
        'aws_db_instance',
        'aws_s3_bucket',
        'aws_eks_cluster',
        'aws_lb',
        'aws_elb',
        'aws_alb'
    ]
    
    unsupported = set()
    for resource in resources:
        if resource.resource_type not in supported_types:
            unsupported.add(resource.resource_type)
    
    return list(unsupported)
