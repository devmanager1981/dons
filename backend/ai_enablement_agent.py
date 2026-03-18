"""
AI Enablement Agent with RAG Architecture

Analyzes workloads and data schemas to propose RAG architecture using
DigitalOcean Managed OpenSearch and provides AI capability recommendations.
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



def parse_data_schemas(infrastructure: Dict) -> List[Dict]:
    """
    Parse data schemas from infrastructure configuration
    
    Args:
        infrastructure: Parsed infrastructure configuration
        
    Returns:
        List of data schemas found
    """
    schemas = []
    
    resources = infrastructure.get("resources", [])
    
    for resource in resources:
        resource_type = resource.get("type", "")
        config = resource.get("config", {})
        
        if resource_type in ["aws_db_instance", "digitalocean_database_cluster"]:
            # Extract database schema information
            schema = {
                "type": "database",
                "engine": config.get("engine", "unknown"),
                "name": resource.get("name", "database"),
                "estimated_size_gb": config.get("allocated_storage", 20),
                "tables": []  # Would be populated from actual DB inspection
            }
            schemas.append(schema)
        
        elif resource_type in ["aws_s3_bucket", "digitalocean_spaces_bucket"]:
            # Extract object storage schema
            schema = {
                "type": "object_storage",
                "name": resource.get("name", "bucket"),
                "estimated_size_gb": config.get("estimated_size_gb", 100),
                "content_types": ["documents", "images", "logs"]  # Placeholder
            }
            schemas.append(schema)
    
    return schemas


def identify_rag_suitable_data(schemas: List[Dict]) -> List[Dict]:
    """
    Identify data types suitable for RAG implementation
    
    Args:
        schemas: List of data schemas
        
    Returns:
        List of RAG-suitable data sources
    """
    rag_suitable = []
    
    for schema in schemas:
        schema_type = schema.get("type", "")
        
        if schema_type == "database":
            # Databases with text content are suitable for RAG
            rag_suitable.append({
                "source": schema.get("name", ""),
                "type": "structured_data",
                "engine": schema.get("engine", ""),
                "use_case": "Query structured data with natural language",
                "estimated_size_gb": schema.get("estimated_size_gb", 0)
            })
        
        elif schema_type == "object_storage":
            # Object storage with documents is suitable for RAG
            content_types = schema.get("content_types", [])
            if "documents" in content_types or "logs" in content_types:
                rag_suitable.append({
                    "source": schema.get("name", ""),
                    "type": "unstructured_data",
                    "content_types": content_types,
                    "use_case": "Search and analyze documents with semantic search",
                    "estimated_size_gb": schema.get("estimated_size_gb", 0)
                })
    
    return rag_suitable


def analyze_workloads(infrastructure: Dict) -> Dict:
    """
    Analyze workload types from infrastructure
    
    Args:
        infrastructure: Parsed infrastructure configuration
        
    Returns:
        Workload analysis
    """
    resources = infrastructure.get("resources", [])
    
    workload_types = []
    
    # Detect workload patterns
    has_web_servers = any(r.get("type") in ["aws_instance", "digitalocean_droplet"] for r in resources)
    has_databases = any(r.get("type") in ["aws_db_instance", "digitalocean_database_cluster"] for r in resources)
    has_storage = any(r.get("type") in ["aws_s3_bucket", "digitalocean_spaces_bucket"] for r in resources)
    has_kubernetes = any(r.get("type") in ["aws_eks_cluster", "digitalocean_kubernetes_cluster"] for r in resources)
    has_load_balancer = any(r.get("type") in ["aws_lb", "aws_alb", "digitalocean_loadbalancer"] for r in resources)
    
    if has_web_servers and has_databases and has_load_balancer:
        workload_types.append("web_application")
    
    if has_databases and has_storage:
        workload_types.append("data_processing")
    
    if has_kubernetes:
        workload_types.append("microservices")
    
    if has_web_servers and not has_databases:
        workload_types.append("static_website")
    
    if not workload_types:
        workload_types.append("general_purpose")
    
    return {
        "workload_types": workload_types,
        "has_web_servers": has_web_servers,
        "has_databases": has_databases,
        "has_storage": has_storage,
        "has_kubernetes": has_kubernetes,
        "resource_count": len(resources)
    }


def recommend_opensearch_cluster_sizing(data_volume_gb: int) -> Dict:
    """
    Recommend OpenSearch cluster sizing based on data volume
    
    Args:
        data_volume_gb: Total data volume in GB
        
    Returns:
        Cluster sizing recommendation
    """
    # Sizing guidelines
    if data_volume_gb < 50:
        return {
            "node_count": 1,
            "node_size": "db-s-2vcpu-4gb",
            "storage_gb": 100,
            "estimated_cost_monthly": 60.00,
            "rationale": "Small dataset suitable for single-node cluster"
        }
    elif data_volume_gb < 200:
        return {
            "node_count": 2,
            "node_size": "db-s-4vcpu-8gb",
            "storage_gb": 250,
            "estimated_cost_monthly": 240.00,
            "rationale": "Medium dataset with high availability (2 nodes)"
        }
    else:
        return {
            "node_count": 3,
            "node_size": "db-s-6vcpu-16gb",
            "storage_gb": 500,
            "estimated_cost_monthly": 720.00,
            "rationale": "Large dataset with production-grade cluster (3 nodes)"
        }


def generate_sample_embedding_code(schema: Dict) -> str:
    """
    Generate sample code for embedding generation
    
    Args:
        schema: Data schema
        
    Returns:
        Sample Python code
    """
    source_type = schema.get("type", "")
    source_name = schema.get("source", "data")
    
    if source_type == "structured_data":
        code = f'''# Sample code for embedding {source_name} database records

from openai import OpenAI
import psycopg2

# Initialize Gradient AI client
client = OpenAI(
    api_key="YOUR_GRADIENT_API_KEY",
    base_url="https://api.gradient.ai/api/inference/openai"
)

# Connect to database
conn = psycopg2.connect(
    host="your-db-host",
    database="{source_name}",
    user="your-user",
    password="your-password"
)

# Fetch records
cursor = conn.cursor()
cursor.execute("SELECT id, title, description FROM your_table")

# Generate embeddings
for row in cursor.fetchall():
    record_id, title, description = row
    text = f"{{title}} {{description}}"
    
    # Generate embedding using Gradient AI
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    
    embedding = response.data[0].embedding
    
    # Store embedding in OpenSearch
    # (OpenSearch client code here)
    print(f"Generated embedding for record {{record_id}}")
'''
    
    elif source_type == "unstructured_data":
        code = f'''# Sample code for embedding {source_name} documents

from openai import OpenAI
import boto3
from botocore.client import Config

# Initialize Gradient AI client
client = OpenAI(
    api_key="YOUR_GRADIENT_API_KEY",
    base_url="https://api.gradient.ai/api/inference/openai"
)

# Initialize Spaces client
s3 = boto3.client(
    's3',
    endpoint_url='https://nyc3.digitaloceanspaces.com',
    aws_access_key_id='YOUR_SPACES_KEY',
    aws_secret_access_key='YOUR_SPACES_SECRET',
    config=Config(signature_version='s3v4')
)

# List objects in bucket
response = s3.list_objects_v2(Bucket='{source_name}')

# Process each document
for obj in response.get('Contents', []):
    key = obj['Key']
    
    # Download document
    file_obj = s3.get_object(Bucket='{source_name}', Key=key)
    content = file_obj['Body'].read().decode('utf-8')
    
    # Generate embedding
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=content[:8000]  # Truncate to token limit
    )
    
    embedding = response.data[0].embedding
    
    # Store embedding in OpenSearch
    # (OpenSearch client code here)
    print(f"Generated embedding for {{key}}")
'''
    
    else:
        code = "# No sample code available for this data type"
    
    return code


async def propose_rag_architecture(
    rag_suitable_data: List[Dict],
    workload_analysis: Dict
) -> Dict:
    """
    Propose RAG architecture using Gradient AI
    
    Args:
        rag_suitable_data: List of RAG-suitable data sources
        workload_analysis: Workload analysis results
        
    Returns:
        RAG architecture proposal
    """
    system_prompt = """You are an AI architecture expert specializing in RAG (Retrieval-Augmented Generation) systems.
