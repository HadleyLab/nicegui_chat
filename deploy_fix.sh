#!/bin/bash
echo "=== MammoChat NAS Deployment Fix ==="

# Clean deployment directory
echo "Cleaning deployment directory..."
rm -rf /volume1/docker/mammochat
mkdir -p /volume1/docker/mammochat
chmod 755 /volume1/docker/mammochat
cd /volume1/docker/mammochat

# Create main application files
echo "Creating main.py..."
cat > main.py << 'MAIN_EOF'
"""Main application entry point for MammoChat."""

from nicegui import app, ui

from src.__version__ import __version__
from src.config import load_app_config
from src.services.auth_service import AuthService
from src.services.chat_service import ChatService
from src.services.memory_service import MemoryService
from src.ui.chat_ui import ChatUI


def main() -> None:
    """Main application entry point."""
    # Load configuration
    config = load_app_config()

    # Add static files for branding
    app.add_static_files("/branding", "branding")

    # Initialize services
    auth_service = AuthService(config.heysol)
    memory_service = MemoryService(auth_service)
    chat_service = ChatService(auth_service, memory_service, config)

    # Check authentication
    if not auth_service.is_authenticated:
        ui.notify(
            "Warning: HeySol API key not configured. Memory features will be disabled.",
            type="warning",
            timeout=5000,
        )

    # Build UI
    @ui.page("/")
    def index() -> None:
        """Main page."""
        chat_ui = ChatUI(config, auth_service, chat_service, memory_service)
        chat_ui.build()

    # Run the application
    print(f"Starting MammoChat v{__version__}")
    ui.run(
        title=f"{config.app.name} v{__version__}",
        host=config.app.host,
        port=config.app.port,
        reload=config.app.reload,
        dark=True,
        favicon="💗",
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
MAIN_EOF

echo "Creating requirements.txt..."
cat > requirements.txt << 'REQ_EOF'
nicegui>=1.4.0
pydantic>=2.7.0
pydantic-ai>=0.8.0,<1.0
python-dotenv>=1.0.0
heysol-api-client>=1.2.1
structlog>=24.1.0
aiofiles>=23.0.0
REQ_EOF

echo "Creating Dockerfile..."
cat > Dockerfile << 'DOCKER_EOF'
# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/', timeout=10)" || exit 1

# Run the application
CMD ["python", "main.py"]
DOCKER_EOF

echo "Creating docker-compose.yml..."
cat > docker-compose.yml << 'COMPOSE_EOF'
services:
  mammochat:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - HEYSOL_API_KEY=${HEYSOL_API_KEY}
      - APP_CONFIG_PATH=${APP_CONFIG_PATH:-config/app_config.json}
    volumes:
      - ./config:/app/config:ro
      - ./branding:/app/branding:ro
      - ./prompts:/app/prompts:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8080/', timeout=10)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
COMPOSE_EOF

echo "Creating .env file..."
cat > .env << 'ENV_EOF'
# DeepSeek API configuration (Required for chat functionality)
DEEPSEEK_API_KEY=sk-043566a9f0ce41099fd1dd0c19c025fe

# HeySol API keys (Optional but recommended for memory features)
HEYSOL_API_KEY=rc_pat_e6qbnv7mq4a3j538ghq3gidc6r5m268i1iz413hu
HEYSOL_API_KEY_IDRDEX_MAMMOCHAT=rc_pat_e6qbnv7mq4a3j538ghq3gidc6r5m268i1iz413hu

# Configuration
APP_CONFIG_PATH=config/app_config.json
ENV_EOF

echo "=== Files created successfully! ==="
ls -la

echo "=== Testing Docker build ==="
/usr/local/bin/docker compose up --build -d

echo "=== Deployment complete! ==="
echo "Access your app at: http://nas.local:8080"
/usr/local/bin/docker ps | grep mammochat
