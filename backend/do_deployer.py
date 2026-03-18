"""
DigitalOcean Deployer Module

Deploys infrastructure to DigitalOcean using the API.
Handles deployment orchestration, progress tracking, and rollback.
"""

import os
import time
import json
import asyncio
from typing import List, Dict, Optional, Tuple
import requests
import boto3
from botocore.client import Config


# DigitalOcean API configuration
DO_API_BASE = "https://api.digitalocean.com/v2"
DO_API_TOKEN = os.getenv("DIGITALOCEAN_API_TOKEN")
DO_PROJECT_NAME = os.getenv("DO_PROJECT_NAME", "DONS")

# Spaces configuration
SPACES_REGION = os.getenv("DO_SPACES_REGION", "nyc3")
SPACES_ACCESS_KEY = os.getenv("DO_SPACES_ACCESS_KEY") or os.getenv("SPACES_ACCESS_KEY_ID")
SPACES_SECRET_KEY = os.getenv("DO_SPACES_SECRET_KEY") or os.getenv("SPACES_ACCESS_KEY")


def get_headers() -> Dict[str, str]:
    """Get headers for DigitalOcean API requests"""
    return {
        "Authorization": f"Bearer {DO_API_TOKEN}",
        "Content-Type": "application/json"
    }


def create_droplet(config: Dict) -> Dict:
    """
    Create a DigitalOcean Droplet
    
    Args:
        config: Droplet configuration
        
    Returns:
        API response with droplet details
    """
    url = f"{DO_API_BASE}/droplets"
    
    payload = {
        "name": config.get("name", "droplet").replace("_", "-"),
        "region": config.get("region", "nyc1"),
        "size": config.get("size", "s-2vcpu-4gb"),
        "image": config.get("image", "ubuntu-22-04-x64"),
        "tags": config.get("tags", []) if isinstance(config.get("tags", []), list) else [config.get("tags", "")],
    }
    
    # Add SSH keys if provided
    if "ssh_keys" in config:
        payload["ssh_keys"] = config["ssh_keys"]
    
    # Add user data if provided
    if "user_data" in config:
        payload["user_data"] = config["user_data"]
    
    print(f"[DROPLET] Creating droplet with payload: {json.dumps(payload)}")
    response = requests.post(url, json=payload, headers=get_headers())
    if response.status_code >= 400:
        print(f"[DROPLET] ❌ DO API error {response.status_code}: {response.text}")
    response.raise_for_status()
    
    return response.json()


def create_database(config: Dict) -> Dict:
    """
    Create a DigitalOcean Managed Database
    
    Args:
        config: Database configuration
        
    Returns:
        API response with database details
    """
    url = f"{DO_API_BASE}/databases"
    
    payload = {
        "name": config.get("name", "database").replace("_", "-"),
        "engine": config.get("engine", "pg"),
        "version": config.get("version", "15"),
        "region": config.get("region", "nyc1"),
        "size": config.get("size", "db-s-1vcpu-2gb"),
        "num_nodes": config.get("node_count", 1),
    }
    
    # Add storage size if provided (only for larger sizes)
    if "storage_size_mib" in config:
        payload["storage_size_mib"] = config["storage_size_mib"]
    
    print(f"[DB] Creating database with payload: {json.dumps(payload)}")
    response = requests.post(url, json=payload, headers=get_headers())
    if response.status_code >= 400:
        print(f"[DB] ❌ DO API error {response.status_code}: {response.text}")
    response.raise_for_status()
    
    return response.json()


def create_spaces_bucket(config: Dict) -> Dict:
    """
    Create a DigitalOcean Spaces bucket using S3-compatible API
    
    Args:
        config: Spaces bucket configuration
        
    Returns:
        Bucket details
    """
    bucket_name = config.get("name", "bucket").replace("_", "-").lower()
    region = config.get("region", SPACES_REGION)
    acl = config.get("acl", "private")
    
    print(f"[SPACES] Creating bucket '{bucket_name}' in region '{region}'")
    
    try:
        # Create S3 client for Spaces
        session = boto3.session.Session()
        client = session.client(
            's3',
            region_name=region,
            endpoint_url=f'https://{region}.digitaloceanspaces.com',
            aws_access_key_id=SPACES_ACCESS_KEY,
            aws_secret_access_key=SPACES_SECRET_KEY,
            config=Config(signature_version='s3v4')
        )
        
        # Check if bucket already exists
        try:
            client.head_bucket(Bucket=bucket_name)
            print(f"[SPACES] ⚠️  Bucket '{bucket_name}' already exists, using existing bucket")
        except:
            # Bucket doesn't exist, create it
            client.create_bucket(Bucket=bucket_name, ACL=acl)
            print(f"[SPACES] ✅ Bucket created successfully")
        
        return {
            "bucket": {
                "name": bucket_name,
                "region": region,
                "endpoint": f"https://{bucket_name}.{region}.digitaloceanspaces.com"
            }
        }
    except Exception as e:
        print(f"[SPACES] ❌ Error creating bucket: {str(e)}")
        raise