Your role is to design RAG architectures using DigitalOcean Managed OpenSearch for vector storage."""
    
    user_prompt = f"""Design a RAG architecture for the following workload:

Workload Analysis:
{json.dumps(workload_analysis, indent=2)}

RAG-Suitable Data Sources:
{json.dumps(rag_suitable_data, indent=2)}

Provide a JSON object with the following structure:
{{
  "architecture_overview": "High-level description of the RAG system",
  "components": [
    {{
      "name": "Component name",
      "description": "Component description",
      "technology": "Technology to use"
    }}
  ],
  "data_flow": "Description of how data flows through the system",
  "opensearch_configuration": {{
    "index_strategy": "How to structure OpenSearch indices",
    "mapping_configuration": "Field mappings for vector embeddings",
    "query_strategy": "How to query for relevant documents"
  }},
  "implementation_steps": [
    "Step 1",
    "Step 2"
  ]
}}

Focus on:
- Using DigitalOcean Managed OpenSearch for vector storage
- Using Gradient AI for embeddings and completions
- Scalable architecture for production use
- Cost-effective design

Return ONLY the JSON object, no additional text."""
    
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
        
        architecture = json.loads(response)
        
        # Calculate total data volume
        total_data_gb = sum(d.get("estimated_size_gb", 0) for d in rag_suitable_data)
        
        # Add OpenSearch cluster sizing
        cluster_sizing = recommend_opensearch_cluster_sizing(total_data_gb)
        architecture["opensearch_cluster_sizing"] = cluster_sizing
        
        # Add sample code for each data source
        architecture["sample_code"] = {}
        for data_source in rag_suitable_data:
            source_name = data_source.get("source", "")
            architecture["sample_code"][source_name] = generate_sample_embedding_code(data_source)
        
        return architecture
        
    except Exception as e:
        print(f"Error proposing RAG architecture: {e}")
        # Return default architecture
        return {
            "architecture_overview": "RAG system using DigitalOcean Managed OpenSearch and Gradient AI",
            "components": [
                {
                    "name": "Data Ingestion",
                    "description": "Extract and process data from sources",
                    "technology": "Python scripts"
                },
                {
                    "name": "Embedding Generation",
                    "description": "Generate vector embeddings using Gradient AI",
                    "technology": "Gradient AI text-embedding-ada-002"
                },
                {
                    "name": "Vector Storage",
                    "description": "Store embeddings in OpenSearch",
                    "technology": "DigitalOcean Managed OpenSearch"
                },
                {
                    "name": "Query Interface",
                    "description": "Accept user queries and retrieve relevant documents",
                    "technology": "FastAPI"
                },
                {
                    "name": "Response Generation",
                    "description": "Generate responses using retrieved context",
                    "technology": "Gradient AI GPT-4"
                }
            ],
            "data_flow": "User query → Embedding → OpenSearch similarity search → Context retrieval → Gradient AI completion → Response",
            "opensearch_configuration": {
                "index_strategy": "One index per data source with vector field",
                "mapping_configuration": "Use knn_vector field type with dimension 1536",
                "query_strategy": "Use kNN search with cosine similarity"
            },
            "implementation_steps": [
                "1. Set up DigitalOcean Managed OpenSearch cluster",
                "2. Create indices with vector field mappings",
                "3. Implement data ingestion pipeline",
                "4. Generate and store embeddings",
                "5. Build query API with FastAPI",
                "6. Integrate Gradient AI for completions"
            ]
        }


async def recommend_ai_capabilities(workload_analysis: Dict, infrastructure: Dict) -> List[Dict]:
    """
    Recommend AI capabilities for the workload
    
    Args:
        workload_analysis: Workload analysis results
        infrastructure: Infrastructure configuration
        
    Returns:
        List of AI capability recommendations
    """
    system_prompt = """You are an AI consultant specializing in identifying AI opportunities for businesses.
