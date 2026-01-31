#!/bin/bash
# Bash Deployment Script for Offer Automation
# Supports AWS ECS deployments
# Usage: ./deploy.sh [ecs|build-only] [--skip-build] [--tag latest]

set -e  # Exit on error

# Parse arguments
TARGET="${1:-ecs}"
SKIP_BUILD=false
TAG="latest"

shift || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Output functions
success() { echo -e "${GREEN}$1${NC}"; }
info() { echo -e "${CYAN}$1${NC}"; }
warn() { echo -e "${YELLOW}$1${NC}"; }
error() { echo -e "${RED}$1${NC}"; exit 1; }

# --- Configuration ---
AWS_REGION="eu-central-1"
AWS_ACCOUNT_ID="039612872461"
ECR_REPOSITORY_NAME="offer-automation"
IMAGE_TAG="$TAG"
ECS_CLUSTER_NAME="offer-automation-cluster"
ECS_SERVICE_NAME="offer-automation-service"
# --- End of Configuration ---

# Construct the full ECR repository URI
ECR_REPOSITORY_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"
LOCAL_IMAGE_NAME="${ECR_REPOSITORY_NAME}:${IMAGE_TAG}"
ECR_IMAGE_URI="${ECR_REPOSITORY_URI}:${IMAGE_TAG}"

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TASK_DEF_FILE="${SCRIPT_DIR}/task-definition-exec.json"

info "========================================="
info "Offer Automation Deployment"
info "========================================="
info "Target: $TARGET"
info "Tag: $TAG"
info "Skip Build: $SKIP_BUILD"
echo ""

# Function to deploy to ECS
deploy_to_ecs() {
    info "Starting ECS deployment..."

    # Build if not skipped
    if [ "$SKIP_BUILD" = false ]; then
        info "Step 1/6: Building Docker image '${LOCAL_IMAGE_NAME}' for linux/amd64..."
        cd "$PROJECT_ROOT"
        docker build --platform linux/amd64 -f docker/Dockerfile -t "$LOCAL_IMAGE_NAME" -t "$ECR_IMAGE_URI" . || error "Docker build failed"
        success "Docker image built successfully."
    fi

    # Log in to AWS ECR
    info "Step 2/6: Logging in to ECR..."
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com" || \
        error "ECR login failed"
    success "ECR login successful."

    # Tag the Docker image for ECR (if not already tagged during build)
    info "Step 3/6: Tagging image for ECR..."
    docker tag "$LOCAL_IMAGE_NAME" "$ECR_IMAGE_URI" || error "Image tagging failed"
    success "Image tagged."

    # Push to ECR
    info "Step 4/6: Pushing image to ECR..."
    docker push "$ECR_IMAGE_URI" || error "Push to ECR failed"
    success "Image pushed to ECR."

    # Register task definition
    info "Step 5/6: Registering task definition..."
    aws ecs register-task-definition \
        --cli-input-json "file://${TASK_DEF_FILE}" \
        --region "$AWS_REGION" > /dev/null || error "Task definition registration failed"
    success "Task definition registered."

    # Update service with deployment configuration for auto-restart
    info "Step 6/6: Updating ECS service with auto-restart configuration..."
    aws ecs update-service \
        --cluster "$ECS_CLUSTER_NAME" \
        --service "$ECS_SERVICE_NAME" \
        --task-definition offer-automation \
        --desired-count 1 \
        --force-new-deployment \
        --deployment-configuration "maximumPercent=200,minimumHealthyPercent=100,deploymentCircuitBreaker={enable=true,rollback=true}" \
        --region "$AWS_REGION" > /dev/null || {
            warn "Service update failed. The service might not exist yet."
            warn "If this is your first deployment, create the service with:"
            warn ""
            warn "aws ecs create-service \\"
            warn "    --cluster $ECS_CLUSTER_NAME \\"
            warn "    --service-name $ECS_SERVICE_NAME \\"
            warn "    --task-definition offer-automation \\"
            warn "    --desired-count 1 \\"
            warn "    --launch-type FARGATE \\"
            warn "    --network-configuration \"awsvpcConfiguration={subnets=[subnet-09d79a6dab2f2076f,subnet-09e9658bdd8b1e2bb,subnet-0add62f70e433ba37],securityGroups=[sg-009b8558fdd076f22],assignPublicIp=ENABLED}\" \\"
            warn "    --region $AWS_REGION"
            warn ""
            error "Deployment failed at service update step"
        }
    success "ECS service updated with auto-restart enabled!"

    success ""
    success "✅ ECS deployment completed successfully!"
    info "Monitor: https://console.aws.amazon.com/ecs/home?region=${AWS_REGION}#/clusters/${ECS_CLUSTER_NAME}/services/${ECS_SERVICE_NAME}/deployments"
}

# Function to build only
build_only() {
    info "Building Docker image only for linux/amd64..."
    cd "$PROJECT_ROOT"
    docker build --platform linux/amd64 -f docker/Dockerfile -t "$LOCAL_IMAGE_NAME" . || error "Docker build failed"
    success "Build completed!"
}

# Main execution
case "$TARGET" in
    ecs)
        deploy_to_ecs
        ;;
    build-only)
        build_only
        ;;
    *)
        error "Invalid target: $TARGET. Usage: ./deploy.sh [ecs|build-only] [--skip-build] [--tag latest]"
        ;;
esac