def create_kubernetes_cluster(config: Dict) -> Dict:
    """
    Create a DigitalOcean Kubernetes cluster
    
    Args:
        config: Kubernetes cluster configuration
        
    Returns:
        API response with cluster details
    """
    url = f"{DO_API_BASE}/kubernetes/clusters"
    
    node_pool = config.get("node_pool", {})
    
    payload = {
        "name": config.get("name", "k8s-cluster"),
        "region": config.get("region", "nyc1"),
        "version": config.get("version", "1.28.2-do.0"),
        "node_pools": [
            {
                "name": node_pool.get("name", "worker-pool"),
                "size": node_pool.get("size", "s-2vcpu-4gb"),
                "count": node_pool.get("node_count", 2),
                "auto_scale": node_pool.get("auto_scale", True),
                "min_nodes": node_pool.get("min_nodes", 1),
                "max_nodes": node_pool.get("max_nodes", 5),
            }
        ],
    }
    
    response = requests.post(url, json=payload, headers=get_headers())
    response.raise_for_status()
    
    return response.json()


def create_load_balancer(config: Dict) -> Dict:
    """
    Create a DigitalOcean Load Balancer
    
    Args:
        config: Load balancer configuration
        
    Returns:
        API response with load balancer details
    """
    url = f"{DO_API_BASE}/load_balancers"
    
    forwarding_rules = config.get("forwarding_rules", [])
    if not forwarding_rules:
        # Default HTTP rule
        forwarding_rules = [
            {
                "entry_protocol": "http",
                "entry_port": 80,
                "target_protocol": "http",
                "target_port": 80
            }
        ]
    
    payload = {
        "name": config.get("name", "lb").replace("_", "-"),
        "region": config.get("region", "nyc1"),
        "forwarding_rules": forwarding_rules,
    }
    
    # Only include droplet_ids if we have actual IDs
    droplet_ids = config.get("droplet_ids", [])
    if droplet_ids:
        payload["droplet_ids"] = droplet_ids
    
    # Include health check if provided
    if "healthcheck" in config:
        payload["health_check"] = config["healthcheck"]
    
    print(f"[LB] Creating load balancer with payload: {json.dumps(payload, default=str)}")
    response = requests.post(url, json=payload, headers=get_headers())
    if response.status_code >= 400:
        print(f"[LB] ❌ DO API error {response.status_code}: {response.text}")
    response.raise_for_status()
    
    return response.json()


def get_resource_status(resource_type: str, resource_id: str) -> str:
    """
    Get the status of a deployed resource
    
    Args:
        resource_type: Type of resource (droplet, database, kubernetes, load_balancer)
        resource_id: Resource ID
        
    Returns:
        Resource status (active, new, provisioning, etc.)
    """
    if resource_type == "droplet":
        url = f"{DO_API_BASE}/droplets/{resource_id}"
    elif resource_type == "database":
        url = f"{DO_API_BASE}/databases/{resource_id}"
    elif resource_type == "kubernetes":
        url = f"{DO_API_BASE}/kubernetes/clusters/{resource_id}"
    elif resource_type == "load_balancer":
        url = f"{DO_API_BASE}/load_balancers/{resource_id}"
    else:
        return "unknown"
    
    try:
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        data = response.json()
        
        # Extract status based on resource type
        if resource_type == "droplet":
            return data.get("droplet", {}).get("status", "unknown")
        elif resource_type == "database":
            return data.get("database", {}).get("status", "unknown")
        elif resource_type == "kubernetes":
            return data.get("kubernetes_cluster", {}).get("status", {}).get("state", "unknown")
        elif resource_type == "load_balancer":
            return data.get("load_balancer", {}).get("status", "unknown")
    except Exception as e:
        print(f"Error getting status for {resource_type} {resource_id}: {e}")
        return "error"
    
    return "unknown"


