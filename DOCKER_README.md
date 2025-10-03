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

The application uses these environment variables:

- `DEEPSEEK_API_KEY` (required): Your DeepSeek API key for chat functionality
- `HEYSOL_API_KEY` (optional): Your HeySol API key for memory features
- `APP_CONFIG_PATH` (optional): Path to config file (defaults to `config/app_config.json`)

## Volume Mounts

The Docker setup includes these volume mounts:

- `./config:/app/config:ro` - Application configuration
- `./branding:/app/branding:ro` - Logo and branding assets
- `./prompts:/app/prompts:ro` - System prompts

## Production Deployment

For production deployment, consider:

1. Using a reverse proxy (nginx)
2. Setting up SSL/TLS certificates
3. Using Docker secrets for API keys
4. Configuring proper logging and monitoring

## Troubleshooting

- **Port already in use:** Change the port mapping in docker-compose.yml
- **API key errors:** Ensure your `.env` file is properly configured
- **Permission errors:** Check that volume mount paths exist and have proper permissions