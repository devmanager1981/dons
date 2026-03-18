"""
DONS Cloud Migration Platform - FastAPI Application

Main application with all API endpoints for cloud migration workflow.
"""

import os
import uuid
import asyncio
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from sqlalchemy.orm import Session
import boto3
from botocore.client import Config

# Import modules
from database import get_db, engine, check_database_health
from models import Base, InfrastructureUpload, MigrationPlan, Deployment, Alert, SelfHealingAction, Document, DocumentChunk
from schemas import (
    UploadResponse, AnalyzeResponse, AnalyzeRequest, MigrationPlanSchema,
    MigrationPlanRequest, TerraformGenerationRequest, CostComparisonSchema,
    CostBreakdownSchema, TerraformResponse,
    DeploymentResultSchema, DeployRequest, AlertsResponse, AlertSchema,
    SelfHealingActionsResponse, ROIReportSchema, ErrorResponse,
    HealthCheckResponse, AIEnablementResponse,
    DocumentInfo, DocumentUploadResponse, IntelligenceRequest,
    IntelligenceResponse, SourceReference, KnowledgeBaseStatus
)
import terraform_parser
import migration_mapper
import cost_estimator
import terraform_generator
import do_deployer
import cloud_migration_architect
import devops_agent
import ai_enablement_agent
import store_intelligence_agent


# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="DONS Cloud Migration Platform",
    description="AI-powered cloud migration from AWS to DigitalOcean",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Spaces configuration
SPACES_REGION = os.getenv("DO_SPACES_REGION", "nyc3")
SPACES_BUCKET = os.getenv("DO_SPACES_BUCKET", "dons-uploads")
SPACES_ACCESS_KEY = os.getenv("DO_SPACES_ACCESS_KEY") or os.getenv("SPACES_ACCESS_KEY_ID")
SPACES_SECRET_KEY = os.getenv("DO_SPACES_SECRET_KEY") or os.getenv("SPACES_ACCESS_KEY")


def get_spaces_client():
    """Get Spaces S3 client"""
    return boto3.client(
        's3',
        region_name=SPACES_REGION,
        endpoint_url=f'https://{SPACES_REGION}.digitaloceanspaces.com',
        aws_access_key_id=SPACES_ACCESS_KEY,
        aws_secret_access_key=SPACES_SECRET_KEY,
        config=Config(signature_version='s3v4')
    )


# Health Check Endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if check_database_health() else "disconnected"
    
    return HealthCheckResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        database=db_status
    )


