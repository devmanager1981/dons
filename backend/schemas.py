"""
Pydantic Schemas for API Request/Response Models

Defines all data models for API contracts with validation rules.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


# Upload Schemas
class UploadResponse(BaseModel):
    """Response for file upload"""
    upload_id: str = Field(..., description="Unique upload identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    file_url: str = Field(..., description="URL to uploaded file in Spaces")
    upload_timestamp: datetime = Field(..., description="Upload timestamp")
    status: str = Field(default="uploaded", description="Upload status")


# Analysis Schemas
class ParsedResource(BaseModel):
    """Parsed infrastructure resource"""
    type: str = Field(..., description="Resource type")
    name: str = Field(..., description="Resource name")
    config: Dict[str, Any] = Field(..., description="Resource configuration")
    dependencies: List[str] = Field(default_factory=list, description="Resource dependencies")


class ParseError(BaseModel):
    """Parse error details"""
    line: Optional[int] = Field(None, description="Line number where error occurred")
    message: str = Field(..., description="Error message")
    file: str = Field(..., description="File where error occurred")


class AnalyzeResponse(BaseModel):
    """Response for infrastructure analysis"""
    upload_id: str = Field(..., description="Upload identifier")
    resources_detected: int = Field(..., description="Number of resources detected")
    resources: List[ParsedResource] = Field(..., description="Parsed resources")
    parse_errors: List[ParseError] = Field(default_factory=list, description="Parse errors if any")
    unsupported_resources: List[str] = Field(default_factory=list, description="Unsupported resource types")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")


# Migration Plan Schemas
class DeploymentStep(BaseModel):
    """Migration deployment step"""
    step: int = Field(..., description="Step number")
    title: str = Field(..., description="Step title")
    description: str = Field(..., description="Step description")
    resources: List[str] = Field(..., description="Resources involved in this step")
    estimated_duration: str = Field(..., description="Estimated duration")


class Risk(BaseModel):
    """Migration risk"""
    risk: str = Field(..., description="Risk description")
    severity: str = Field(..., description="Risk severity: High, Medium, Low")
    impact: str = Field(..., description="Potential impact")
    mitigation: str = Field(..., description="Mitigation strategy")


class RollbackProcedure(BaseModel):
    """Rollback procedure for a resource"""
    resource: str = Field(..., description="Resource name")
    steps: List[str] = Field(..., description="Rollback steps")


class DurationEstimate(BaseModel):
    """Migration duration estimate"""
    total_minutes: int = Field(..., description="Total minutes")
    total_hours: int = Field(..., description="Total hours")
    remaining_minutes: int = Field(..., description="Remaining minutes after hours")
    formatted: str = Field(..., description="Formatted duration string")
    breakdown: List[Dict[str, Any]] = Field(..., description="Duration breakdown by resource")


class MigrationPlanSchema(BaseModel):
    """Complete migration plan"""
    plan_id: str = Field(..., description="Migration plan identifier")
    deployment_steps: List[DeploymentStep] = Field(..., description="Deployment steps")
    deployment_order: List[str] = Field(..., description="Ordered list of resource names")
    risks: List[Risk] = Field(..., description="Identified risks")
    rollback_procedures: List[RollbackProcedure] = Field(..., description="Rollback procedures")
    duration_estimate: DurationEstimate = Field(..., description="Duration estimate")
    total_resources: int = Field(..., description="Total number of resources")
    migration_strategy: str = Field(..., description="Migration strategy")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Plan creation timestamp")


# Cost Comparison Schemas
class CostBreakdownSchema(BaseModel):
    """Cost breakdown by category"""
    compute: float = Field(default=0.0, description="Compute costs")
    storage: float = Field(default=0.0, description="Storage costs")
    network: float = Field(default=0.0, description="Network costs")
    database: float = Field(default=0.0, description="Database costs")
    kubernetes: float = Field(default=0.0, description="Kubernetes costs")
    load_balancer: float = Field(default=0.0, description="Load balancer costs")


class CostComparisonSchema(BaseModel):
    """Cost comparison between AWS and DigitalOcean"""
    aws_monthly_cost: float = Field(..., description="AWS monthly cost in USD")
    do_monthly_cost: float = Field(..., description="DigitalOcean monthly cost in USD")
    monthly_savings: float = Field(..., description="Monthly savings in USD")
    savings_percentage: float = Field(..., description="Savings percentage")
    aws_breakdown: CostBreakdownSchema = Field(..., description="AWS cost breakdown")
    do_breakdown: CostBreakdownSchema = Field(..., description="DO cost breakdown")
    annual_savings: float = Field(..., description="Annual savings in USD")


# ROI Report Schemas
class ROIReportSchema(BaseModel):
    """One-click ROI report"""
    monthly_savings: float = Field(..., description="Monthly savings in USD")
    annual_savings: float = Field(..., description="Annual savings in USD")
    savings_percentage: float = Field(..., description="Savings percentage")
    aws_monthly_cost: float = Field(..., description="AWS monthly cost")
    do_monthly_cost: float = Field(..., description="DO monthly cost")
    cost_breakdown: Dict[str, Dict[str, float]] = Field(..., description="Cost breakdown by category")
    payback_period_months: int = Field(..., description="Payback period in months")
    three_year_savings: float = Field(..., description="Three-year savings projection")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Report generation timestamp")


# Terraform Schemas
class TerraformResponse(BaseModel):
    """Response for Terraform generation"""
    terraform_code: str = Field(..., description="Generated Terraform code")
    file_url: str = Field(..., description="URL to Terraform file in Spaces")
    validation_status: str = Field(..., description="Validation status: valid, invalid")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors if any")
    resource_count: int = Field(..., description="Number of resources in Terraform code")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")


# Deployment Schemas
class DeployedResource(BaseModel):
    """Deployed resource details"""
    name: str = Field(..., description="Resource name")
    type: str = Field(..., description="Resource type")
    id: str = Field(..., description="Resource ID in DigitalOcean")
    status: str = Field(..., description="Resource status")


class FailedResource(BaseModel):
    """Failed resource details"""
    name: str = Field(..., description="Resource name")
    type: str = Field(..., description="Resource type")
    error: str = Field(..., description="Error message")


class DeploymentResultSchema(BaseModel):
    """Deployment result"""
    deployment_id: str = Field(..., description="Deployment identifier")
    status: str = Field(..., description="Deployment status: completed, failed, partial")
    deployed_resources: List[DeployedResource] = Field(..., description="Successfully deployed resources")
    failed_resources: List[FailedResource] = Field(default_factory=list, description="Failed resources")
    total_resources: int = Field(..., description="Total resources to deploy")
    deployed_count: int = Field(..., description="Number of deployed resources")
    failed_count: int = Field(..., description="Number of failed resources")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Deployment start time")
    completed_at: Optional[datetime] = Field(None, description="Deployment completion time")


# Alert Schemas
class AlertSchema(BaseModel):
    """Infrastructure alert"""
    alert_id: str = Field(..., description="Alert identifier")
    resource_id: str = Field(..., description="Resource ID")
    resource_name: str = Field(..., description="Resource name")
    resource_type: str = Field(..., description="Resource type")
    severity: str = Field(..., description="Alert severity: High, Medium, Low")
    message: str = Field(..., description="Alert message")
    metric_type: str = Field(..., description="Metric type: cpu, storage, network, anomaly")
    metric_value: Optional[float] = Field(None, description="Metric value")
    threshold: Optional[float] = Field(None, description="Threshold value")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Alert creation time")
    resolved: bool = Field(default=False, description="Whether alert is resolved")


class AlertsResponse(BaseModel):
    """Response for alerts retrieval"""
    alerts: List[AlertSchema] = Field(..., description="List of alerts")
    total_count: int = Field(..., description="Total number of alerts")
    unresolved_count: int = Field(..., description="Number of unresolved alerts")


# Self-Healing Schemas
class SelfHealingActionSchema(BaseModel):
    """Self-healing action details"""
    action_id: str = Field(..., description="Action identifier")
    alert_id: str = Field(..., description="Related alert ID")
    resource_id: str = Field(..., description="Resource ID")
    resource_name: str = Field(..., description="Resource name")
    action_type: str = Field(..., description="Action type: storage_autoscaling, resize, etc.")
    terraform_code: str = Field(..., description="Generated Terraform code")
    pr_url: str = Field(..., description="GitHub pull request URL")
    status: str = Field(..., description="Action status: pending, merged, rejected")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Action creation time")


class SelfHealingActionsResponse(BaseModel):
    """Response for self-healing actions retrieval"""
    actions: List[SelfHealingActionSchema] = Field(..., description="List of self-healing actions")
    total_count: int = Field(..., description="Total number of actions")
    pending_count: int = Field(..., description="Number of pending actions")


# AI Enablement Schemas
class RAGDataSource(BaseModel):
    """RAG-suitable data source"""
    source: str = Field(..., description="Data source name")
    type: str = Field(..., description="Data type: structured_data, unstructured_data")
    use_case: str = Field(..., description="Use case description")
    estimated_size_gb: int = Field(..., description="Estimated data size in GB")


class RAGArchitectureComponent(BaseModel):
    """RAG architecture component"""
    name: str = Field(..., description="Component name")
    description: str = Field(..., description="Component description")
    technology: str = Field(..., description="Technology to use")


class OpenSearchConfig(BaseModel):
    """OpenSearch configuration"""
    index_strategy: str = Field(..., description="Index strategy")
    mapping_configuration: str = Field(..., description="Mapping configuration")
    query_strategy: str = Field(..., description="Query strategy")


class OpenSearchClusterSizing(BaseModel):
    """OpenSearch cluster sizing recommendation"""
    node_count: int = Field(..., description="Number of nodes")
    node_size: str = Field(..., description="Node size")
    storage_gb: int = Field(..., description="Storage per node in GB")
    estimated_cost_monthly: float = Field(..., description="Estimated monthly cost")
    rationale: str = Field(..., description="Sizing rationale")


class RAGArchitectureSchema(BaseModel):
    """RAG architecture proposal"""
    architecture_overview: str = Field(..., description="High-level architecture description")
    components: List[RAGArchitectureComponent] = Field(..., description="Architecture components")
    data_flow: str = Field(..., description="Data flow description")
    opensearch_configuration: OpenSearchConfig = Field(..., description="OpenSearch configuration")
    opensearch_cluster_sizing: OpenSearchClusterSizing = Field(..., description="Cluster sizing")
    implementation_steps: List[str] = Field(..., description="Implementation steps")
    sample_code: Dict[str, str] = Field(..., description="Sample code for each data source")


class AICapabilityRecommendation(BaseModel):
    """AI capability recommendation"""
    capability: str = Field(..., description="AI capability name")
    description: str = Field(..., description="Capability description")
    business_value: str = Field(..., description="Business value and ROI")
    implementation_complexity: str = Field(..., description="Complexity: Low, Medium, High")
    priority: str = Field(..., description="Priority: High, Medium, Low")
    use_cases: List[str] = Field(..., description="Use cases")


class AIEnablementResponse(BaseModel):
    """Response for AI enablement analysis"""
    workload_types: List[str] = Field(..., description="Detected workload types")
    rag_suitable_data: List[RAGDataSource] = Field(..., description="RAG-suitable data sources")
    rag_architecture: Optional[RAGArchitectureSchema] = Field(None, description="RAG architecture proposal")
    ai_recommendations: List[AICapabilityRecommendation] = Field(..., description="AI capability recommendations")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")


# Request Schemas
class AnalyzeRequest(BaseModel):
    """Request for infrastructure analysis"""
    upload_id: str = Field(..., description="Upload identifier")


class MigrationPlanRequest(BaseModel):
    """Request for migration plan generation"""
    upload_id: str = Field(..., description="Upload identifier")
    include_ai_enablement: bool = Field(default=True, description="Include AI enablement analysis")


class TerraformGenerationRequest(BaseModel):
    """Request for Terraform code generation"""
    plan_id: str = Field(..., description="Migration plan identifier")


class DeployRequest(BaseModel):
    """Request for infrastructure deployment"""
    plan_id: str = Field(..., description="Migration plan identifier")
    confirm: bool = Field(..., description="Confirmation flag")
    
    @validator('confirm')
    def confirm_must_be_true(cls, v):
        if not v:
            raise ValueError('Deployment must be confirmed')
        return v


class ExportReportRequest(BaseModel):
    """Request for report export"""
    plan_id: str = Field(..., description="Migration plan identifier")
    include_terraform: bool = Field(default=True, description="Include Terraform code")
    include_cost_analysis: bool = Field(default=True, description="Include cost analysis")
    include_risks: bool = Field(default=True, description="Include risk analysis")


# Error Response Schema
class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


# Health Check Schema
class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status: healthy, unhealthy")
    database: str = Field(..., description="Database status: connected, disconnected")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    version: str = Field(default="1.0.0", description="API version")


# ---------------------------------------------------------------------------
# Store Intelligence Schemas
# ---------------------------------------------------------------------------

class DocumentInfo(BaseModel):
    """Info about an uploaded document."""
    document_id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: Optional[int] = None


class DocumentUploadResponse(BaseModel):
    """Response for document upload."""
    documents: List[DocumentInfo]
    total_uploaded: int


class IntelligenceRequest(BaseModel):
    """Request for RAG query."""
    question: str
    max_sources: int = 5


class SourceReference(BaseModel):
    """Source reference in a RAG response."""
    document_id: str
    filename: str
    chunk_excerpt: str
    relevance_score: float


class IntelligenceResponse(BaseModel):
    """Response for RAG query."""
    answer: str
    sources: List[SourceReference]
    model_used: str = "llama3-8b-instruct"


class KnowledgeBaseStatus(BaseModel):
    """Knowledge base statistics."""
    total_documents: int
    total_chunks: int
    index_health: str  # green, yellow, red
    last_updated: Optional[str] = None
