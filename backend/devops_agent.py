"""
DevOps Monitoring AI Agent

Monitors DigitalOcean infrastructure, detects anomalies, creates alerts,
and implements self-healing capabilities with Terraform PR generation.
"""

import os
import json
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import requests
from openai import OpenAI


# DigitalOcean API configuration
DO_API_BASE = "https://api.digitalocean.com/v2"
DO_API_TOKEN = os.getenv("DIGITALOCEAN_API_TOKEN")

# Gradient AI configuration
GRADIENT_API_KEY = os.getenv("GRADIENT_API_KEY") or os.getenv("GRADIENT_AI_MODEL_KEY")
GRADIENT_MODEL = os.getenv("GRADIENT_MODEL") or os.getenv("GRADIENT_AI_MODELNAME", "llama3-8b-instruct")
GRADIENT_BASE_URL = "https://inference.do-ai.run/v1/"

# GitHub configuration (for PR creation)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")


def get_headers() -> Dict[str, str]:
    """Get headers for DigitalOcean API requests"""
    return {
        "Authorization": f"Bearer {DO_API_TOKEN}",
        "Content-Type": "application/json"
    }


def get_gradient_client() -> OpenAI:
    """Get configured Gradient AI client"""
    return OpenAI(
        api_key=GRADIENT_API_KEY,
        base_url=GRADIENT_BASE_URL,
        timeout=120.0,
    )


