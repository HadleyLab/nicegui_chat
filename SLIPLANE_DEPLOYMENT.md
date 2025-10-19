# Sliplane Deployment Guide

This guide explains how to deploy the NiceGUI Chat Application to sliplane.io.

## Overview

The application is configured for deployment on sliplane.io with the following components:

- **sliplane.yml**: Main deployment configuration
- **.env.sliplane**: Environment variables and secrets
- **scripts/deploy_to_sliplane.sh**: Automated deployment script
- **Dockerfile**: Optimized for sliplane deployment
- **docker-compose.sliplane.yml**: Docker Compose configuration for sliplane

## Prerequisites

1. **Sliplane Account**: Sign up at [sliplane.io](https://sliplane.io)
2. **API Keys**: Obtain your DeepSeek and HeySol API keys
3. **Docker**: Ensure Docker is installed and running
4. **Git**: Ensure Git is installed

## Quick Start

### 1. Configure Environment Variables

Copy the example environment file and update it with your actual values:

```bash
cp .env.sliplane .env.sliplane.local
```

Edit `.env.sliplane.local` and replace the placeholder values:

```bash
# Replace these with your actual API keys
DEEPSEEK_API_KEY=your_actual_deepseek_api_key
HEYSOL_API_KEY=your_actual_heysol_api_key

# Update app name if needed
SLIPLANE_APP_NAME=your-unique-app-name
```

### 2. Deploy Using the Script

Run the deployment script:

```bash
./scripts/deploy_to_sliplane.sh
```

The script will:
- Validate configuration files
- Build the Docker image
- Attempt to deploy to sliplane (or create deployment manifest if CLI not available)

### 3. Manual Deployment (Alternative)

If the automated script doesn't work, you can deploy manually:

1. **Build the Docker image**:
   ```bash
   docker build -f Dockerfile -t your-app-name:latest .
   ```

2. **Push to a registry** (if using external registry):
   ```bash
   docker tag your-app-name:latest your-registry/your-app-name:latest
   docker push your-registry/your-app-name:latest
   ```

3. **Deploy via sliplane dashboard**:
   - Go to [sliplane.io dashboard](https://dashboard.sliplane.io)
   - Create a new application
   - Use the provided `sliplane.yml` configuration
   - Set your environment variables and secrets

## Configuration Files

### sliplane.yml

Main deployment configuration including:
- Application metadata
- Resource limits and requests
- Health checks
- Environment variables
- Security settings

### .env.sliplane

Environment variables template including:
- API keys (as secrets)
- Application settings
- Logging configuration
- Security settings

### docker-compose.sliplane.yml

Docker Compose configuration optimized for sliplane:
- Multi-replica deployment
- Health checks
- Resource management
- Logging configuration

## Environment Variables

### Required Secrets (Set in Sliplane Dashboard)

| Variable | Description | Required |
|----------|-------------|----------|
| `DEEPSEEK_API_KEY` | DeepSeek API key for AI chat | Yes |
| `HEYSOL_API_KEY` | HeySol API key for additional features | Yes |

### Optional Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARN, ERROR) | INFO |
| `PORT` | Application port | 8080 |
| `ENVIRONMENT` | Environment (development, production) | production |
| `SLIPLANE_REPLICAS` | Number of replicas | 2 |

## Deployment Process

### Automated Deployment

The deployment script handles:
1. **Validation**: Checks configuration files and environment
2. **Build**: Creates optimized Docker image
3. **Deploy**: Pushes to sliplane and starts the application
4. **Verification**: Validates deployment success

### Manual Deployment Steps

1. **Build Docker Image**:
   ```bash
   docker build -f Dockerfile -t your-app-name:latest .
   ```

2. **Test Locally** (Optional):
   ```bash
   docker run -p 8080:8080 --env-file .env.sliplane.local your-app-name:latest
   ```

3. **Deploy to Sliplane**:
   - Use the sliplane dashboard
   - Upload `sliplane.yml` configuration
   - Set environment variables and secrets
   - Deploy the application

## Monitoring and Troubleshooting

### Health Checks

The application includes health check endpoints:
- **Liveness**: `/health` - Checks if application is running
- **Readiness**: `/health` - Checks if application is ready to serve requests

### Logs

Access logs through:
- Sliplane dashboard logs section
- Docker logs (if running locally)
- Application logs in `/app/logs/` directory

### Common Issues

1. **Build Failures**:
   - Check Docker is running
   - Verify all dependencies in `requirements.txt`
   - Check available disk space

2. **Deployment Failures**:
   - Verify API keys are correct
   - Check sliplane account limits
   - Validate configuration syntax

3. **Runtime Errors**:
   - Check environment variables
   - Verify API key permissions
   - Check application logs for errors

## Security Considerations

- API keys are stored as secrets in sliplane
- Application runs as non-root user
- Minimal attack surface with slim Docker image
- Health checks don't expose sensitive information

## Scaling

The application is configured for horizontal scaling:
- Default: 2 replicas
- Configurable resource limits
- Rolling deployment strategy
- Health check validation

## Backup and Recovery

- Application data is stateless by design
- Configuration backups recommended
- Environment variables should be documented separately

## Support

For issues with:
- **Application**: Check application logs and health endpoints
- **Deployment**: Review sliplane dashboard and deployment logs
- **Configuration**: Validate YAML syntax and environment variables

## Updates

To update the application:

1. Make your code changes
2. Update version in `sliplane.yml` if needed
3. Run the deployment script again:
   ```bash
   ./scripts/deploy_to_sliplane.sh
   ```

The deployment uses rolling updates to minimize downtime.