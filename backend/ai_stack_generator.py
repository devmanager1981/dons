"""
AI Stack Terraform Generator

Generates Terraform configuration for the three AI agents:
1. Cloud Migration Architect Agent
2. DevOps Agent  
3. AI Enablement Agent

Includes Gradient AI integration, Managed OpenSearch for RAG, and App Platform deployment.
"""

from typing import List, Dict, Optional


def generate_ai_stack_variables() -> str:
    """Generate variables for AI stack"""
    return '''# AI Stack Variables
variable "gradient_api_key" {
  description = "DigitalOcean Gradient AI API key"
  type        = string
  sensitive   = true
}

variable "github_token" {
  description = "GitHub token for self-healing PRs (optional)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "enable_ai_stack" {
  description = "Enable AI agent stack deployment"
  type        = bool
  default     = true
}

variable "opensearch_size" {
  description = "OpenSearch cluster size for RAG vector storage"
  type        = string
  default     = "db-s-2vcpu-4gb"
}
'''


def generate_opensearch_cluster() -> str:
    """Generate Managed OpenSearch cluster for RAG vector storage"""
    return '''# Managed OpenSearch for RAG Vector Storage
resource "digitalocean_database_cluster" "rag_vector_store" {
  count = var.enable_ai_stack ? 1 : 0
  
  name       = "rag-vector-store"
  engine     = "opensearch"
  version    = "2"
  size       = var.opensearch_size
  region     = var.region
  node_count = 1
  
  # Storage autoscaling for growing vector data
  storage_size_mib = 20480  # 20 GB initial
  
  tags = ["dons", "ai-stack", "rag", "vector-store"]
}

# OpenSearch connection info output
output "opensearch_cluster_id" {
  description = "OpenSearch cluster ID for RAG"
  value       = var.enable_ai_stack ? digitalocean_database_cluster.rag_vector_store[0].id : null
}

output "opensearch_uri" {
  description = "OpenSearch connection URI"
  value       = var.enable_ai_stack ? digitalocean_database_cluster.rag_vector_store[0].uri : null
  sensitive   = true
}

output "opensearch_host" {
  description = "OpenSearch host"
  value       = var.enable_ai_stack ? digitalocean_database_cluster.rag_vector_store[0].host : null
}

output "opensearch_port" {
  description = "OpenSearch port"
  value       = var.enable_ai_stack ? digitalocean_database_cluster.rag_vector_store[0].port : null
}
'''


def generate_knowledge_base_bucket() -> str:
    """Generate Spaces bucket for Knowledge Base documents"""
    return '''# Spaces Bucket for Knowledge Base Documents
resource "digitalocean_spaces_bucket" "knowledge_base" {
  count = var.enable_ai_stack ? 1 : 0
  
  name   = "dons-knowledge-base"
  region = var.region
  acl    = "private"
  
  # Enable versioning for document history
  versioning {
    enabled = true
  }
  
  # Lifecycle rules for old document versions
  lifecycle_rule {
    enabled = true
    
    noncurrent_version_expiration {
      days = 90
    }
  }
}

output "knowledge_base_bucket_name" {
  description = "Knowledge Base Spaces bucket name"
  value       = var.enable_ai_stack ? digitalocean_spaces_bucket.knowledge_base[0].name : null
}

output "knowledge_base_bucket_endpoint" {
  description = "Knowledge Base bucket endpoint"
  value       = var.enable_ai_stack ? "https://${digitalocean_spaces_bucket.knowledge_base[0].name}.${var.region}.digitaloceanspaces.com" : null
}
'''


