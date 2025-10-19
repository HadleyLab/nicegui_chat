#!/bin/bash

# Sliplane Deployment Script
# This script deploys the NiceGUI chat application to sliplane.io

# Strict error handling - fail immediately on any error
set -e
set -o pipefail

# Get the absolute path to the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $*"
}

# Error handler
error_exit() {
    log_error "$1"
    exit 1
}

# Configuration
CONFIG_FILE="$PROJECT_ROOT/sliplane.yml"
ENV_FILE="$PROJECT_ROOT/.env.sliplane.local"

# Validate configuration files exist
if [[ ! -f "$CONFIG_FILE" ]]; then
    error_exit "Sliplane configuration file not found: $CONFIG_FILE"
fi

if [[ ! -f "$ENV_FILE" ]]; then
    error_exit "Environment file not found: $ENV_FILE"
fi

# Load environment variables
log_info "Loading environment configuration from $ENV_FILE"
if ! source "$ENV_FILE"; then
    error_exit "Failed to load environment file: $ENV_FILE"
fi

# Validate required environment variables
REQUIRED_VARS=(
    "SLIPLANE_APP_NAME"
    "DEEPSEEK_API_KEY"
    "HEYSOL_API_KEY"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        error_exit "Required environment variable $var is not set"
    fi
done

# Check if sliplane CLI is available
check_sliplane_cli() {
    if command -v sliplane &> /dev/null; then
        log_info "Sliplane CLI found"
        return 0
    else
        log_warn "Sliplane CLI not found. Installing..."

        # Try to install sliplane CLI
        if command -v npm &> /dev/null; then
            log_info "Installing sliplane CLI via npm..."
            npm install -g @sliplane/cli || {
                log_warn "npm installation failed, trying alternative methods..."
                return 1
            }
        elif command -v curl &> /dev/null; then
            log_info "Trying to download sliplane CLI..."
            curl -fsSL https://get.sliplane.io | bash || {
                log_warn "curl installation failed"
                return 1
            }
        else
            log_error "Cannot install sliplane CLI. Please install manually."
            return 1
        fi
    fi
}

# Build Docker image
build_image() {
    log_info "Building Docker image for sliplane deployment..."

    # Check if we're in the correct directory
    cd "$PROJECT_ROOT"

    # Build the image
    local image_name="$SLIPLANE_APP_NAME:latest"
    log_info "Building image: $image_name"

    if ! docker build -f Dockerfile -t "$image_name" .; then
        error_exit "Failed to build Docker image"
    fi

    log_info "Docker image built successfully: $image_name"
}

# Deploy to sliplane
deploy_to_sliplane() {
    log_info "Deploying to sliplane..."

    # Check if sliplane CLI is available
    if ! check_sliplane_cli; then
        log_warn "Sliplane CLI not available. Creating deployment manifest instead..."

        # Create a deployment manifest that can be used manually
        create_deployment_manifest
        return 0
    fi

    # Login to sliplane (if required)
    if [[ -n "${SLIPLANE_API_TOKEN:-}" ]]; then
        log_info "Logging in to sliplane..."
        if ! sliplane login --token "$SLIPLANE_API_TOKEN"; then
            error_exit "Failed to login to sliplane"
        fi
    fi

    # Deploy the application
    log_info "Deploying application: $SLIPLANE_APP_NAME"

    if sliplane deploy \
        --config "$CONFIG_FILE" \
        --env "$ENV_FILE" \
        --image "$SLIPLANE_APP_NAME:latest" \
        --yes; then

        log_info "Deployment initiated successfully!"
        log_info "You can monitor the deployment at: https://dashboard.sliplane.io"

    else
        error_exit "Deployment failed"
    fi
}

# Create deployment manifest for manual deployment
create_deployment_manifest() {
    log_info "Creating deployment manifest..."

    local manifest_file="$PROJECT_ROOT/sliplane-deployment.json"

    cat > "$manifest_file" << EOF
{
  "name": "$SLIPLANE_APP_NAME",
  "version": "$APP_VERSION",
  "description": "NiceGUI Chat Application",
  "image": "$SLIPLANE_APP_NAME:latest",
  "port": $APP_PORT,
  "healthCheckPath": "$HEALTH_CHECK_PATH",
  "environment": {
    "PYTHONUNBUFFERED": "$PYTHONUNBUFFERED",
    "PYTHONDONTWRITEBYTECODE": "$PYTHONDONTWRITEBYTECODE",
    "PYTHONOPTIMIZE": "$PYTHONOPTIMIZE",
    "LOG_LEVEL": "$LOG_LEVEL",
    "ENVIRONMENT": "$ENVIRONMENT",
    "DEBUG": "$DEBUG"
  },
  "secrets": [
    "DEEPSEEK_API_KEY",
    "HEYSOL_API_KEY"
  ],
  "resources": {
    "memory": "512Mi",
    "cpu": "250m"
  },
  "replicas": 2,
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

    log_info "Deployment manifest created: $manifest_file"
    log_info "You can use this file to deploy manually through the sliplane dashboard"
}

# Validate deployment
validate_deployment() {
    log_info "Validating deployment configuration..."

    # Check if Docker image exists
    log_info "Checking for Docker image: $SLIPLANE_APP_NAME:latest"
    if ! docker images | grep -q "$SLIPLANE_APP_NAME"; then
        log_error "Docker image not found. Available images:"
        docker images
        error_exit "Docker image not found. Please build the image first."
    fi

    # Validate configuration files
    if ! command -v python3 &> /dev/null; then
        log_warn "Python3 not found. Skipping YAML validation."
    else
        log_info "Validating YAML configuration..."
        if python3 -c "import yaml; yaml.safe_load(open('$CONFIG_FILE'))" 2>/dev/null; then
            log_info "YAML configuration is valid"
        else
            log_warn "YAML configuration may have issues"
        fi
    fi

    log_info "Validation completed"
}

# Main deployment flow
main() {
    log_info "Starting sliplane deployment process..."

    # Validate configuration
    validate_deployment

    # Build Docker image
    build_image

    # Deploy to sliplane
    deploy_to_sliplane

    log_info "Sliplane deployment process completed!"
    log_info ""
    log_info "Next steps:"
    log_info "1. Monitor your deployment at: https://dashboard.sliplane.io"
    log_info "2. Update your DNS settings if needed"
    log_info "3. Configure SSL certificates in the sliplane dashboard"
    log_info "4. Set up monitoring and alerting"
}

# Run main function
main "$@"