Your role is to recommend practical AI capabilities that add business value."""
    
    user_prompt = f"""Recommend AI capabilities for the following workload:

Workload Analysis:
{json.dumps(workload_analysis, indent=2)}

Infrastructure:
{json.dumps(infrastructure, indent=2)}

Provide a JSON array of recommendations with the following structure:
[
  {{
    "capability": "AI capability name",
    "description": "What this capability does",
    "business_value": "Business value and ROI",
    "implementation_complexity": "Low|Medium|High",
    "priority": "High|Medium|Low",
    "use_cases": ["Use case 1", "Use case 2"]
  }}
]

Focus on:
- Practical AI capabilities using Gradient AI
- Clear business value
- Realistic implementation

Return ONLY the JSON array, no additional text."""
    
    try:
        response = await call_gradient_ai(user_prompt, system_prompt, temperature=0.6)
        
        # Parse JSON response
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        recommendations = json.loads(response)
        
        # Prioritize recommendations
        return prioritize_recommendations(recommendations)
        
    except Exception as e:
        print(f"Error recommending AI capabilities: {e}")
        # Return default recommendations
        return [
            {
                "capability": "Intelligent Search",
                "description": "Semantic search across your data using RAG",
                "business_value": "Improve user experience and reduce search time by 60%",
                "implementation_complexity": "Medium",
                "priority": "High",
                "use_cases": ["Document search", "Product search", "Knowledge base"]
            },
            {
                "capability": "Automated Support",
                "description": "AI-powered chatbot for customer support",
                "business_value": "Reduce support costs by 40% and improve response time",
                "implementation_complexity": "Medium",
                "priority": "High",
                "use_cases": ["Customer support", "FAQ automation", "Ticket triage"]
            }
        ]


def prioritize_recommendations(recommendations: List[Dict]) -> List[Dict]:
    """
    Prioritize recommendations by business value
    
    Args:
        recommendations: List of recommendations
        
    Returns:
        Prioritized list
    """
    priority_order = {"High": 1, "Medium": 2, "Low": 3}
    
    return sorted(
        recommendations,
        key=lambda r: (
            priority_order.get(r.get("priority", "Medium"), 2),
            r.get("implementation_complexity", "Medium")
        )
    )


async def generate_implementation_guide(recommendation: Dict) -> str:
    """
    Generate implementation guide for a recommendation
    
    Args:
        recommendation: AI capability recommendation
        
    Returns:
        Implementation guide with code examples
    """
    capability = recommendation.get("capability", "")
    
    guide = f"""# Implementation Guide: {capability}

