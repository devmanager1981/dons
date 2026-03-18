"""
Cost Estimator Module

Calculates cost comparison between AWS and DigitalOcean infrastructure.
Provides detailed cost breakdown by resource type and savings analysis.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class CostBreakdown:
    """Cost breakdown by category"""
    compute: float = 0.0
    storage: float = 0.0
    network: float = 0.0
    database: float = 0.0
    kubernetes: float = 0.0
    load_balancer: float = 0.0


@dataclass
class CostComparison:
    """Cost comparison result"""
    aws_monthly_cost: float
    do_monthly_cost: float
    monthly_savings: float
    savings_percentage: float
    aws_breakdown: CostBreakdown
    do_breakdown: CostBreakdown
    annual_savings: float


# AWS Pricing Data (monthly estimates in USD)
AWS_PRICING = {
    # EC2 instances (per month, on-demand pricing)
    "t2.micro": 8.47,
    "t2.small": 16.79,
    "t2.medium": 33.58,
    "t2.large": 67.16,
    "t3.micro": 7.59,
    "t3.small": 15.18,
    "t3.medium": 30.37,
    "t3.large": 60.74,
    "m5.large": 70.08,
    "m5.xlarge": 140.16,
    "m5.2xlarge": 280.32,
    "c5.large": 62.05,
    "c5.xlarge": 124.10,
    "r5.large": 91.98,
    "r5.xlarge": 183.96,
    
    # RDS instances (per month, on-demand pricing)
    "db.t3.micro": 12.41,
    "db.t3.small": 24.82,
    "db.t3.medium": 49.64,
    "db.t3.large": 99.28,
    "db.m5.large": 124.56,
    "db.m5.xlarge": 249.12,
    "db.r5.large": 163.80,
    "db.r5.xlarge": 327.60,
    
    # Storage (per GB per month)
    "ebs_gp3": 0.08,
    "ebs_gp2": 0.10,
    "s3_standard": 0.023,
    "rds_storage": 0.115,
    
    # Network (per GB)
    "data_transfer_out": 0.09,
    
    # EKS
    "eks_cluster": 73.00,  # per cluster per month
    "eks_node_t3_medium": 30.37,  # per node per month
    
    # Load Balancer
    "alb": 22.27,  # per month
    "nlb": 22.27,  # per month
}

# DigitalOcean Pricing Data (monthly estimates in USD)
DO_PRICING = {
    # Droplets (per month)
    "s-1vcpu-512mb-10gb": 4.00,
    "s-1vcpu-1gb": 6.00,
    "s-1vcpu-2gb": 12.00,
    "s-2vcpu-2gb": 18.00,
    "s-2vcpu-4gb": 24.00,
    "s-4vcpu-8gb": 48.00,
    "s-8vcpu-16gb": 96.00,
    "c-2": 42.00,  # CPU-optimized
    "c-4": 84.00,
    "m-2vcpu-16gb": 90.00,  # Memory-optimized
    "m-4vcpu-32gb": 180.00,
    
    # Managed Databases (per month)
    "db-s-1vcpu-1gb": 15.00,
    "db-s-1vcpu-2gb": 30.00,
    "db-s-2vcpu-4gb": 60.00,
    "db-s-4vcpu-8gb": 120.00,
    "db-s-6vcpu-16gb": 240.00,
    
    # Storage (per GB per month)
    "block_storage": 0.10,
    "spaces_storage": 0.02,
    "db_storage": 0.00,  # Included in database pricing
    
    # Network
    "bandwidth": 0.01,  # per GB (after free tier)
    
    # Kubernetes
    "doks_cluster": 0.00,  # Free control plane
    "doks_node_s-2vcpu-4gb": 24.00,  # per node per month
    
    # Load Balancer
    "load_balancer": 12.00,  # per month
}


def get_aws_instance_cost(instance_type: str, count: int = 1) -> float:
    """Get AWS EC2 instance cost"""
    base_type = instance_type.split(".")[0] + "." + instance_type.split(".")[1] if "." in instance_type else instance_type
    return AWS_PRICING.get(base_type, AWS_PRICING.get("t3.medium", 30.37)) * count


def get_do_droplet_cost(size: str, count: int = 1) -> float:
    """Get DigitalOcean Droplet cost"""
    return DO_PRICING.get(size, DO_PRICING.get("s-2vcpu-4gb", 24.00)) * count


def get_aws_rds_cost(instance_class: str, storage_gb: int = 20) -> float:
    """Get AWS RDS cost including instance and storage"""
    instance_cost = AWS_PRICING.get(instance_class, AWS_PRICING.get("db.t3.small", 24.82))
    storage_cost = storage_gb * AWS_PRICING["rds_storage"]
    return instance_cost + storage_cost


def get_do_database_cost(size: str, storage_gb: int = 20) -> float:
    """Get DigitalOcean Managed Database cost (storage included)"""
    return DO_PRICING.get(size, DO_PRICING.get("db-s-1vcpu-2gb", 30.00))


def get_aws_s3_cost(storage_gb: int = 100) -> float:
    """Get AWS S3 cost"""
    return storage_gb * AWS_PRICING["s3_standard"]


def get_do_spaces_cost(storage_gb: int = 100) -> float:
    """Get DigitalOcean Spaces cost"""
    return storage_gb * DO_PRICING["spaces_storage"]


def get_aws_eks_cost(node_count: int = 2, node_type: str = "t3.medium") -> float:
    """Get AWS EKS cost including cluster and nodes"""
    cluster_cost = AWS_PRICING["eks_cluster"]
    node_cost = AWS_PRICING.get(node_type, AWS_PRICING["eks_node_t3_medium"]) * node_count
    return cluster_cost + node_cost


def get_do_doks_cost(node_count: int = 2, node_size: str = "s-2vcpu-4gb") -> float:
    """Get DigitalOcean Kubernetes cost (free control plane)"""
    return DO_PRICING.get(node_size, DO_PRICING["doks_node_s-2vcpu-4gb"]) * node_count


def get_aws_lb_cost() -> float:
    """Get AWS Load Balancer cost"""
    return AWS_PRICING["alb"]


def get_do_lb_cost() -> float:
    """Get DigitalOcean Load Balancer cost"""
    return DO_PRICING["load_balancer"]


def estimate_aws_cost(resources: List[Dict]) -> tuple[float, CostBreakdown]:
    """
    Estimate AWS monthly cost for given resources
    
    Args:
        resources: List of AWS resources with type and configuration
        
    Returns:
        Tuple of (total_cost, cost_breakdown)
    """
    breakdown = CostBreakdown()
    
    for resource in resources:
        resource_type = resource.get("type", "")
        config = resource.get("config", {})
        
        if resource_type == "aws_instance":
            instance_type = config.get("instance_type", "t3.medium")
            count = config.get("count", 1)
            cost = get_aws_instance_cost(instance_type, count)
            breakdown.compute += cost
            
        elif resource_type == "aws_db_instance":
            instance_class = config.get("instance_class", "db.t3.small")
            storage = config.get("allocated_storage", 20)
            cost = get_aws_rds_cost(instance_class, storage)
            breakdown.database += cost
            
        elif resource_type == "aws_s3_bucket":
            # Estimate 100GB per bucket
            storage = config.get("estimated_size_gb", 100)
            cost = get_aws_s3_cost(storage)
            breakdown.storage += cost
            
        elif resource_type == "aws_eks_cluster":
            node_count = config.get("desired_size", 2)
            node_type = config.get("instance_types", ["t3.medium"])[0]
            cost = get_aws_eks_cost(node_count, node_type)
            breakdown.kubernetes += cost
            
        elif resource_type in ["aws_lb", "aws_alb", "aws_elb"]:
            cost = get_aws_lb_cost()
            breakdown.load_balancer += cost
    
    total = (breakdown.compute + breakdown.storage + breakdown.network + 
             breakdown.database + breakdown.kubernetes + breakdown.load_balancer)
    
    return total, breakdown


def estimate_do_cost(resources: List[Dict]) -> tuple[float, CostBreakdown]:
    """
    Estimate DigitalOcean monthly cost for given resources
    
    Args:
        resources: List of DO resources with type and configuration
        
    Returns:
        Tuple of (total_cost, cost_breakdown)
    """
    breakdown = CostBreakdown()
    
    for resource in resources:
        resource_type = resource.get("type", "")
        config = resource.get("config", {})
        
        if resource_type == "digitalocean_droplet":
            size = config.get("size", "s-2vcpu-4gb")
            count = config.get("count", 1)
            cost = get_do_droplet_cost(size, count)
            breakdown.compute += cost
            
        elif resource_type == "digitalocean_database_cluster":
            size = config.get("size", "db-s-1vcpu-2gb")
            cost = get_do_database_cost(size)
            breakdown.database += cost
            
        elif resource_type == "digitalocean_spaces_bucket":
            # Estimate 100GB per bucket
            storage = config.get("estimated_size_gb", 100)
            cost = get_do_spaces_cost(storage)
            breakdown.storage += cost
            
        elif resource_type == "digitalocean_kubernetes_cluster":
            node_count = config.get("node_count", 2)
            node_size = config.get("node_size", "s-2vcpu-4gb")
            cost = get_do_doks_cost(node_count, node_size)
            breakdown.kubernetes += cost
            
        elif resource_type == "digitalocean_loadbalancer":
            cost = get_do_lb_cost()
            breakdown.load_balancer += cost
    
    total = (breakdown.compute + breakdown.storage + breakdown.network + 
             breakdown.database + breakdown.kubernetes + breakdown.load_balancer)
    
    return total, breakdown


def calculate_savings(aws_cost: float, do_cost: float) -> tuple[float, float]:
    """
    Calculate savings from migration
    
    Args:
        aws_cost: AWS monthly cost
        do_cost: DigitalOcean monthly cost
        
    Returns:
        Tuple of (monthly_savings, savings_percentage)
    """
    monthly_savings = aws_cost - do_cost
    savings_percentage = (monthly_savings / aws_cost * 100) if aws_cost > 0 else 0.0
    
    return monthly_savings, savings_percentage


def compare_costs(aws_resources: List[Dict], do_resources: List[Dict]) -> CostComparison:
    """
    Compare costs between AWS and DigitalOcean infrastructure
    
    Args:
        aws_resources: List of AWS resources
        do_resources: List of DigitalOcean resources
        
    Returns:
        CostComparison object with detailed breakdown
    """
    aws_cost, aws_breakdown = estimate_aws_cost(aws_resources)
    do_cost, do_breakdown = estimate_do_cost(do_resources)
    monthly_savings, savings_percentage = calculate_savings(aws_cost, do_cost)
    annual_savings = monthly_savings * 12
    
    return CostComparison(
        aws_monthly_cost=round(aws_cost, 2),
        do_monthly_cost=round(do_cost, 2),
        monthly_savings=round(monthly_savings, 2),
        savings_percentage=round(savings_percentage, 2),
        aws_breakdown=aws_breakdown,
        do_breakdown=do_breakdown,
        annual_savings=round(annual_savings, 2)
    )


# Pricing cache for 24-hour caching
_pricing_cache = {
    "aws": AWS_PRICING.copy(),
    "do": DO_PRICING.copy(),
    "last_updated": datetime.now()
}


def get_cached_pricing() -> Dict:
    """Get cached pricing data (24-hour cache)"""
    global _pricing_cache
    
    # Check if cache is older than 24 hours
    if datetime.now() - _pricing_cache["last_updated"] > timedelta(hours=24):
        # In production, this would fetch updated pricing from APIs
        # For now, we use static pricing
        _pricing_cache["last_updated"] = datetime.now()
    
    return _pricing_cache


def refresh_pricing_cache():
    """Refresh pricing cache (called periodically)"""
    global _pricing_cache
    
    # In production, fetch updated pricing from AWS and DO APIs
    # For now, we use static pricing
    _pricing_cache["aws"] = AWS_PRICING.copy()
    _pricing_cache["do"] = DO_PRICING.copy()
    _pricing_cache["last_updated"] = datetime.now()