# File Upload Endpoint
@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload infrastructure file (Terraform or CloudFormation)
    """
    # Validate file extension
    allowed_extensions = ['.tf', '.tf.json', '.tfstate', '.yaml', '.yml', '.json']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Validate file size (50MB limit)
    if file_size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 50MB limit"
        )
    
    # Generate upload ID
    upload_id = str(uuid.uuid4())
    
    # Upload to Spaces
    try:
        s3_client = get_spaces_client()
        s3_key = f"uploads/{upload_id}/{file.filename}"
        
        s3_client.put_object(
            Bucket=SPACES_BUCKET,
            Key=s3_key,
            Body=content,
            ACL='private'
        )
        
        file_url = f"https://{SPACES_BUCKET}.{SPACES_REGION}.digitaloceanspaces.com/{s3_key}"
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
    
    # Store metadata in database
    upload = InfrastructureUpload(
        id=upload_id,
        user_id=None,  # TODO: Get from authenticated user
        filename=file.filename,
        file_size_bytes=file_size,
        file_type=file_ext,
        storage_url=file_url,
        parse_status="pending"
    )
    
    db.add(upload)
    db.commit()
    db.refresh(upload)
    
    return UploadResponse(
        upload_id=str(upload.id),
        filename=upload.filename,
        file_size=upload.file_size_bytes,
        file_url=upload.storage_url,
        upload_timestamp=upload.created_at,
        status=upload.parse_status
    )


# Infrastructure Analysis Endpoint
@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_infrastructure(
    request: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze uploaded infrastructure file
    """
    # Get upload from database
    upload = db.query(InfrastructureUpload).filter(
        InfrastructureUpload.id == request.upload_id
    ).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    # Download file from Spaces
    try:
        s3_client = get_spaces_client()
        s3_key = upload.storage_url.split(f"{SPACES_BUCKET}.{SPACES_REGION}.digitaloceanspaces.com/")[1]
        
        response = s3_client.get_object(Bucket=SPACES_BUCKET, Key=s3_key)
        content = response['Body'].read().decode('utf-8')
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )
    
    # Parse infrastructure file
    try:
        # Get file extension
        file_ext = os.path.splitext(upload.filename)[1].lower()
        print(f"[DEBUG] Parsing file with extension: {file_ext}")
        
        parsed_result = terraform_parser.parse_infrastructure_file(
            content,
            file_ext
        )
        print(f"[DEBUG] Parsed {len(parsed_result.resources)} resources")
        
        # Convert AWSResource objects to dictionaries for response
        resources = [
            {
                "name": r.resource_name,
                "type": r.resource_type,
                "config": r.configuration,
                "dependencies": r.dependencies
            }
            for r in parsed_result.resources
        ]
        print(f"[DEBUG] Converted to {len(resources)} resource dicts")
        
        # Identify unsupported resources
        supported_resources, unsupported_types = terraform_parser.filter_supported_resources(parsed_result.resources)
        print(f"[DEBUG] Found {len(unsupported_types)} unsupported types")
        
        # Convert error strings to ParseError objects
        parse_errors = [
            {
                "message": error,
                "file": upload.filename,
                "line": None
            }
            for error in parsed_result.errors
        ]
        print(f"[DEBUG] Converted {len(parse_errors)} errors")
        
        # Update upload status
        upload.parse_status = "analyzed"
        db.commit()
        print(f"[DEBUG] Updated upload status to analyzed")
        
        return AnalyzeResponse(
            upload_id=request.upload_id,
            resources_detected=len(resources),
            resources=resources,
            parse_errors=parse_errors,
            unsupported_resources=unsupported_types,
            analysis_timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        print(f"[ERROR] Failed to analyze: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze infrastructure: {str(e)}"
        )


# Migration Plan Generation Endpoint
@app.post("/api/escape-plan", response_model=MigrationPlanSchema)
async def generate_escape_plan(
    request: MigrationPlanRequest,
    db: Session = Depends(get_db)
):
    """
    Generate migration plan (escape plan)
    """
    # Get upload from database
    upload = db.query(InfrastructureUpload).filter(
        InfrastructureUpload.id == request.upload_id
    ).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    # Download and parse file
    try:
        print(f"[DEBUG] Fetching file from Spaces for upload {request.upload_id}")
        s3_client = get_spaces_client()
        s3_key = upload.storage_url.split(f"{SPACES_BUCKET}.{SPACES_REGION}.digitaloceanspaces.com/")[1]
        
        response = s3_client.get_object(Bucket=SPACES_BUCKET, Key=s3_key)
        content = response['Body'].read().decode('utf-8')
        print(f"[DEBUG] Downloaded file, size: {len(content)} bytes")
        
        # Get file extension
        file_ext = os.path.splitext(upload.filename)[1].lower()
        
        parsed_result = terraform_parser.parse_infrastructure_file(content, file_ext)
        print(f"[DEBUG] Parsed {len(parsed_result.resources)} resources")
        
    except Exception as e:
        print(f"[ERROR] Failed to process file: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}"
        )
    
    # Map AWS resources to DigitalOcean
    try:
        print(f"[DEBUG] Mapping {len(parsed_result.resources)} AWS resources to DO")
        do_resources = []
        mappings = []
        
        for aws_resource in parsed_result.resources:
            print(f"[DEBUG] Mapping {aws_resource.resource_type}.{aws_resource.resource_name}")
            do_resource = migration_mapper.map_aws_to_do(aws_resource)
            do_resources.append(do_resource)
            
            mappings.append({
                "aws_resource": aws_resource.resource_name,
                "aws_type": aws_resource.resource_type,
                "do_resource": do_resource.resource_name,
                "do_type": do_resource.resource_type
            })
        
        print(f"[DEBUG] Mapped to {len(do_resources)} DO resources")
        
        # Convert to dict format for AI processing
        aws_resources_dict = [
            {
                "name": r.resource_name,
                "type": r.resource_type,
                "config": r.configuration,
                "dependencies": r.dependencies
            }
            for r in parsed_result.resources
        ]
        
    except Exception as e:
        print(f"[ERROR] Failed to map resources: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to map resources: {str(e)}"
        )
    
    # Generate migration plan using AI
    try:
        print(f"[DEBUG] Generating migration plan with AI")
        # Convert DO resources to dict format
        do_resources_dict = [
            {
                "name": r.resource_name,
                "type": r.resource_type,
                "config": r.configuration
            }
            for r in do_resources
        ]
        
        plan = await cloud_migration_architect.generate_migration_plan(
            aws_resources=aws_resources_dict,
            do_resources=do_resources_dict,
            mappings=mappings
        )
        print(f"[DEBUG] AI plan generated")
        
        # Generate plan ID
        plan_id = str(uuid.uuid4())
        
        # Store plan in database
        migration_plan = MigrationPlan(
            id=plan_id,
            upload_id=request.upload_id,
            resources_detected=aws_resources_dict,
            resource_mappings=mappings,
            migration_plan=plan.get("deployment_steps", []),
            risk_analysis=plan.get("risks", []),
            overall_risk_score=plan.get("overall_risk_score", "Medium"),
            estimated_duration_hours=plan.get("duration_estimate", {}).get("total_hours", 0),
            created_at=datetime.utcnow()
        )
        
        db.add(migration_plan)
        db.commit()
        
        return MigrationPlanSchema(
            plan_id=plan_id,
            deployment_steps=plan.get("deployment_steps", []),
            deployment_order=plan.get("deployment_order", []),
            risks=plan.get("risks", []),
            rollback_procedures=plan.get("rollback_procedures", []),
            duration_estimate=plan.get("duration_estimate", {}),
            total_resources=plan.get("total_resources", 0),
            migration_strategy=plan.get("migration_strategy", ""),
            created_at=migration_plan.created_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate migration plan: {str(e)}"
        )


# Cost Comparison Endpoint
@app.post("/api/cost", response_model=CostComparisonSchema)
async def calculate_costs(
    request: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate cost comparison between AWS and DigitalOcean
    """
    # Get upload and parse resources
    upload = db.query(InfrastructureUpload).filter(
        InfrastructureUpload.id == request.upload_id
    ).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    try:
        print(f"[DEBUG] Calculating costs for upload {request.upload_id}")
        # Download and parse file
        s3_client = get_spaces_client()
        s3_key = upload.storage_url.split(f"{SPACES_BUCKET}.{SPACES_REGION}.digitaloceanspaces.com/")[1]
        
        response = s3_client.get_object(Bucket=SPACES_BUCKET, Key=s3_key)
        content = response['Body'].read().decode('utf-8')
        
        # Get file extension
        file_ext = os.path.splitext(upload.filename)[1].lower()
        
        parsed_result = terraform_parser.parse_infrastructure_file(content, file_ext)
        print(f"[DEBUG] Parsed {len(parsed_result.resources)} resources for cost calculation")
        
        # Map to DO resources (using AWSResource objects)
        do_resources = []
        for aws_resource in parsed_result.resources:
            do_resource = migration_mapper.map_aws_to_do(aws_resource)
            do_resources.append({
                "name": do_resource.resource_name,
                "type": do_resource.resource_type,
                "config": do_resource.configuration
            })
        
        # Convert AWS resources to dicts for cost estimator
        aws_resources_dict = [
            {
                "name": r.resource_name,
                "type": r.resource_type,
                "config": r.configuration,
                "dependencies": r.dependencies
            }
            for r in parsed_result.resources
        ]
        
        # Calculate costs
        print(f"[DEBUG] Calculating costs for {len(aws_resources_dict)} AWS and {len(do_resources)} DO resources")
        comparison = cost_estimator.compare_costs(aws_resources_dict, do_resources)
        print(f"[DEBUG] Cost calculation complete: AWS ${comparison.aws_monthly_cost:.2f}, DO ${comparison.do_monthly_cost:.2f}")
        
        # Convert CostBreakdown dataclasses to dicts for Pydantic
        return CostComparisonSchema(
            aws_monthly_cost=comparison.aws_monthly_cost,
            do_monthly_cost=comparison.do_monthly_cost,
            monthly_savings=comparison.monthly_savings,
            savings_percentage=comparison.savings_percentage,
            aws_breakdown=CostBreakdownSchema(
                compute=comparison.aws_breakdown.compute,
                storage=comparison.aws_breakdown.storage,
                network=comparison.aws_breakdown.network,
                database=comparison.aws_breakdown.database,
                kubernetes=comparison.aws_breakdown.kubernetes,
                load_balancer=comparison.aws_breakdown.load_balancer
            ),
            do_breakdown=CostBreakdownSchema(
                compute=comparison.do_breakdown.compute,
                storage=comparison.do_breakdown.storage,
                network=comparison.do_breakdown.network,
                database=comparison.do_breakdown.database,
                kubernetes=comparison.do_breakdown.kubernetes,
                load_balancer=comparison.do_breakdown.load_balancer
            ),
            annual_savings=comparison.annual_savings
        )
        
    except Exception as e:
        print(f"[ERROR] Failed to calculate costs: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate costs: {str(e)}"
        )


# Terraform Generation Endpoint
@app.post("/api/generate-terraform", response_model=TerraformResponse)
async def generate_terraform(
    request: TerraformGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate Terraform code for DigitalOcean resources
    """
    # Get migration plan
    plan = db.query(MigrationPlan).filter(
        MigrationPlan.id == request.plan_id
    ).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Migration plan not found"
        )
    
    try:
        print(f"[DEBUG] Generating Terraform for plan {request.plan_id}")
        # Get upload and parse resources
        upload = db.query(InfrastructureUpload).filter(
            InfrastructureUpload.id == plan.upload_id
        ).first()
        
        s3_client = get_spaces_client()
        s3_key = upload.storage_url.split(f"{SPACES_BUCKET}.{SPACES_REGION}.digitaloceanspaces.com/")[1]
        
        response = s3_client.get_object(Bucket=SPACES_BUCKET, Key=s3_key)
        content = response['Body'].read().decode('utf-8')
        
        # Get file extension
        file_ext = os.path.splitext(upload.filename)[1].lower()
        
        parsed_result = terraform_parser.parse_infrastructure_file(content, file_ext)
        print(f"[DEBUG] Parsed {len(parsed_result.resources)} resources for Terraform generation")
        
        # Map to DO resources (using AWSResource objects)
        do_resources = []
        for aws_resource in parsed_result.resources:
            do_resource = migration_mapper.map_aws_to_do(aws_resource)
            do_resources.append({
                "name": do_resource.resource_name,
                "type": do_resource.resource_type,
                "config": do_resource.configuration
            })
        
        # Generate Terraform code
        print(f"[DEBUG] Generating Terraform code for {len(do_resources)} DO resources")
        terraform_code = terraform_generator.generate_terraform_code(do_resources)
        print(f"[DEBUG] Generated {len(terraform_code)} chars of Terraform code")
        
        # Validate
        is_valid, errors = terraform_generator.validate_terraform_syntax(terraform_code)
        print(f"[DEBUG] Terraform validation: {'valid' if is_valid else 'invalid'}")
        
        # Upload to Spaces
        tf_key = f"terraform/{plan.id}/main.tf"
        s3_client.put_object(
            Bucket=SPACES_BUCKET,
            Key=tf_key,
            Body=terraform_code.encode('utf-8'),
            ACL='private'
        )
        
        file_url = f"https://{SPACES_BUCKET}.{SPACES_REGION}.digitaloceanspaces.com/{tf_key}"
        print(f"[DEBUG] Uploaded Terraform to {file_url}")
        
        return TerraformResponse(
            terraform_code=terraform_code,
            file_url=file_url,
            validation_status="valid" if is_valid else "invalid",
            validation_errors=errors,
            resource_count=len(do_resources),
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        print(f"[ERROR] Failed to generate Terraform: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Terraform: {str(e)}"
        )


# Deployment Endpoint
@app.post("/api/deploy", response_model=DeploymentResultSchema)
async def deploy_infrastructure(
    request: DeployRequest,
    db: Session = Depends(get_db)
):
    """
    Deploy infrastructure to DigitalOcean
    """
    # Get migration plan
    plan = db.query(MigrationPlan).filter(
        MigrationPlan.id == request.plan_id
    ).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Migration plan not found"
        )
    
    try:
        print(f"[DEBUG] Deploying infrastructure for plan {request.plan_id}")
        # Get upload and parse resources
        upload = db.query(InfrastructureUpload).filter(
            InfrastructureUpload.id == plan.upload_id
        ).first()
        
        s3_client = get_spaces_client()
        s3_key = upload.storage_url.split(f"{SPACES_BUCKET}.{SPACES_REGION}.digitaloceanspaces.com/")[1]
        
        response = s3_client.get_object(Bucket=SPACES_BUCKET, Key=s3_key)
        content = response['Body'].read().decode('utf-8')
        
        # Get file extension
        file_ext = os.path.splitext(upload.filename)[1].lower()
        
        parsed_result = terraform_parser.parse_infrastructure_file(content, file_ext)
        print(f"[DEBUG] Parsed {len(parsed_result.resources)} resources for deployment")
        
        # Map to DO resources (using AWSResource objects)
        do_resources = []
        for aws_resource in parsed_result.resources:
            do_resource = migration_mapper.map_aws_to_do(aws_resource)
            do_resources.append({
                "name": do_resource.resource_name,
                "type": do_resource.resource_type,
                "config": do_resource.configuration
            })
        
        # Deploy infrastructure
        print(f"[DEBUG] Deploying {len(do_resources)} DO resources")
        deployment_result = await do_deployer.deploy_infrastructure(do_resources)
        print(f"[DEBUG] Deployment complete: {deployment_result.get('status')}")
        
        # Generate deployment ID
        deployment_id = str(uuid.uuid4())
        
        # Store deployment in database
        deployment = Deployment(
            id=deployment_id,
            migration_plan_id=request.plan_id,
            status=deployment_result.get("status"),
            deployed_resources=deployment_result.get("deployed_resources", []),
            started_at=datetime.utcnow()
        )
        
        db.add(deployment)
        db.commit()
        
        return DeploymentResultSchema(
            deployment_id=deployment_id,
            status=deployment_result.get("status"),
            deployed_resources=deployment_result.get("deployed_resources", []),
            failed_resources=deployment_result.get("failed_resources", []),
            total_resources=deployment_result.get("total_resources", 0),
            deployed_count=deployment_result.get("deployed_count", 0),
            failed_count=deployment_result.get("failed_count", 0),
            started_at=deployment.started_at,
            completed_at=datetime.utcnow()
        )
        
    except Exception as e:
        print(f"[ERROR] Deployment failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deploy infrastructure: {str(e)}"
        )


# Destroy Infrastructure Endpoint
@app.post("/api/destroy")
async def destroy_infrastructure(
    request: DeployRequest,
    db: Session = Depends(get_db)
):
    """
    Destroy/teardown deployed infrastructure
    """
    # Get deployment
    deployment = db.query(Deployment).filter(
        Deployment.migration_plan_id == request.plan_id
    ).order_by(Deployment.created_at.desc()).first()
    
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No deployment found for this plan"
        )
    
    if not deployment.deployed_resources:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No resources to destroy"
        )
    
    try:
        print(f"[DEBUG] Destroying infrastructure for deployment {deployment.id}")
        print(f"[DEBUG] Resources to destroy: {len(deployment.deployed_resources)}")
        
        # Rollback/destroy the deployment
        rollback_result = await do_deployer.rollback_deployment(deployment.deployed_resources)
        print(f"[DEBUG] Destroy complete: {rollback_result.get('status')}")
        
        # Update deployment status
        deployment.status = "destroyed"
        db.commit()
        
        return {
            "deployment_id": str(deployment.id),
            "status": rollback_result.get("status"),
            "deleted_resources": rollback_result.get("deleted_resources", []),
            "failed_deletions": rollback_result.get("failed_deletions", []),
            "total_deleted": len(rollback_result.get("deleted_resources", [])),
            "total_failed": len(rollback_result.get("failed_deletions", [])),
            "destroyed_at": datetime.utcnow()
        }
        
    except Exception as e:
        print(f"[ERROR] Destroy failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to destroy infrastructure: {str(e)}"
        )