async def track_deployment_progress(resource_type: str, resource_id: str, timeout: int = 600) -> bool:
    """
    Track deployment progress by polling resource status
    
    Args:
        resource_type: Type of resource
        resource_id: Resource ID
        timeout: Maximum time to wait in seconds
        
    Returns:
        True if resource becomes active, False if timeout
    """
    start_time = time.time()
    poll_count = 0
    
    # Increase timeout for databases (they take 3-5 minutes to provision)
    if resource_type == "database":
        timeout = 600  # Wait up to 10 minutes for databases
    
    while time.time() - start_time < timeout:
        status = get_resource_status(resource_type, resource_id)
        poll_count += 1
        
        print(f"[POLL {poll_count}] {resource_type} {resource_id}: {status}")
        
        if status in ("active", "online"):
            return True
        elif status == "error":
            return False
        
        # Wait 10 seconds before next poll
        await asyncio.sleep(10)
    
    print(f"[TIMEOUT] {resource_type} {resource_id} did not become active within {timeout}s")
    return False


def determine_deployment_order(resources: List[Dict]) -> List[Dict]:
    """
    Determine deployment order based on dependencies
    
    Args:
        resources: List of resources to deploy
        
    Returns:
        Ordered list of resources
    """
    # Deployment order priority:
    # 1. Droplets (compute)
    # 2. Databases
    # 3. Spaces buckets
    # 4. Kubernetes clusters
    # 5. Load balancers (depend on droplets)
    
    priority_map = {
        "digitalocean_droplet": 1,
        "digitalocean_database_cluster": 2,
        "digitalocean_spaces_bucket": 3,
        "digitalocean_kubernetes_cluster": 4,
        "digitalocean_loadbalancer": 5,
    }
    
    return sorted(resources, key=lambda r: priority_map.get(r.get("type", ""), 99))


