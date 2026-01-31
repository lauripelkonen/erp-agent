# PowerShell Deployment Script for Offer Automation
# Supports AWS ECS deployments
# Usage: .\deploy.ps1 [ecs|build-only] [-SkipBuild] [-Environment production]

param(
    [Parameter(Position=0)]
    [ValidateSet("ecs", "docker", "local", "build-only")]
    [string]$Target = "ecs",
    
    [Parameter()]
    [string]$Environment = "production",
    
    [Parameter()]
    [switch]$SkipBuild,
    
    [Parameter()]
    [switch]$Force,
    
    [Parameter()]
    [string]$Tag = "latest"
)

# Stop on any error
$ErrorActionPreference = "Stop"

# Color output functions
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

# --- Configuration ---
$AWS_REGION = "eu-central-1"
$AWS_ACCOUNT_ID = "039612872461"
$ECR_REPOSITORY_NAME = "offer-automation"
$IMAGE_TAG = $Tag
$ECS_CLUSTER_NAME = "offer-automation-cluster"
$ECS_SERVICE_NAME = "offer-automation-service"
# --- End of Configuration ---

# Construct the full ECR repository URI
$ECR_REPOSITORY_URI = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"
$LOCAL_IMAGE_NAME = "${ECR_REPOSITORY_NAME}:${IMAGE_TAG}"
$ECR_IMAGE_URI = "${ECR_REPOSITORY_URI}:${IMAGE_TAG}"

# Paths
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR
$TASK_DEF_FILE = Join-Path $SCRIPT_DIR "task-definition-exec.json"
$ENV_FILE = Join-Path $PROJECT_ROOT ".env"

Write-Info "=========================================" 
Write-Info "Offer Automation Deployment"
Write-Info "=========================================" 
Write-Info "Target: $Target"
Write-Info "Environment: $Environment"
Write-Info "Tag: $Tag"
Write-Info ""

# Function to deploy to ECS
function Deploy-ToECS {
    Write-Info "Starting ECS deployment..."
    
    # Build if not skipped
    if (!$SkipBuild) {
        Write-Info "Step 1/6: Building Docker image '${LOCAL_IMAGE_NAME}'..."
        Set-Location $PROJECT_ROOT
        docker build -f docker/Dockerfile -t $LOCAL_IMAGE_NAME -t $ECR_IMAGE_URI .
        if ($LASTEXITCODE -ne 0) { throw "Docker build failed" }
        Write-Success "Docker image built successfully."
    }
    
    # Log in to AWS ECR
    Write-Info "Step 2/6: Logging in to ECR..."
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    if ($LASTEXITCODE -ne 0) { throw "ECR login failed" }
    Write-Success "ECR login successful."
    
    # Tag the Docker image for ECR (if not already tagged during build)
    Write-Info "Step 3/6: Tagging image for ECR..."
    docker tag $LOCAL_IMAGE_NAME $ECR_IMAGE_URI
    Write-Success "Image tagged."
    
    # Push to ECR
    Write-Info "Step 4/6: Pushing image to ECR..."
    docker push $ECR_IMAGE_URI
    if ($LASTEXITCODE -ne 0) { throw "Push to ECR failed" }
    Write-Success "Image pushed to ECR."
    
    # Register task definition
    Write-Info "Step 5/6: Registering task definition..."
    aws ecs register-task-definition --cli-input-json file://$TASK_DEF_FILE --region $AWS_REGION > $null
    if ($LASTEXITCODE -ne 0) { throw "Task definition registration failed" }
    Write-Success "Task definition registered."
    
    # Update service with deployment configuration for auto-restart
    Write-Info "Step 6/6: Updating ECS service with auto-restart configuration..."
    aws ecs update-service `
        --cluster $ECS_CLUSTER_NAME `
        --service $ECS_SERVICE_NAME `
        --task-definition offer-automation `
        --desired-count 1 `
        --force-new-deployment `
        --deployment-configuration "maximumPercent=200,minimumHealthyPercent=100,deploymentCircuitBreaker={enable=true,rollback=true}" `
        --region $AWS_REGION > $null
    if ($LASTEXITCODE -ne 0) { throw "Service update failed" }
    Write-Success "ECS service updated with auto-restart enabled!"
    
    Write-Success "`n✅ ECS deployment completed successfully!"
    Write-Info "Monitor: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$ECS_CLUSTER_NAME/services/$ECS_SERVICE_NAME/deployments"
}

# Function to deploy with Docker Compose
function Deploy-DockerCompose {
    Write-Error "Docker Compose deployment is not available."
    Write-Info "docker-compose.yml has been removed. This deployment method is no longer supported."
    Write-Info "Please use: .\deploy.ps1 ecs"
    exit 1
}

# Main execution
try {
    switch ($Target) {
        "ecs" {
            Deploy-ToECS
        }
        "docker" {
            Deploy-DockerCompose
        }
        "local" {
            Deploy-DockerCompose
        }
        "build-only" {
            Set-Location $PROJECT_ROOT
            docker build -f docker/Dockerfile -t $LOCAL_IMAGE_NAME .
            Write-Success "Build completed!"
        }
        default {
            Write-Error "Invalid target: $Target"
            Write-Info "Usage: .\deploy.ps1 [ecs|build-only]"
            exit 1
        }
    }
}
catch {
    Write-Error "Deployment failed: $_"
    exit 1
} 