# Alerts Endpoint
@app.get("/api/alerts", response_model=AlertsResponse)
async def get_alerts(
    resource_id: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get infrastructure alerts
    """
    query = db.query(Alert)
    
    if resource_id:
        query = query.filter(Alert.resource_id == resource_id)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    
    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    
    unresolved_count = db.query(Alert).filter(Alert.resolved == False).count()
    
    return AlertsResponse(
        alerts=[
            AlertSchema(
                alert_id=str(alert.id),
                resource_id=alert.resource_id,
                resource_name=alert.resource_name or "",
                resource_type=alert.resource_type or "",
                severity=alert.severity,
                message=alert.message,
                metric_type=alert.metric_type or "",
                metric_value=alert.metric_value,
                threshold=alert.threshold,
                created_at=alert.created_at,
                resolved=alert.resolved
            )
            for alert in alerts
        ],
        total_count=len(alerts),
        unresolved_count=unresolved_count
    )


# ROI Report Endpoint
@app.get("/api/roi-report", response_model=ROIReportSchema)
async def get_roi_report(
    plan_id: str,
    db: Session = Depends(get_db)
):
    """
    Generate one-click ROI report
    """
    # Get migration plan
    plan = db.query(MigrationPlan).filter(
        MigrationPlan.id == plan_id
    ).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Migration plan not found"
        )
    
    try:
        # Get upload and calculate costs
        upload = db.query(InfrastructureUpload).filter(
            InfrastructureUpload.id == plan.upload_id
        ).first()
        
        s3_client = get_spaces_client()
        s3_key = upload.storage_url.split(f"{SPACES_BUCKET}.{SPACES_REGION}.digitaloceanspaces.com/")[1]
        
        response = s3_client.get_object(Bucket=SPACES_BUCKET, Key=s3_key)
        content = response['Body'].read().decode('utf-8')
        
        # Get file extension
        file_ext = os.path.splitext(upload.filename)[1].lower()
        
        parsed_result = terraform_parser.parse_infrastructure_file(content, file_ext)
        
        # Convert AWS resources to dicts
        aws_resources = [
            {
                "name": r.resource_name,
                "type": r.resource_type,
                "config": r.configuration,
                "dependencies": r.dependencies
            }
            for r in parsed_result.resources
        ]
        
        # Map to DO resources
        do_resources = []
        for aws_resource in parsed_result.resources:
            do_resource = migration_mapper.map_aws_to_do(aws_resource)
            do_resources.append({
                "name": do_resource.resource_name,
                "type": do_resource.resource_type,
                "config": do_resource.configuration
            })
        
        # Calculate costs
        comparison = cost_estimator.compare_costs(aws_resources, do_resources)
        
        # Calculate payback period (assume $5000 migration cost)
        migration_cost = 5000
        payback_months = int(migration_cost / comparison.monthly_savings) if comparison.monthly_savings > 0 else 0
        
        # Calculate 3-year savings
        three_year_savings = comparison.annual_savings * 3 - migration_cost
        
        return ROIReportSchema(
            monthly_savings=comparison.monthly_savings,
            annual_savings=comparison.annual_savings,
            savings_percentage=comparison.savings_percentage,
            aws_monthly_cost=comparison.aws_monthly_cost,
            do_monthly_cost=comparison.do_monthly_cost,
            cost_breakdown={
                "aws": {
                    "compute": comparison.aws_breakdown.compute,
                    "storage": comparison.aws_breakdown.storage,
                    "database": comparison.aws_breakdown.database,
                    "kubernetes": comparison.aws_breakdown.kubernetes,
                    "load_balancer": comparison.aws_breakdown.load_balancer
                },
                "digitalocean": {
                    "compute": comparison.do_breakdown.compute,
                    "storage": comparison.do_breakdown.storage,
                    "database": comparison.do_breakdown.database,
                    "kubernetes": comparison.do_breakdown.kubernetes,
                    "load_balancer": comparison.do_breakdown.load_balancer
                }
            },
            payback_period_months=payback_months,
            three_year_savings=three_year_savings,
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate ROI report: {str(e)}"
        )


# Self-Healing Actions Endpoint
@app.get("/api/self-healing-actions", response_model=SelfHealingActionsResponse)
async def get_self_healing_actions(
    resource_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get self-healing actions history
    """
    query = db.query(SelfHealingAction)
    
    if resource_id:
        query = query.filter(SelfHealingAction.resource_id == resource_id)
    
    actions = query.order_by(SelfHealingAction.created_at.desc()).limit(limit).all()
    
    pending_count = db.query(SelfHealingAction).filter(
        SelfHealingAction.status == "pending"
    ).count()
    
    return SelfHealingActionsResponse(
        actions=[
            SelfHealingActionSchema(
                action_id=str(action.id),
                alert_id=str(action.alert_id),
                resource_id=action.resource_id,
                resource_name=action.resource_name or "",
                action_type=action.action_type,
                terraform_code=action.terraform_code,
                pr_url=action.pr_url,
                status=action.status,
                created_at=action.created_at
            )
            for action in actions
        ],
        total_count=len(actions),
        pending_count=pending_count
    )


# Export Report Endpoint
@app.get("/api/export-report")
async def export_report(
    plan_id: str,
    db: Session = Depends(get_db)
):
    """
    Export migration report as Markdown
    """
    # Get migration plan
    plan = db.query(MigrationPlan).filter(
        MigrationPlan.id == plan_id
    ).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Migration plan not found"
        )
    
    try:
        # Get upload
        upload = db.query(InfrastructureUpload).filter(
            InfrastructureUpload.id == plan.upload_id
        ).first()
        
        # Get file and parse
        s3_client = get_spaces_client()
        s3_key = upload.storage_url.split(f"{SPACES_BUCKET}.{SPACES_REGION}.digitaloceanspaces.com/")[1]
        response = s3_client.get_object(Bucket=SPACES_BUCKET, Key=s3_key)
        content = response['Body'].read().decode('utf-8')
        file_ext = os.path.splitext(upload.filename)[1].lower()
        parsed_result = terraform_parser.parse_infrastructure_file(content, file_ext)
        
        # Convert resources
        aws_resources = [
            {"name": r.resource_name, "type": r.resource_type, "config": r.configuration, "dependencies": r.dependencies}
            for r in parsed_result.resources
        ]
        do_resources = []
        for aws_resource in parsed_result.resources:
            do_resource = migration_mapper.map_aws_to_do(aws_resource)
            do_resources.append({"name": do_resource.resource_name, "type": do_resource.resource_type, "config": do_resource.configuration})
        
        # Calculate costs
        comparison = cost_estimator.compare_costs(aws_resources, do_resources)
        
        # Generate Markdown report
        report = f"""# DONS Cloud Migration Report

**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Plan ID**: `{plan_id}`  
**Source File**: `{upload.filename}`

---

## Executive Summary

This report provides a comprehensive analysis of migrating your AWS infrastructure to DigitalOcean.

### Key Metrics
- **Total Resources**: {len(aws_resources)}
- **Monthly Savings**: ${comparison.monthly_savings:.2f} ({comparison.savings_percentage:.1f}%)
- **Annual Savings**: ${comparison.annual_savings:.2f}
- **Payback Period**: {int(5000 / comparison.monthly_savings) if comparison.monthly_savings > 0 else 0} months

---

## Cost Analysis

### Current AWS Costs (Monthly)
- **Total**: ${comparison.aws_monthly_cost:.2f}/month
- Compute: ${comparison.aws_breakdown.compute:.2f}
- Storage: ${comparison.aws_breakdown.storage:.2f}
- Database: ${comparison.aws_breakdown.database:.2f}
- Kubernetes: ${comparison.aws_breakdown.kubernetes:.2f}
- Load Balancer: ${comparison.aws_breakdown.load_balancer:.2f}

### DigitalOcean Costs (Monthly)
- **Total**: ${comparison.do_monthly_cost:.2f}/month
- Compute: ${comparison.do_breakdown.compute:.2f}
- Storage: ${comparison.do_breakdown.storage:.2f}
- Database: ${comparison.do_breakdown.database:.2f}
- Kubernetes: ${comparison.do_breakdown.kubernetes:.2f}
- Load Balancer: ${comparison.do_breakdown.load_balancer:.2f}

### Savings Breakdown
- **Monthly Savings**: ${comparison.monthly_savings:.2f}
- **Annual Savings**: ${comparison.annual_savings:.2f}
- **3-Year Savings**: ${comparison.annual_savings * 3 - 5000:.2f}

---

## Resource Mapping

### AWS Resources Detected
"""
        for resource in aws_resources:
            report += f"\n- **{resource['type']}**.`{resource['name']}`"
        
        report += "\n\n### DigitalOcean Equivalent Resources\n"
        for resource in do_resources:
            report += f"\n- **{resource['type']}**.`{resource['name']}`"
        
        report += f"""

---

## Migration Strategy

### Recommended Approach
1. **Pre-Migration**: Backup all data and test rollback procedures
2. **Pilot Migration**: Start with non-critical resources
3. **Validation**: Test functionality in DigitalOcean environment
4. **Full Migration**: Migrate remaining resources
5. **Optimization**: Fine-tune configurations for cost and performance

### Estimated Timeline
- **Preparation**: 1-2 weeks
- **Pilot Migration**: 1 week
- **Full Migration**: 2-4 weeks
- **Optimization**: 1-2 weeks

---

## Risk Assessment

### Identified Risks
"""
        
        # Add risks from plan if available
        risks = plan.risk_analysis if isinstance(plan.risk_analysis, list) else []
        if risks:
            for risk in risks[:5]:  # Top 5 risks
                if isinstance(risk, dict):
                    report += f"\n- **{risk.get('severity', 'Medium')}**: {risk.get('risk', 'Risk assessment')}"
                    report += f"\n  - *Mitigation*: {risk.get('mitigation', 'Standard mitigation procedures')}"
        else:
            report += "\n- **Medium**: Data migration complexity - Use incremental migration approach"
            report += "\n- **Low**: Service downtime - Plan maintenance window"
            report += "\n- **Low**: Configuration drift - Use Infrastructure as Code"
        
        report += """

---

## Next Steps

1. **Review this report** with your team
2. **Schedule a migration planning session**
3. **Set up DigitalOcean account** and configure access
4. **Create backup strategy** for all critical data
5. **Execute pilot migration** with non-critical resources
6. **Monitor and validate** pilot results
7. **Proceed with full migration** once validated

---

## Support

For questions or assistance with your migration:
- **Documentation**: https://docs.digitalocean.com
- **Support**: https://www.digitalocean.com/support
- **Community**: https://www.digitalocean.com/community

---

*This report was generated by DONS (DigitalOcean Migration Platform)*
"""
        
        # Return as downloadable file
        from fastapi.responses import Response
        return Response(
            content=report,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=migration-report-{plan_id[:8]}.md"
            }
        )
        
    except Exception as e:
        print(f"[ERROR] Failed to generate report: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Store Intelligence Endpoints
# ---------------------------------------------------------------------------

ALLOWED_DOC_TYPES = {".pdf", ".txt", ".md", ".csv"}


@app.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Upload documents for Store Intelligence processing."""
    uploaded: List[DocumentInfo] = []

    for file in files:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_DOC_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type '{file_ext}'. Allowed: {', '.join(ALLOWED_DOC_TYPES)}",
            )

        content = await file.read()
        file_size = len(content)

        if file_size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}' exceeds 50MB limit",
            )

        doc_id = str(uuid.uuid4())

        # Upload to Spaces
        try:
            s3_client = get_spaces_client()
            s3_key = f"documents/{doc_id}/{file.filename}"
            s3_client.put_object(
                Bucket=SPACES_BUCKET,
                Key=s3_key,
                Body=content,
                ACL="private",
            )
            file_url = f"https://{SPACES_BUCKET}.{SPACES_REGION}.digitaloceanspaces.com/{s3_key}"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload '{file.filename}' to storage: {str(e)}",
            )

        # Create Document record
        doc = Document(
            id=doc_id,
            filename=file.filename,
            file_type=file_ext.lstrip("."),
            file_size_bytes=file_size,
            storage_url=file_url,
            processing_status="pending",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Process document (chunking + embedding)
        try:
            await store_intelligence_agent.process_document(
                document_id=doc_id,
                file_content=content,
                filename=file.filename,
                file_type=file_ext.lstrip("."),
                db=db,
            )
        except Exception as e:
            print(f"[ERROR] Document processing failed for {file.filename}: {e}")
            doc.processing_status = "failed"
            doc.error_message = str(e)
            db.commit()

        db.refresh(doc)
        uploaded.append(
            DocumentInfo(
                document_id=str(doc.id),
                filename=doc.filename,
                file_type=doc.file_type,
                file_size=doc.file_size_bytes,
                status=doc.processing_status,
                chunk_count=doc.chunk_count,
            )
        )

    return DocumentUploadResponse(documents=uploaded, total_uploaded=len(uploaded))


@app.post("/api/intelligence/ask", response_model=IntelligenceResponse)
async def ask_intelligence(
    request: IntelligenceRequest,
    db: Session = Depends(get_db),
):
    """RAG query endpoint for Store Intelligence."""
    if not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty",
        )

    result = await store_intelligence_agent.ask_question(
        question=request.question,
        db=db,
        max_sources=request.max_sources,
    )

    sources = [
        SourceReference(
            document_id=s["document_id"],
            filename=s["filename"],
            chunk_excerpt=s["chunk_excerpt"],
            relevance_score=s["relevance_score"],
        )
        for s in result.get("sources", [])
    ]

    return IntelligenceResponse(
        answer=result["answer"],
        sources=sources,
        model_used=result.get("model_used", "llama3-8b-instruct"),
    )


@app.get("/api/knowledge-base/status")
async def get_knowledge_base_status(db: Session = Depends(get_db)):
    """Return knowledge base statistics with DO KB details."""
    total_documents = db.query(Document).filter(
        Document.processing_status == "completed"
    ).count()
    total_chunks = db.query(DocumentChunk).count()

    index_health = await store_intelligence_agent.get_index_health()

    # Get last updated timestamp
    last_doc = (
        db.query(Document)
        .filter(Document.processing_status == "completed")
        .order_by(Document.created_at.desc())
        .first()
    )
    last_updated = last_doc.created_at.isoformat() if last_doc and last_doc.created_at else None

    # Get DO KB details
    kb_details = await store_intelligence_agent.get_kb_details()

    return {
        "total_documents": total_documents,
        "total_chunks": total_chunks,
        "index_health": index_health,
        "last_updated": last_updated,
        "kb_uuid": kb_details.get("uuid"),
        "kb_status": kb_details.get("status", "not_created"),
        "kb_name": kb_details.get("name"),
        "spaces_bucket": kb_details.get("spaces_bucket", os.getenv("DO_SPACES_BUCKET", "1donsspaces")),
        "spaces_region": kb_details.get("spaces_region", os.getenv("DO_SPACES_REGION", "nyc3")),
        "embedding_model": kb_details.get("embedding_model", "GTE Large v1.5"),
    }


@app.delete("/api/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    """Delete a document and all associated data."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # 1. Delete from OpenSearch (best-effort)
    await store_intelligence_agent.delete_document_embeddings(document_id)

    # 2. Delete from Spaces (best-effort)
    try:
        s3_client = get_spaces_client()
        s3_key = doc.storage_url.split(
            f"{SPACES_BUCKET}.{SPACES_REGION}.digitaloceanspaces.com/"
        )[1]
        s3_client.delete_object(Bucket=SPACES_BUCKET, Key=s3_key)
    except Exception as e:
        print(f"[WARN] Failed to delete file from Spaces: {e}")

    # 3. Delete from database (cascade deletes chunks)
    db.delete(doc)
    db.commit()

    return {"status": "deleted", "document_id": document_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