def generate_migration_architect_agent() -> str:
    """Generate Cloud Migration Architect Agent on App Platform"""
    return '''# Cloud Migration Architect Agent
resource "digitalocean_app" "migration_architect_agent" {
  count = var.enable_ai_stack ? 1 : 0
  
  spec {
    name   = "migration-architect-agent"
    region = var.region
    
    # Agent API Service
    service {
      name               = "architect-api"
      instance_count     = 1
      instance_size_slug = "basic-xxs"
      
      github {
        repo           = var.github_repo
        branch         = var.github_branch
        deploy_on_push = true
      }
      
      source_dir = "/backend"
      
      # Run command for the agent
      run_command = "uvicorn cloud_migration_architect:app --host 0.0.0.0 --port 8080"
      
      # Environment variables
      env {
        key   = "AGENT_TYPE"
        value = "migration_architect"
      }
      
      env {
        key   = "GRADIENT_API_KEY"
        value = var.gradient_api_key
        type  = "SECRET"
      }
      
      env {
        key   = "GRADIENT_MODEL"
        value = "llama3-8b-instruct"
      }
      
      env {
        key   = "OPENSEARCH_HOST"
        value = var.enable_ai_stack ? digitalocean_database_cluster.rag_vector_store[0].host : ""
      }
      
      env {
        key   = "OPENSEARCH_PORT"
        value = var.enable_ai_stack ? tostring(digitalocean_database_cluster.rag_vector_store[0].port) : "443"
      }
      
      env {
        key   = "OPENSEARCH_USER"
        value = var.enable_ai_stack ? digitalocean_database_cluster.rag_vector_store[0].user : ""
      }
      
      env {
        key   = "OPENSEARCH_PASSWORD"
        value = var.enable_ai_stack ? digitalocean_database_cluster.rag_vector_store[0].password : ""
        type  = "SECRET"
      }
      
      # Health check
      health_check {
        http_path             = "/health"
        initial_delay_seconds = 30
        period_seconds        = 10
        timeout_seconds       = 5
        success_threshold     = 1
        failure_threshold     = 3
      }
      
      # HTTP port
      http_port = 8080
    }
  }
}

output "migration_architect_url" {
  description = "Cloud Migration Architect Agent URL"
  value       = var.enable_ai_stack ? digitalocean_app.migration_architect_agent[0].live_url : null
}
'''


def generate_devops_agent() -> str:
    """Generate DevOps Agent with self-healing capabilities"""
    return '''# DevOps Agent with Self-Healing
resource "digitalocean_app" "devops_agent" {
  count = var.enable_ai_stack ? 1 : 0
  
  spec {
    name   = "devops-agent"
    region = var.region
    
    # Agent API Service
    service {
      name               = "devops-api"
      instance_count     = 1
      instance_size_slug = "basic-xxs"
      
      github {
        repo           = var.github_repo
        branch         = var.github_branch
        deploy_on_push = true
      }
      
      source_dir = "/backend"
      
      # Run command for the agent
      run_command = "uvicorn devops_agent:app --host 0.0.0.0 --port 8080"
      
      # Environment variables
      env {
        key   = "AGENT_TYPE"
        value = "devops"
      }
      
      env {
        key   = "GRADIENT_API_KEY"
        value = var.gradient_api_key
        type  = "SECRET"
      }
      
      env {
        key   = "GRADIENT_MODEL"
        value = "llama3-8b-instruct"
      }
      
      env {
        key   = "GITHUB_TOKEN"
        value = var.github_token
        type  = "SECRET"
      }
      
      env {
        key   = "DIGITALOCEAN_API_TOKEN"
        value = var.do_token
        type  = "SECRET"
      }
      
      env {
        key   = "MONITORING_INTERVAL"
        value = "300"  # 5 minutes
      }
      
      # Health check
      health_check {
        http_path             = "/health"
        initial_delay_seconds = 30
        period_seconds        = 10
        timeout_seconds       = 5
        success_threshold     = 1
        failure_threshold     = 3
      }
      
      # HTTP port
      http_port = 8080
    }
    
    # Background worker for monitoring
    worker {
      name               = "monitor-worker"
      instance_count     = 1
      instance_size_slug = "basic-xxs"
      
      github {
        repo           = var.github_repo
        branch         = var.github_branch
        deploy_on_push = true
      }
      
      source_dir = "/backend"
      
      # Run monitoring worker
      run_command = "python devops_agent.py --mode monitor"
      
      # Same environment variables as service
      env {
        key   = "AGENT_TYPE"
        value = "devops_monitor"
      }
      
      env {
        key   = "GRADIENT_API_KEY"
        value = var.gradient_api_key
        type  = "SECRET"
      }
      
      env {
        key   = "GITHUB_TOKEN"
        value = var.github_token
        type  = "SECRET"
      }
      
      env {
        key   = "DIGITALOCEAN_API_TOKEN"
        value = var.do_token
        type  = "SECRET"
      }
    }
  }
}

output "devops_agent_url" {
  description = "DevOps Agent URL"
  value       = var.enable_ai_stack ? digitalocean_app.devops_agent[0].live_url : null
}
'''


