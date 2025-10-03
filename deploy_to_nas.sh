#!/bin/bash

# MammoChat NAS Deployment Script
# This script deploys MammoChat to NAS Docker with persistent storage

set -e  # Exit on any error

echo "🚀 Deploying MammoChat to NAS Docker..."

# Configuration
NAS_HOST="nas.local"
NAS_USER="idrdex"
NAS_PATH="/volume1/docker/mammochat"
DOCKER_COMPOSE_FILE="docker-compose.nas.yml"
SSH_KEY="~/.ssh/id_ed25519"  # Ed25519 key for NAS connection

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[NAS]${NC} $1"
}

# Function to run SSH commands
ssh_cmd() {
    ssh -p 2222 -i "$SSH_KEY" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR "$NAS_USER@$NAS_HOST" "$1"
}

# Function to copy files to NAS
scp_to_nas() {
    scp -P 2222 -i "$SSH_KEY" -o StrictHostKeyChecking=no -r "$1" "$NAS_USER@$NAS_HOST:$2"
}

# Function to copy single files to NAS
scp_file_to_nas() {
    scp -P 2222 -i "$SSH_KEY" -o StrictHostKeyChecking=no "$1" "$NAS_USER@$NAS_HOST:$2"
}

# Function to copy files with directory creation
scp_file_to_dir() {
    local file="$1"
    local dest_dir="$2"
    # Create directory first, then copy file
    ssh_cmd "mkdir -p \"$dest_dir\""
    scp -P 2222 -i "$SSH_KEY" -o StrictHostKeyChecking=no "$file" "$NAS_USER@$NAS_HOST:$dest_dir/"
}

print_status "Connecting to NAS at $NAS_HOST..."

# Create necessary directories on NAS
print_status "Creating directories on NAS..."
ssh_cmd "mkdir -p $NAS_PATH"
ssh_cmd "mkdir -p $NAS_PATH/{config,branding,prompts,data}"

# Copy all necessary files to NAS using tar (most reliable method)
print_status "Copying all application files to NAS..."

# Create a tar archive of all necessary files and pipe it to NAS
tar -czf - \
    config/app_config.json \
    branding \
    prompts \
    src \
    main.py \
    Dockerfile \
    "$DOCKER_COMPOSE_FILE" \
    requirements.txt \
    .env \
    2>/dev/null | ssh_cmd "cd $NAS_PATH && tar -xzf -"

print_status "✓ Copied all application files"

# Create .dockerignore for NAS deployment
print_status "Creating .dockerignore for NAS deployment..."
DOCKERIGNORE_CONTENT=".git
.gitignore
README.md
.env
.env.example
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.pytest_cache
nosetests.xml
coverage.xml
*.cover
*.log
.venv
.mypy_cache
.ruff_cache
.DS_Store
deploy_to_nas.sh"

ssh_cmd "cat > $NAS_PATH/.dockerignore << 'EOF'
$DOCKERIGNORE_CONTENT
EOF"

print_status "✓ Created .dockerignore"

# Set proper permissions on NAS
print_status "Setting proper permissions on NAS files..."
ssh_cmd "find $NAS_PATH -type d -not -path '*/@eaDir/*' -exec chmod 755 {} \\;"
ssh_cmd "find $NAS_PATH -type f -not -path '*/@eaDir/*' -name 'app_config.json' -exec chmod 644 {} \\;"
ssh_cmd "find $NAS_PATH -type f -not -path '*/@eaDir/*' -name '*.md' -exec chmod 644 {} \\;"
ssh_cmd "find $NAS_PATH -type f -not -path '*/@eaDir/*' -name '*.py' -exec chmod 644 {} \\;"

# Build and run on NAS
print_status "Building and starting MammoChat on NAS Docker..."

# Clean up any existing containers first
print_status "Cleaning up existing containers..."
ssh_cmd "cd $NAS_PATH && /usr/local/bin/docker-compose -f $DOCKER_COMPOSE_FILE down" 2>/dev/null || true

# Build and start the container with non-interactive flags
BUILD_OUTPUT=$(ssh_cmd "cd $NAS_PATH && echo 'y' | /usr/local/bin/docker-compose -f $DOCKER_COMPOSE_FILE up --build -d" 2>&1)
BUILD_EXIT_CODE=$?

if [ $BUILD_EXIT_CODE -eq 0 ]; then
    print_status "✅ Docker build completed successfully"
else
    print_error "❌ Docker build failed"
    print_error "Build output:"
    echo "$BUILD_OUTPUT"
    exit 1
fi

# Wait for container to be ready
print_status "Waiting for MammoChat to start..."
sleep 20

# Check if container is running
print_info "Checking container status..."
CONTAINER_STATUS=$(ssh_cmd "cd $NAS_PATH && /usr/local/bin/docker-compose -f $DOCKER_COMPOSE_FILE ps" 2>/dev/null)

if echo "$CONTAINER_STATUS" | grep -q "Up"; then
    print_status "✅ MammoChat successfully deployed to NAS Docker!"
    print_status "📱 Access your application at: http://$NAS_HOST:8080"

    # Show container status
    echo
    print_status "Container status:"
    ssh_cmd "cd $NAS_PATH && /usr/local/bin/docker-compose -f $DOCKER_COMPOSE_FILE ps"

    # Show recent logs
    echo
    print_status "Recent logs:"
    ssh_cmd "cd $NAS_PATH && /usr/local/bin/docker-compose -f $DOCKER_COMPOSE_FILE logs --tail 10"

else
    print_error "❌ Failed to start MammoChat container"
    print_error "Container status:"
    echo "$CONTAINER_STATUS"

    # Show logs to help debug
    echo
    print_error "Container logs:"
    ssh_cmd "cd $NAS_PATH && /usr/local/bin/docker-compose -f $DOCKER_COMPOSE_FILE logs" 2>/dev/null || echo "Could not retrieve logs"

    exit 1
fi

print_status "🎉 Deployment complete!"
print_status "Your files are stored in: $NAS_HOST:$NAS_PATH"
print_status "Application accessible at: http://$NAS_HOST:8080"