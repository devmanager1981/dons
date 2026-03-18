"""
Cloud Migration Architect AI Agent

Uses Gradient AI to generate intelligent migration plans with risk analysis,
deployment order, rollback procedures, and duration estimates.
"""

import os
import json
import asyncio
from typing import List, Dict, Optional
from openai import OpenAI


# Gradient AI configuration
GRADIENT_API_KEY = os.getenv("GRADIENT_API_KEY") or os.getenv("GRADIENT_AI_MODEL_KEY")
GRADIENT_MODEL = os.getenv("GRADIENT_MODEL") or os.getenv("GRADIENT_AI_MODELNAME", "llama3-8b-instruct")
GRADIENT_BASE_URL = "https://inference.do-ai.run/v1/"


def get_gradient_client() -> OpenAI:
    """Get configured Gradient AI client"""
    return OpenAI(
        api_key=GRADIENT_API_KEY,
        base_url=GRADIENT_BASE_URL,
        timeout=120.0,
    )


async def call_gradient_ai(prompt: str, system_prompt: str, temperature: float = 0.7) -> str:
    """
    Call Gradient AI with given prompts.
    Runs in a thread executor to avoid blocking the event loop.
    """
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


async def analyze_risks(resources: List[Dict], mappings: List[Dict]) -> List[Dict]:
    """
    Analyze migration risks using AI
    
    Args:
        resources: List of AWS resources
        mappings: List of resource mappings
        
    Returns:
        List of risks with severity and mitigation
    """
    system_prompt = """You are a cloud migration expert specializing in AWS to DigitalOcean migrations.
Your role is to identify potential risks and provide mitigation strategies."""
    
    user_prompt = f"""Analyze the following AWS to DigitalOcean migration and identify risks:

AWS Resources:
{json.dumps(resources, indent=2)}

Resource Mappings:
{json.dumps(mappings, indent=2)}

Provide a JSON array of risks with the following structure:
[
  {{
    "risk": "Description of the risk",
    "severity": "High|Medium|Low",
    "impact": "Description of potential impact",
    "mitigation": "Mitigation strategy"
  }}
]

Focus on:
- Data migration risks
- Downtime risks
- Configuration compatibility
- Network connectivity
- Security considerations
- Performance differences

Return ONLY the JSON array, no additional text."""
    
    try:
        response = await call_gradient_ai(user_prompt, system_prompt, temperature=0.3)
        
        # Parse JSON response
        # Remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        risks = json.loads(response)
        return risks
        
    except Exception as e:
        print(f"Error analyzing risks: {e}")
        # Return default risks
        return [
            {
                "risk": "Data migration complexity",
                "severity": "Medium",
                "impact": "Potential data loss or corruption during migration",
                "mitigation": "Perform thorough backup before migration and validate data integrity"
            },
            {
                "risk": "Service downtime",
                "severity": "High",
                "impact": "Application unavailability during migration",
                "mitigation": "Use blue-green deployment strategy with DNS cutover"
            }
        ]


def determine_deployment_order(resources: List[Dict], dependencies: Dict) -> List[str]:
    """
    Determine optimal deployment order based on dependencies
    
    Args:
        resources: List of resources
        dependencies: Resource dependencies map
        
    Returns:
        Ordered list of resource names
    """
    # Build dependency graph
    graph = {}
    for resource in resources:
        name = resource.get("name", "")
        resource_type = resource.get("type", "")
        graph[name] = {
            "type": resource_type,
            "depends_on": dependencies.get(name, [])
        }
    
    # Topological sort
    visited = set()
    order = []
    
    def visit(node):
        if node in visited:
            return
        visited.add(node)
        
        for dep in graph.get(node, {}).get("depends_on", []):
            if dep in graph:
                visit(dep)
        
        order.append(node)
    
    for node in graph:
        visit(node)
    
    return order


def generate_rollback_procedures(resources: List[Dict]) -> List[Dict]:
    """
    Generate rollback procedures for each resource
    
    Args:
        resources: List of resources
        
    Returns:
        List of rollback procedures
    """
    procedures = []
    
    for resource in resources:
        name = resource.get("name", "")
        resource_type = resource.get("type", "")
        
        if resource_type == "digitalocean_droplet":
            procedure = {
                "resource": name,
                "steps": [
                    "1. Stop application traffic to the droplet",
                    "2. Create snapshot of droplet for backup",
                    "3. Delete droplet using DigitalOcean API",
                    "4. Restore AWS EC2 instance from backup if needed"
                ]
            }
        elif resource_type == "digitalocean_database_cluster":
            procedure = {
                "resource": name,
                "steps": [
                    "1. Stop application connections to database",
                    "2. Create final backup of database",
                    "3. Delete database cluster",
                    "4. Restore AWS RDS from backup snapshot"
                ]
            }
        elif resource_type == "digitalocean_spaces_bucket":
            procedure = {
                "resource": name,
                "steps": [
                    "1. Sync data back to AWS S3",
                    "2. Verify data integrity",
                    "3. Delete Spaces bucket",
                    "4. Update application to use S3 endpoint"
                ]
            }
        elif resource_type == "digitalocean_kubernetes_cluster":
            procedure = {
                "resource": name,
                "steps": [
                    "1. Drain all nodes in DOKS cluster",
                    "2. Backup all Kubernetes resources (kubectl get all)",
                    "3. Delete DOKS cluster",
                    "4. Restore EKS cluster and redeploy workloads"
                ]
            }
        elif resource_type == "digitalocean_loadbalancer":
            procedure = {
                "resource": name,
                "steps": [
                    "1. Update DNS to point back to AWS ELB",
                    "2. Wait for DNS propagation (TTL)",
                    "3. Delete DigitalOcean load balancer",
                    "4. Verify traffic routing to AWS"
                ]
            }
        else:
            procedure = {
                "resource": name,
                "steps": [
                    "1. Document current state",
                    "2. Delete resource from DigitalOcean",
                    "3. Restore AWS resource from backup"
                ]
            }
        
        procedures.append(procedure)
    
    return procedures