def generate_ai_enablement_agent() -> str:
    """Generate AI Enablement Agent for RAG recommendations"""
    return '''# AI Enablement Agent
resource "digitalocean_app" "ai_enablement_agent" {
  count = var.enable_ai_stack ? 1 : 0
  
  spec {
    name   = "ai-enablement-agent"
    region = var.region
    
    # Agent API Service
    service {
      name               = "enablement-api"
      instance_count     = 1
      instance_size_slug = "basic-xxs"
      
      github {
        repo           = var.github_repo
        branch         = var.github_branch
        deploy_on_push = true
      }
      
      source_dir = "/backend"
      
      # Run command for the agent
      run_command = "uvicorn ai_enablement_agent:app --host 0.0.0.0 --port 8080"
      
      # Environment variables
      env {
        key   = "AGENT_TYPE"
        value = "ai_enablement"
      }
      
      env {
        key   = "GRADIENT_API_KEY"
        value = var.gradient_api_key
        type  = "SECRET"
      }
      
      env {
        key   = "GRADIENT_MODEL"
        value = "llama3-8b-instruct"
      }
      
      env {
        key   = "OPENSEARCH_HOST"
        value = var.enable_ai_stack ? digitalocean_database_cluster.rag_vector_store[0].host : ""
      }
      
      env {
        key   = "OPENSEARCH_PORT"
        value = var.enable_ai_stack ? tostring(digitalocean_database_cluster.rag_vector_store[0].port) : "443"
      }
      
      env {
        key   = "OPENSEARCH_USER"
        value = var.enable_ai_stack ? digitalocean_database_cluster.rag_vector_store[0].user : ""
      }
      
      env {
        key   = "OPENSEARCH_PASSWORD"
        value = var.enable_ai_stack ? digitalocean_database_cluster.rag_vector_store[0].password : ""
        type  = "SECRET"
      }
      
      env {
        key   = "KNOWLEDGE_BASE_BUCKET"
        value = var.enable_ai_stack ? digitalocean_spaces_bucket.knowledge_base[0].name : ""
      }
      
      env {
        key   = "SPACES_ACCESS_KEY"
        value = var.spaces_access_key
        type  = "SECRET"
      }
      
      env {
        key   = "SPACES_SECRET_KEY"
        value = var.spaces_secret_key
        type  = "SECRET"
      }
      
      # Health check
      health_check {
        http_path             = "/health"
        initial_delay_seconds = 30
        period_seconds        = 10
        timeout_seconds       = 5
        success_threshold     = 1
        failure_threshold     = 3
      }
      
      # HTTP port
      http_port = 8080
    }
  }
}

output "ai_enablement_agent_url" {
  description = "AI Enablement Agent URL"
  value       = var.enable_ai_stack ? digitalocean_app.ai_enablement_agent[0].live_url : null
}
'''


def generate_ai_stack_outputs() -> str:
    """Generate comprehensive outputs for AI stack"""
    return '''# AI Stack Summary Outputs
output "ai_stack_enabled" {
  description = "Whether AI stack is enabled"
  value       = var.enable_ai_stack
}

output "ai_agents" {
  description = "AI Agent endpoints"
  value = var.enable_ai_stack ? {
    migration_architect = digitalocean_app.migration_architect_agent[0].live_url
    devops             = digitalocean_app.devops_agent[0].live_url
    ai_enablement      = digitalocean_app.ai_enablement_agent[0].live_url
  } : {}
}

output "rag_infrastructure" {
  description = "RAG infrastructure details"
  value = var.enable_ai_stack ? {
    opensearch_cluster_id = digitalocean_database_cluster.rag_vector_store[0].id
    opensearch_host       = digitalocean_database_cluster.rag_vector_store[0].host
    knowledge_base_bucket = digitalocean_spaces_bucket.knowledge_base[0].name
  } : {}
}

output "ai_stack_cost_estimate" {
  description = "Estimated monthly cost for AI stack"
  value = var.enable_ai_stack ? {
    opensearch_cluster = "$60-120/month"
    app_platform_agents = "$36/month (3 agents x $12)"
    knowledge_base_storage = "$5/month"
    total_estimated = "$101-161/month"
  } : {}
}
'''