## Overview
{recommendation.get("description", "")}

## Business Value
{recommendation.get("business_value", "")}

## Implementation Steps

### 1. Set up Gradient AI
```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_GRADIENT_API_KEY",
    base_url="https://api.gradient.ai/api/inference/openai"
)
```

### 2. Implement Core Functionality
```python
# Example implementation
def {capability.lower().replace(" ", "_")}(user_input: str) -> str:
    response = client.chat.completions.create(
        model="openai-gpt-4o-mini",
        messages=[
            {{"role": "system", "content": "You are a helpful assistant."}},
            {{"role": "user", "content": user_input}}
        ]
    )
    return response.choices[0].message.content
```

### 3. Deploy to DigitalOcean App Platform
```yaml
# app.yaml
name: {capability.lower().replace(" ", "-")}
services:
  - name: api
    source_dir: /
    github:
      repo: your-repo
      branch: main
    run_command: uvicorn main:app --host 0.0.0.0 --port 8080
    envs:
      - key: GRADIENT_API_KEY
        scope: RUN_TIME
        type: SECRET
```

## Use Cases
{chr(10).join([f"- {uc}" for uc in recommendation.get("use_cases", [])])}

## Estimated Timeline
- Setup: 1-2 days
- Development: 1-2 weeks
- Testing: 3-5 days
- Deployment: 1 day

## Cost Estimate
- Gradient AI: $50-200/month (depending on usage)
- DigitalOcean App Platform: $12-48/month
- Total: $62-248/month
"""
    
    return guide
