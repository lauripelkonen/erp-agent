#!/bin/bash
set -e

# Default environment variables
export PORT=${PORT:-8080}
export PYTHONPATH="/app/src:${PYTHONPATH}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[ENTRYPOINT]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[ENTRYPOINT]${NC} $1"
}

error() {
    echo -e "${RED}[ENTRYPOINT]${NC} $1"
}


# Function to run the REST API server (default for Fargate)
run_api() {
    log "Starting REST API server on port $PORT..."
    log "ERP Type: ${ERP_TYPE:-csv}"
    exec uvicorn src.api.main:app --host 0.0.0.0 --port $PORT --log-level info
}

# Function to run the FastAPI webhook server
run_webhook() {
    log "Starting Enhanced FastAPI webhook server on port $PORT..."
    exec uvicorn src.api.enhanced_webhook:app --host 0.0.0.0 --port $PORT --log-level info
}

# Function to run the main automation system
run_automation() {
    log "Starting Offer Automation System..."
    exec python src/main.py
}

# Function to run Gmail setup
run_gmail_setup() {
    log "Running Gmail setup..."
    exec python scripts/setup-gmail.py "$@"
}


# Determine what to run based on command line arguments or environment
case "${1:-api}" in
    api)
        run_api
        ;;
    webhook)
        run_webhook
        ;;
    automation)
        run_automation
        ;;
    gmail-setup)
        shift
        run_gmail_setup "$@"
        ;;
    *)
        echo "Usage: $0 {api|webhook|automation|gmail-setup}"
        echo "  api          - Start REST API server (default)"
        echo "  webhook      - Start FastAPI webhook server"
        echo "  automation   - Start main automation system"
        echo "  gmail-setup  - Run Gmail push notification setup"
        exit 1
        ;;
esac 