def generate_ai_stack_readme() -> str:
    """Generate README for AI stack usage"""
    return '''# AI Stack Configuration

## Overview

This Terraform configuration deploys the DONS AI Agent Stack:

1. **Cloud Migration Architect Agent** - Generates migration plans with risk analysis
2. **DevOps Agent** - Monitors infrastructure with self-healing capabilities  
3. **AI Enablement Agent** - Proposes RAG architecture and AI capabilities

## Infrastructure Components

- **Managed OpenSearch** - Vector storage for RAG (Retrieval-Augmented Generation)
- **Spaces Bucket** - Knowledge Base document storage
- **App Platform** - Serverless deployment for all three agents

## Prerequisites

1. DigitalOcean API token
2. Gradient AI API key (get from https://cloud.digitalocean.com/gradient-ai)
3. GitHub repository with agent code
4. GitHub token (for self-healing PRs)

## Usage

### Enable AI Stack

```hcl
variable "enable_ai_stack" {
  default = true
}

variable "gradient_api_key" {
  default = "your-gradient-api-key"
}

variable "github_token" {
  default = "your-github-token"
}
```

### Deploy

```bash
terraform init
terraform plan
terraform apply
```

### Access Agents

After deployment, get agent URLs:

```bash
terraform output ai_agents
```

## Cost Breakdown

| Component | Monthly Cost |
|-----------|-------------|
| OpenSearch Cluster (1 node) | $60-120 |
| App Platform (3 agents) | $36 |
| Knowledge Base Storage | $5 |
| **Total** | **$101-161** |

## Agent Endpoints

### Migration Architect Agent
- **URL**: `https://migration-architect-agent-xxxxx.ondigitalocean.app`
- **Purpose**: Generate migration plans, risk analysis, deployment strategies
- **API**: POST `/api/generate-plan`

### DevOps Agent
- **URL**: `https://devops-agent-xxxxx.ondigitalocean.app`
- **Purpose**: Monitor infrastructure, create self-healing PRs
- **API**: GET `/api/alerts`, POST `/api/heal`

### AI Enablement Agent
- **URL**: `https://ai-enablement-agent-xxxxx.ondigitalocean.app`
- **Purpose**: Propose RAG architecture, AI capability recommendations
- **API**: POST `/api/propose-rag`, GET `/api/recommendations`

## Knowledge Base Setup

1. Upload documents to the Knowledge Base bucket:
   ```bash
   aws s3 cp docs/ s3://dons-knowledge-base/ --recursive \\
     --endpoint-url=https://nyc3.digitaloceanspaces.com
   ```

2. Documents are automatically indexed in OpenSearch

3. Agents use RAG to answer questions based on your documents

## Self-Healing Configuration

The DevOps Agent monitors:
- CPU usage > 80%
- Memory usage > 85%
- Disk usage > 80%
- Database storage > 80%

When thresholds are exceeded, it automatically:
1. Creates a GitHub PR with Terraform fix
2. Notifies via webhook
3. Applies fix after approval

## Disable AI Stack

To save costs during development:

```hcl
variable "enable_ai_stack" {
  default = false
}
```

This will skip AI stack deployment while keeping base infrastructure.

## Troubleshooting

### Agents not starting
- Check Gradient AI API key is valid
- Verify GitHub repository is accessible
- Check App Platform logs: `doctl apps logs <app-id>`

### OpenSearch connection failed
- Verify OpenSearch cluster is active
- Check firewall rules allow agent IPs
- Verify credentials in agent environment variables

### Knowledge Base not working
- Ensure Spaces bucket exists
- Verify Spaces credentials are correct
- Check documents are uploaded to bucket

## Support

For issues:
- Check agent logs in App Platform console
- Review OpenSearch cluster status
- Verify all environment variables are set correctly
'''


def generate_complete_ai_stack_terraform(
    region: str = "nyc1",
    github_repo: str = "",
    github_branch: str = "main"
) -> str:
    """
    Generate complete AI stack Terraform configuration
    
    Args:
        region: DigitalOcean region
        github_repo: GitHub repository for agent code
        github_branch: GitHub branch to deploy
        
    Returns:
        Complete Terraform configuration for AI stack
    """
    # Additional variables needed
    additional_vars = f'''
variable "region" {{
  description = "DigitalOcean region"
  type        = string
  default     = "{region}"
}}

variable "github_repo" {{
  description = "GitHub repository for agent code"
  type        = string
  default     = "{github_repo}"
}}

variable "github_branch" {{
  description = "GitHub branch to deploy"
  type        = string
  default     = "{github_branch}"
}}

variable "spaces_access_key" {{
  description = "Spaces access key"
  type        = string
  sensitive   = true
}}

variable "spaces_secret_key" {{
  description = "Spaces secret key"
  type        = string
  sensitive   = true
}}
'''
    
    # Combine all sections
    terraform_code = f"""# DONS AI Agent Stack
# Generated by DONS Platform
# 
# This configuration deploys three AI agents:
# 1. Cloud Migration Architect - Migration planning and risk analysis
# 2. DevOps Agent - Infrastructure monitoring and self-healing
# 3. AI Enablement Agent - RAG architecture and AI recommendations

{generate_ai_stack_variables()}

{additional_vars}

{generate_opensearch_cluster()}

{generate_knowledge_base_bucket()}

{generate_migration_architect_agent()}

{generate_devops_agent()}

{generate_ai_enablement_agent()}

{generate_ai_stack_outputs()}
"""
    
    return terraform_code


def format_ai_stack_terraform(terraform_code: str) -> str:
    """Format AI stack Terraform code"""
    # Remove multiple consecutive blank lines
    lines = terraform_code.split("\n")
    result = []
    prev_blank = False
    
    for line in lines:
        if line.strip() == "":
            if not prev_blank:
                result.append(line)
            prev_blank = True
        else:
            result.append(line)
            prev_blank = False
    
    return "\n".join(result)