def get_or_create_project(project_name: str = None) -> Optional[str]:
    """
    Find an existing project by name or create a new one.

    Args:
        project_name: Name of the project (defaults to DO_PROJECT_NAME)

    Returns:
        Project ID string, or None on failure
    """
    name = project_name or DO_PROJECT_NAME
    try:
        # List existing projects
        url = f"{DO_API_BASE}/projects"
        response = requests.get(url, headers=get_headers())
        if response.status_code != 200:
            print(f"[PROJECT] ⚠️  Could not list projects: {response.status_code}")
            return None

        projects = response.json().get("projects", [])
        for project in projects:
            if project.get("name") == name:
                print(f"[PROJECT] Found existing project '{name}' → {project['id']}")
                return project["id"]

        # Project doesn't exist — create it
        print(f"[PROJECT] Project '{name}' not found, creating...")
        payload = {
            "name": name,
            "description": "DONS Cloud Migration Platform — deployed resources",
            "purpose": "Service or API",
            "environment": "Production",
        }
        resp = requests.post(url, json=payload, headers=get_headers())
        if resp.status_code in (200, 201):
            project_id = resp.json().get("project", {}).get("id")
            print(f"[PROJECT] ✅ Created project '{name}' → {project_id}")
            return project_id
        else:
            print(f"[PROJECT] ❌ Failed to create project: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"[PROJECT] ❌ Error in get_or_create_project: {e}")
        return None


def associate_with_project(resource_type: str, resource_id: str, project_id: str = None) -> bool:
    """
    Associate deployed resource with DO project.

    Args:
        resource_type: Type of resource
        resource_id: Resource ID
        project_id: Project ID (if None, will look up by DO_PROJECT_NAME)

    Returns:
        True if successful
    """
    try:
        if not project_id:
            project_id = get_or_create_project()
        if not project_id:
            print(f"[PROJECT] ⚠️  No project ID available, skipping association")
            return False

        url = f"{DO_API_BASE}/projects/{project_id}/resources"

        # Map resource type to URN format
        urn_type_map = {
            "droplet": "do:droplet",
            "database": "do:dbaas",
            "kubernetes": "do:kubernetes",
            "load_balancer": "do:loadbalancer",
            "spaces": "do:space",
        }

        urn_type = urn_type_map.get(resource_type, "do:resource")
        urn = f"{urn_type}:{resource_id}"

        payload = {"resources": [urn]}

        print(f"[PROJECT] Associating {urn} with project {project_id}")
        response = requests.post(url, json=payload, headers=get_headers())

        if response.status_code == 200:
            print(f"[PROJECT] ✅ Successfully associated {resource_type} {resource_id}")
            return True
        else:
            print(f"[PROJECT] ❌ Failed to associate: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"[PROJECT] ❌ Error associating resource: {str(e)}")
        return False


async def deploy_infrastructure(resources: List[Dict]) -> Dict:
    """
    Deploy infrastructure to DigitalOcean
    
    Args:
        resources: List of resources to deploy
        
    Returns:
        Deployment result with status and deployed resources
    """
    from datetime import datetime
    
    # Generate HHmm suffix for unique resource names
    time_suffix = datetime.utcnow().strftime("%H%M")
    
    # Determine deployment order
    ordered_resources = determine_deployment_order(resources)
    
    # Create or find the project ONCE before deploying anything
    project_id = get_or_create_project()
    
    deployed = []
    failed = []
    deployed_droplet_ids = []  # Track droplet IDs for load balancer association
    
    print(f"\n[DEPLOY] Starting deployment of {len(ordered_resources)} resources (suffix: {time_suffix})")
    
    for idx, resource in enumerate(ordered_resources, 1):
        resource_type = resource.get("type", "")
        config = resource.get("config", {}).copy()  # copy so we don't mutate original
        name = resource.get("name", "resource")
        
        # Append HHmm suffix to resource name for uniqueness
        if "name" in config:
            config["name"] = f"{config['name']}-{time_suffix}"
        else:
            config["name"] = f"{name}-{time_suffix}"
        
        print(f"\n[DEPLOY] [{idx}/{len(ordered_resources)}] Deploying {resource_type}: {name}")
        
        try:
            # Deploy based on type
            if resource_type == "digitalocean_droplet":
                print(f"[DEPLOY] Creating droplet...")
                result = create_droplet(config)
                resource_id = result.get("droplet", {}).get("id")
                api_type = "droplet"
                if resource_id:
                    deployed_droplet_ids.append(resource_id)
                print(f"[DEPLOY] ✅ Droplet created with ID: {resource_id}")
                
            elif resource_type == "digitalocean_database_cluster":
                print(f"[DEPLOY] Creating database cluster...")
                result = create_database(config)
                resource_id = result.get("database", {}).get("id")
                api_type = "database"
                print(f"[DEPLOY] ✅ Database created with ID: {resource_id}")
                
            elif resource_type == "digitalocean_spaces_bucket":
                print(f"[DEPLOY] Creating Spaces bucket...")
                result = create_spaces_bucket(config)
                resource_id = result.get("bucket", {}).get("name")
                api_type = "spaces"
                print(f"[DEPLOY] ✅ Spaces bucket created: {resource_id}")
                
            elif resource_type == "digitalocean_kubernetes_cluster":
                print(f"[DEPLOY] Creating Kubernetes cluster...")
                result = create_kubernetes_cluster(config)
                resource_id = result.get("kubernetes_cluster", {}).get("id")
                api_type = "kubernetes"
                print(f"[DEPLOY] ✅ Kubernetes cluster created with ID: {resource_id}")
                
            elif resource_type == "digitalocean_loadbalancer":
                print(f"[DEPLOY] Creating load balancer...")
                # Inject deployed droplet IDs into LB config
                print(f"[DEPLOY] Droplet IDs to attach to LB: {deployed_droplet_ids}")
                if deployed_droplet_ids:
                    config["droplet_ids"] = deployed_droplet_ids
                else:
                    print(f"[DEPLOY] ⚠️  No droplet IDs available — LB will have no targets")
                result = create_load_balancer(config)
                resource_id = result.get("load_balancer", {}).get("id")
                api_type = "load_balancer"
                print(f"[DEPLOY] ✅ Load balancer created with ID: {resource_id}")
                
            else:
                print(f"[DEPLOY] ❌ Unsupported resource type: {resource_type}")
                failed.append({
                    "name": name,
                    "type": resource_type,
                    "error": "Unsupported resource type"
                })
                continue
            
            # Track deployment progress (except for Spaces)
            if api_type != "spaces":
                print(f"[DEPLOY] Waiting for {api_type} to become active...")
                success = await track_deployment_progress(api_type, resource_id)
                
                if not success:
                    print(f"[DEPLOY] ⚠️  {api_type} did not become active (timeout)")
                    # Still add to deployed list but mark as provisioning
                    deployed.append({
                        "name": name,
                        "type": resource_type,
                        "id": str(resource_id),
                        "status": "provisioning"
                    })
                    # Try to associate with project anyway
                    associate_with_project(api_type, resource_id, project_id)
                    continue
                
                print(f"[DEPLOY] ✅ {api_type} is now active")
                
                # Associate with project
                associate_with_project(api_type, resource_id, project_id)
            else:
                # Spaces buckets are instant, no need to wait
                print(f"[DEPLOY] ✅ Spaces bucket ready")
                associate_with_project("spaces", resource_id, project_id)
            
            deployed.append({
                "name": name,
                "type": resource_type,
                "id": str(resource_id),
                "status": "active"
            })
            
        except Exception as e:
            print(f"[DEPLOY] ❌ Failed to deploy {name}: {str(e)}")
            failed.append({
                "name": name,
                "type": resource_type,
                "error": str(e)
            })
            
            # Continue with next resource instead of halting
            continue
    
    # Calculate overall status
    if failed and not deployed:
        status = "failed"
    elif failed:
        status = "partial"
    elif len(deployed) == len(ordered_resources):
        status = "completed"
    else:
        status = "partial"
    
    print(f"\n[DEPLOY] Deployment complete: {status}")
    print(f"[DEPLOY] Deployed: {len(deployed)}, Failed: {len(failed)}")
    
    return {
        "status": status,
        "deployed_resources": deployed,
        "failed_resources": failed,
        "total_resources": len(ordered_resources),
        "deployed_count": len(deployed),
        "failed_count": len(failed)
    }


def delete_resource(resource_type: str, resource_id: str) -> bool:
    """
    Delete a deployed resource
    
    Args:
        resource_type: Type of resource
        resource_id: Resource ID
        
    Returns:
        True if successful
    """
    try:
        if resource_type == "droplet":
            url = f"{DO_API_BASE}/droplets/{resource_id}"
        elif resource_type == "database":
            url = f"{DO_API_BASE}/databases/{resource_id}"
        elif resource_type == "kubernetes":
            url = f"{DO_API_BASE}/kubernetes/clusters/{resource_id}"
        elif resource_type == "load_balancer":
            url = f"{DO_API_BASE}/load_balancers/{resource_id}"
        elif resource_type == "spaces":
            # Delete Spaces bucket
            session = boto3.session.Session()
            client = session.client(
                's3',
                region_name=SPACES_REGION,
                endpoint_url=f'https://{SPACES_REGION}.digitaloceanspaces.com',
                aws_access_key_id=SPACES_ACCESS_KEY,
                aws_secret_access_key=SPACES_SECRET_KEY
            )
            client.delete_bucket(Bucket=resource_id)
            return True
        else:
            return False
        
        response = requests.delete(url, headers=get_headers())
        return response.status_code == 204
        
    except Exception as e:
        print(f"Error deleting {resource_type} {resource_id}: {e}")
        return False


async def rollback_deployment(deployed_resources: List[Dict]) -> Dict:
    """
    Rollback deployment by deleting resources in reverse order
    
    Args:
        deployed_resources: List of deployed resources
        
    Returns:
        Rollback result
    """
    # Reverse order for rollback
    reversed_resources = list(reversed(deployed_resources))
    
    deleted = []
    failed = []
    
    for resource in reversed_resources:
        resource_type = resource.get("type", "")
        resource_id = resource.get("id", "")
        name = resource.get("name", "")
        
        # Map resource type to API type
        api_type_map = {
            "digitalocean_droplet": "droplet",
            "digitalocean_database_cluster": "database",
            "digitalocean_kubernetes_cluster": "kubernetes",
            "digitalocean_loadbalancer": "load_balancer",
            "digitalocean_spaces_bucket": "spaces",
        }
        
        api_type = api_type_map.get(resource_type, "")
        
        if delete_resource(api_type, resource_id):
            deleted.append(name)
        else:
            failed.append(name)
    
    return {
        "status": "completed" if not failed else "partial",
        "deleted_resources": deleted,
        "failed_deletions": failed
    }
