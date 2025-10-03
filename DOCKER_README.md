# Docker Deployment Guide

This guide explains how to run MammoChat using Docker.

## Prerequisites

- Docker installed on your system
- API keys for DeepSeek (required) and HeySol (optional)

## Quick Start

1. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys
   ```

2. **Build and run with Docker Compose:**
   ```bash
   docker compose up --build
   ```

3. **Access the application:**
   Open your browser and go to `http://localhost:8080`

## Manual Docker Commands

If you prefer to use Docker directly:

```bash
# Build the image
docker build -t mammochat:latest .

# Run the container
docker run -d \
  --name mammochat \
  -p 8080:8080 \
  -e DEEPSEEK_API_KEY=your_api_key \
  -e HEYSOL_API_KEY=your_heysol_key \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/branding:/app/branding:ro \
  -v $(pwd)/prompts:/app/prompts:ro \
  mammochat:latest
```

## Configuration

### Application Configuration

The application uses these environment variables:

- `DEEPSEEK_API_KEY` (required): Your DeepSeek API key for chat functionality
- `HEYSOL_API_KEY` (optional): Your HeySol API key for memory features
- `APP_CONFIG_PATH` (optional): Path to config file (defaults to `config/app_config.json`)

### NAS Deployment Configuration

NAS deployment settings are configured in `config/nas_config.json`:

```json
{
  "nas": {
    "host": "your-nas.local",
    "user": "your-username",
    "path": "/volume1/docker/mammochat",
    "ssh_port": 22,
    "ssh_key": "~/.ssh/id_rsa",
    "docker_compose_file": "docker-compose.nas.yml"
  },
  "deployment": {
    "directories": ["config", "branding", "prompts", "data"],
    "files_to_copy": [
      "config/app_config.json",
      "branding",
      "prompts",
      "src",
      "main.py",
      "Dockerfile",
      "docker-compose.nas.yml",
      "requirements.txt",
      ".env"
    ]
  }
}
```

**Configuration Options:**

- **nas.host**: NAS hostname or IP address
- **nas.user**: SSH username for NAS authentication
- **nas.path**: Base directory for MammoChat on NAS
- **nas.ssh_port**: SSH port (default: 22)
- **nas.ssh_key**: Path to SSH private key file
- **deployment.directories**: Subdirectories to create on NAS
- **deployment.files_to_copy**: Files and directories to copy during deployment

## Volume Mounts

The Docker setup includes these volume mounts:

- `./config:/app/config:ro` - Application configuration
- `./branding:/app/branding:ro` - Logo and branding assets
- `./prompts:/app/prompts:ro` - System prompts

## NAS Deployment

MammoChat includes automated deployment to NAS Docker environments with persistent storage.

### Prerequisites for NAS Deployment

- NAS device with Docker support (Synology, QNAP, etc.)
- SSH access to NAS with key-based authentication
- `jq` installed on the deployment machine for JSON parsing

### Configuration

1. **Edit NAS configuration:**
   ```bash
   # Edit config/nas_config.json with your NAS settings
   {
     "nas": {
       "host": "your-nas.local",
       "user": "your-username",
       "path": "/volume1/docker/mammochat",
       "ssh_port": 22,
       "ssh_key": "~/.ssh/id_rsa",
       "docker_compose_file": "docker-compose.nas.yml"
     }
   }
   ```

2. **Deploy to NAS:**
   ```bash
   ./deploy_to_nas.sh
   ```

### NAS Deployment Features

- **Automated Setup**: Creates directories and copies all necessary files
- **Persistent Storage**: Config, branding, prompts, and data directories
- **Container Management**: Handles cleanup and restart of existing containers
- **Status Monitoring**: Shows container status and recent logs
- **Error Handling**: Comprehensive error reporting and troubleshooting

### Customizing NAS Deployment

The deployment reads configuration from `config/nas_config.json`:

- **host**: NAS hostname or IP address
- **user**: SSH username for NAS access
- **path**: Base path for MammoChat installation on NAS
- **ssh_port**: SSH port (default: 22)
- **ssh_key**: Path to SSH private key
- **docker_compose_file**: Docker Compose file to use for deployment

## Production Deployment

For production deployment, consider:

1. Using a reverse proxy (nginx)
2. Setting up SSL/TLS certificates
3. Using Docker secrets for API keys
4. Configuring proper logging and monitoring

## Troubleshooting

### General Issues

- **Port already in use:** Change the port mapping in docker-compose.yml
- **API key errors:** Ensure your `.env` file is properly configured
- **Permission errors:** Check that volume mount paths exist and have proper permissions

### NAS Deployment Issues

- **SSH connection failed:** Verify NAS host, username, and SSH key configuration in `config/nas_config.json`
- **Docker not found on NAS:** Ensure Docker is installed and running on your NAS device
- **Permission denied:** Check that the SSH key has appropriate permissions and NAS user has Docker access
- **jq not found:** Install jq on your deployment machine: `sudo apt-get install jq` (Ubuntu/Debian) or `brew install jq` (macOS)