def estimate_migration_duration(resources: List[Dict]) -> Dict:
    """
    Estimate migration duration based on resource complexity
    
    Args:
        resources: List of resources
        
    Returns:
        Duration estimate with breakdown
    """
    # Base time estimates (in minutes)
    time_estimates = {
        "digitalocean_droplet": 10,
        "digitalocean_database_cluster": 30,
        "digitalocean_spaces_bucket": 20,
        "digitalocean_kubernetes_cluster": 45,
        "digitalocean_loadbalancer": 5,
    }
    
    total_minutes = 0
    breakdown = []
    
    for resource in resources:
        resource_type = resource.get("type", "")
        name = resource.get("name", "")
        
        minutes = time_estimates.get(resource_type, 15)
        total_minutes += minutes
        
        breakdown.append({
            "resource": name,
            "estimated_minutes": minutes
        })
    
    # Add buffer time (20%)
    total_minutes = int(total_minutes * 1.2)
    
    hours = total_minutes // 60
    minutes = total_minutes % 60
    
    return {
        "total_minutes": total_minutes,
        "total_hours": hours,
        "remaining_minutes": minutes,
        "formatted": f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m",
        "breakdown": breakdown
    }


async def generate_migration_plan(
    aws_resources: List[Dict],
    do_resources: List[Dict],
    mappings: List[Dict],
    dependencies: Optional[Dict] = None
) -> Dict:
    """
    Generate comprehensive migration plan using AI
    
    Args:
        aws_resources: List of AWS resources
        do_resources: List of DigitalOcean resources
        mappings: Resource mappings
        dependencies: Resource dependencies
        
    Returns:
        Complete migration plan
    """
    if dependencies is None:
        dependencies = {}
    
    # Generate deployment steps using AI
    system_prompt = """You are a cloud migration architect with expertise in AWS to DigitalOcean migrations.
Your role is to create detailed, step-by-step migration plans that minimize downtime and risk."""
    
    user_prompt = f"""Create a detailed migration plan for the following infrastructure:

AWS Resources:
{json.dumps(aws_resources, indent=2)}

DigitalOcean Resources:
{json.dumps(do_resources, indent=2)}

Resource Mappings:
{json.dumps(mappings, indent=2)}

Provide a JSON array of deployment steps with the following structure:
[
  {{
    "step": 1,
    "title": "Step title",
    "description": "Detailed description",
    "resources": ["resource1", "resource2"],
    "estimated_duration": "15 minutes"
  }}
]

Include steps for:
1. Pre-migration preparation (backups, validation)
2. Resource deployment in correct order
3. Data migration
4. Configuration and testing
5. DNS cutover
6. Post-migration validation

Return ONLY the JSON array, no additional text."""
    
    try:
        response = await call_gradient_ai(user_prompt, system_prompt, temperature=0.5)
        
        # Parse JSON response
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        deployment_steps = json.loads(response)
        
    except Exception as e:
        print(f"Error generating deployment steps: {e}")
        # Return default steps
        deployment_steps = [
            {
                "step": 1,
                "title": "Pre-migration preparation",
                "description": "Create backups of all AWS resources and validate configurations",
                "resources": [r.get("name", "") for r in aws_resources],
                "estimated_duration": "30 minutes"
            },
            {
                "step": 2,
                "title": "Deploy infrastructure",
                "description": "Deploy resources to DigitalOcean in dependency order",
                "resources": [r.get("name", "") for r in do_resources],
                "estimated_duration": "60 minutes"
            },
            {
                "step": 3,
                "title": "Migrate data",
                "description": "Transfer data from AWS to DigitalOcean",
                "resources": [],
                "estimated_duration": "45 minutes"
            },
            {
                "step": 4,
                "title": "Validate and cutover",
                "description": "Test DigitalOcean infrastructure and update DNS",
                "resources": [],
                "estimated_duration": "30 minutes"
            }
        ]
    
    # Analyze risks
    risks = await analyze_risks(aws_resources, mappings)
    
    # Determine deployment order
    deployment_order = determine_deployment_order(do_resources, dependencies)
    
    # Generate rollback procedures
    rollback_procedures = generate_rollback_procedures(do_resources)
    
    # Estimate duration
    duration_estimate = estimate_migration_duration(do_resources)
    
    return {
        "deployment_steps": deployment_steps,
        "deployment_order": deployment_order,
        "risks": risks,
        "rollback_procedures": rollback_procedures,
        "duration_estimate": duration_estimate,
        "total_resources": len(do_resources),
        "migration_strategy": "Blue-green deployment with DNS cutover"
    }