async def call_gradient_ai(prompt: str, system_prompt: str, temperature: float = 0.7) -> str:
    """Call Gradient AI with given prompts (non-blocking)."""
    def _sync_call():
        client = get_gradient_client()
        response = client.chat.completions.create(
            model=GRADIENT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content

    loop = asyncio.get_event_loop()
    return await asyncio.wait_for(
        loop.run_in_executor(None, _sync_call),
        timeout=90.0,
    )


def fetch_droplet_metrics(droplet_id: str, metric_type: str = "cpu") -> Dict:
    """
    Fetch metrics for a droplet
    
    Args:
        droplet_id: Droplet ID
        metric_type: Type of metric (cpu, memory, disk, network)
        
    Returns:
        Metrics data
    """
    # Calculate time range (last hour)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    
    url = f"{DO_API_BASE}/monitoring/metrics/droplet/{metric_type}"
    
    params = {
        "host_id": droplet_id,
        "start": int(start_time.timestamp()),
        "end": int(end_time.timestamp())
    }
    
    try:
        response = requests.get(url, params=params, headers=get_headers())
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching metrics for droplet {droplet_id}: {e}")
        return {}


def fetch_database_metrics(database_id: str) -> Dict:
    """
    Fetch metrics for a managed database
    
    Args:
        database_id: Database cluster ID
        
    Returns:
        Metrics data
    """
    url = f"{DO_API_BASE}/databases/{database_id}"
    
    try:
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        data = response.json()
        
        # Extract relevant metrics
        db = data.get("database", {})
        return {
            "status": db.get("status"),
            "num_nodes": db.get("num_nodes"),
            "size": db.get("size"),
            "storage_size_mib": db.get("storage_size_mib", 0),
            "db_names": db.get("db_names", [])
        }
    except Exception as e:
        print(f"Error fetching database metrics: {e}")
        return {}


def check_cpu_threshold(metrics: Dict, threshold: float = 80.0) -> Optional[Dict]:
    """
    Check if CPU usage exceeds threshold
    
    Args:
        metrics: CPU metrics data
        threshold: CPU threshold percentage
        
    Returns:
        Alert dict if threshold exceeded, None otherwise
    """
    data = metrics.get("data", {}).get("result", [])
    
    if not data:
        return None
    
    # Get latest value
    values = data[0].get("values", [])
    if not values:
        return None
    
    latest_value = float(values[-1][1])
    
    if latest_value > threshold:
        return {
            "severity": "High" if latest_value > 90 else "Medium",
            "message": f"CPU usage at {latest_value:.1f}% (threshold: {threshold}%)",
            "metric_type": "cpu",
            "metric_value": latest_value,
            "threshold": threshold
        }
    
    return None


def check_storage_threshold(metrics: Dict, threshold: float = 90.0) -> Optional[Dict]:
    """
    Check if storage usage exceeds threshold
    
    Args:
        metrics: Storage metrics data
        threshold: Storage threshold percentage
        
    Returns:
        Alert dict if threshold exceeded, None otherwise
    """
    storage_size = metrics.get("storage_size_mib", 0)
    
    # In production, fetch actual usage from monitoring API
    # For now, simulate with a percentage
    usage_percentage = 75.0  # Placeholder
    
    if usage_percentage > threshold:
        return {
            "severity": "High",
            "message": f"Storage usage at {usage_percentage:.1f}% (threshold: {threshold}%)",
            "metric_type": "storage",
            "metric_value": usage_percentage,
            "threshold": threshold
        }
    
    return None


def check_network_errors(metrics: Dict, threshold: float = 5.0) -> Optional[Dict]:
    """
    Check if network error rate exceeds threshold
    
    Args:
        metrics: Network metrics data
        threshold: Error rate threshold percentage
        
    Returns:
        Alert dict if threshold exceeded, None otherwise
    """
    # In production, calculate error rate from metrics
    error_rate = 2.0  # Placeholder
    
    if error_rate > threshold:
        return {
            "severity": "Medium",
            "message": f"Network error rate at {error_rate:.1f}% (threshold: {threshold}%)",
            "metric_type": "network",
            "metric_value": error_rate,
            "threshold": threshold
        }
    
    return None


async def detect_anomalies(metrics: Dict, resource_type: str) -> List[Dict]:
    """
    Detect anomalies using Gradient AI
    
    Args:
        metrics: Metrics data
        resource_type: Type of resource
        
    Returns:
        List of detected anomalies
    """
    system_prompt = """You are a DevOps expert specializing in infrastructure monitoring and anomaly detection.
Your role is to analyze metrics and identify unusual patterns or potential issues."""
    
    user_prompt = f"""Analyze the following metrics for a {resource_type} and identify any anomalies:

Metrics:
{json.dumps(metrics, indent=2)}

Provide a JSON array of anomalies with the following structure:
[
  {{
    "anomaly": "Description of the anomaly",
    "severity": "High|Medium|Low",
    "recommendation": "Recommended action"
  }}
]

Return ONLY the JSON array, no additional text. If no anomalies detected, return an empty array []."""
    
    try:
        response = await call_gradient_ai(user_prompt, system_prompt, temperature=0.3)
        
        # Parse JSON response
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        anomalies = json.loads(response)
        return anomalies
        
    except Exception as e:
        print(f"Error detecting anomalies: {e}")
        return []


def generate_terraform_fix(alert: Dict, resource_config: Dict) -> str:
    """
    Generate Terraform code to fix the issue
    
    Args:
        alert: Alert details
        resource_config: Current resource configuration
        
    Returns:
        Terraform code for fix
    """
    metric_type = alert.get("metric_type", "")
    resource_type = resource_config.get("type", "")
    resource_name = resource_config.get("name", "resource")
    
    if metric_type == "storage" and resource_type == "digitalocean_database_cluster":
        # Generate storage autoscaling fix
        current_storage = resource_config.get("storage_size_mib", 10240)
        new_storage = int(current_storage * 1.5)  # Increase by 50%
        
        terraform_code = f'''# Auto-generated fix for storage threshold alert
# Alert: {alert.get("message", "")}
# Generated: {datetime.utcnow().isoformat()}

resource "digitalocean_database_cluster" "{resource_name}" {{
  name       = "{resource_name}"
  engine     = "{resource_config.get("engine", "pg")}"
  version    = "{resource_config.get("version", "15")}"
  size       = "{resource_config.get("size", "db-s-1vcpu-2gb")}"
  region     = "{resource_config.get("region", "nyc1")}"
  node_count = {resource_config.get("node_count", 1)}
  
  # Storage increased from {current_storage} MiB to {new_storage} MiB
  storage_size_mib = {new_storage}
}}
'''
        return terraform_code
    
    elif metric_type == "cpu" and resource_type == "digitalocean_droplet":
        # Generate droplet resize fix
        current_size = resource_config.get("size", "s-2vcpu-4gb")
        
        # Size upgrade map
        size_upgrades = {
            "s-1vcpu-1gb": "s-2vcpu-2gb",
            "s-1vcpu-2gb": "s-2vcpu-4gb",
            "s-2vcpu-2gb": "s-2vcpu-4gb",
            "s-2vcpu-4gb": "s-4vcpu-8gb",
            "s-4vcpu-8gb": "s-8vcpu-16gb",
        }
        
        new_size = size_upgrades.get(current_size, "s-4vcpu-8gb")
        
        terraform_code = f'''# Auto-generated fix for CPU threshold alert
# Alert: {alert.get("message", "")}
# Generated: {datetime.utcnow().isoformat()}

resource "digitalocean_droplet" "{resource_name}" {{
  name   = "{resource_name}"
  # Size upgraded from {current_size} to {new_size}
  size   = "{new_size}"
  image  = "{resource_config.get("image", "ubuntu-22-04-x64")}"
  region = "{resource_config.get("region", "nyc1")}"
  tags   = {resource_config.get("tags", [])}
}}
'''
        return terraform_code
    
    else:
        return f"# No automatic fix available for {metric_type} on {resource_type}"


def validate_terraform_fix(terraform_code: str) -> tuple[bool, List[str]]:
    """
    Validate generated Terraform code
    
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
    
    # Check for resource block
    if "resource" not in terraform_code:
        errors.append("No resource block found")
    
    return len(errors) == 0, errors


def create_github_pr(terraform_code: str, alert: Dict, branch_name: str) -> Optional[str]:
    """
    Create GitHub pull request with self-healing changes
    
    Args:
        terraform_code: Terraform code to commit
        alert: Alert that triggered self-healing
        branch_name: Branch name for PR
        
    Returns:
        PR URL if successful, None otherwise
    """
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print("GitHub token or repo not configured")
        return None
    
    try:
        # GitHub API base
        api_base = "https://api.github.com"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get default branch
        repo_url = f"{api_base}/repos/{GITHUB_REPO}"
        response = requests.get(repo_url, headers=headers)
        response.raise_for_status()
        default_branch = response.json().get("default_branch", "main")
        
        # Create branch
        ref_url = f"{api_base}/repos/{GITHUB_REPO}/git/refs"
        ref_response = requests.get(f"{ref_url}/heads/{default_branch}", headers=headers)
        ref_response.raise_for_status()
        sha = ref_response.json().get("object", {}).get("sha")
        
        create_branch_payload = {
            "ref": f"refs/heads/{branch_name}",
            "sha": sha
        }
        requests.post(ref_url, json=create_branch_payload, headers=headers)
        
        # Create/update file
        file_path = "terraform/self_healing_fix.tf"
        content_url = f"{api_base}/repos/{GITHUB_REPO}/contents/{file_path}"
        
        import base64
        encoded_content = base64.b64encode(terraform_code.encode()).decode()
        
        commit_payload = {
            "message": f"Self-healing fix: {alert.get('message', 'Resource threshold exceeded')}",
            "content": encoded_content,
            "branch": branch_name
        }
        
        requests.put(content_url, json=commit_payload, headers=headers)
        
        # Create pull request
        pr_url = f"{api_base}/repos/{GITHUB_REPO}/pulls"
        pr_payload = {
            "title": f"[Self-Healing] Fix for {alert.get('metric_type', 'resource')} threshold",
            "body": f"""## Self-Healing Action

**Alert:** {alert.get('message', '')}
**Severity:** {alert.get('severity', 'Medium')}
**Metric:** {alert.get('metric_type', '')} at {alert.get('metric_value', 0):.1f}%

This PR was automatically generated by the DevOps AI agent to address the alert.

### Changes
- Resource configuration updated to resolve threshold violation
- Terraform code validated before PR creation

### Review Checklist
- [ ] Verify resource sizing is appropriate
- [ ] Check cost implications
- [ ] Approve and merge to apply changes
""",
            "head": branch_name,
            "base": default_branch
        }
        
        pr_response = requests.post(pr_url, json=pr_payload, headers=headers)
        pr_response.raise_for_status()
        
        return pr_response.json().get("html_url")
        
    except Exception as e:
        print(f"Error creating GitHub PR: {e}")
        return None


async def monitor_infrastructure(resources: List[Dict], db_session) -> List[Dict]:
    """
    Monitor infrastructure and create alerts
    
    Args:
        resources: List of resources to monitor
        db_session: Database session for storing alerts
        
    Returns:
        List of created alerts
    """
    alerts = []
    
    for resource in resources:
        resource_type = resource.get("type", "")
        resource_id = resource.get("id", "")
        resource_name = resource.get("name", "")
        
        if resource_type == "digitalocean_droplet":
            # Fetch CPU metrics
            cpu_metrics = fetch_droplet_metrics(resource_id, "cpu")
            cpu_alert = check_cpu_threshold(cpu_metrics)
            
            if cpu_alert:
                cpu_alert["resource_id"] = resource_id
                cpu_alert["resource_name"] = resource_name
                cpu_alert["resource_type"] = resource_type
                alerts.append(cpu_alert)
            
            # Detect anomalies
            anomalies = await detect_anomalies(cpu_metrics, resource_type)
            for anomaly in anomalies:
                alerts.append({
                    "resource_id": resource_id,
                    "resource_name": resource_name,
                    "resource_type": resource_type,
                    "severity": anomaly.get("severity", "Medium"),
                    "message": anomaly.get("anomaly", ""),
                    "metric_type": "anomaly",
                    "recommendation": anomaly.get("recommendation", "")
                })
        
        elif resource_type == "digitalocean_database_cluster":
            # Fetch database metrics
            db_metrics = fetch_database_metrics(resource_id)
            storage_alert = check_storage_threshold(db_metrics, threshold=80.0)
            
            if storage_alert:
                storage_alert["resource_id"] = resource_id
                storage_alert["resource_name"] = resource_name
                storage_alert["resource_type"] = resource_type
                alerts.append(storage_alert)
                
                # Trigger self-healing for storage
                await trigger_self_healing(storage_alert, resource, db_session)
    
    return alerts


async def trigger_self_healing(alert: Dict, resource_config: Dict, db_session) -> Optional[Dict]:
    """
    Trigger self-healing action for an alert
    
    Args:
        alert: Alert details
        resource_config: Resource configuration
        db_session: Database session
        
    Returns:
        Self-healing action details
    """
    metric_type = alert.get("metric_type", "")
    metric_value = alert.get("metric_value", 0)
    
    # Only trigger self-healing for storage > 80%
    if metric_type == "storage" and metric_value > 80.0:
        # Generate Terraform fix
        terraform_code = generate_terraform_fix(alert, resource_config)
        
        # Validate Terraform
        is_valid, errors = validate_terraform_fix(terraform_code)
        
        if not is_valid:
            print(f"Invalid Terraform generated: {errors}")
            return None
        
        # Create GitHub PR
        branch_name = f"self-healing-{resource_config.get('name', 'resource')}-{int(datetime.utcnow().timestamp())}"
        pr_url = create_github_pr(terraform_code, alert, branch_name)
        
        if pr_url:
            # Store self-healing action in database
            action = {
                "alert_id": alert.get("id"),
                "resource_id": alert.get("resource_id"),
                "action_type": "storage_autoscaling",
                "terraform_code": terraform_code,
                "pr_url": pr_url,
                "status": "pending",
                "created_at": datetime.utcnow()
            }
            
            # In production, save to database using db_session
            print(f"Self-healing action created: {pr_url}")
            
            return action
    
    return None


async def monitoring_loop(resources: List[Dict], db_session, interval: int = 300):
    """
    Continuous monitoring loop
    
    Args:
        resources: List of resources to monitor
        db_session: Database session
        interval: Polling interval in seconds (default: 5 minutes)
    """
    while True:
        try:
            alerts = await monitor_infrastructure(resources, db_session)
            
            if alerts:
                print(f"Created {len(alerts)} alerts")
            
            # Wait for next interval
            await asyncio.sleep(interval)
            
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            await asyncio.sleep(interval)
