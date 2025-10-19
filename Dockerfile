# Production Dockerfile optimized for sliplane.io deployment
FROM python:3.11-slim

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONOPTIMIZE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8080 \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO

# Install minimal system dependencies for production
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create application user for security
RUN groupadd -r -g 1000 appuser && useradd -r -u 1000 -g appuser appuser

# Set work directory
WORKDIR /app

# Copy dependency files first for better layer caching
COPY requirements.txt ./

# Install Python dependencies using pip for broader compatibility
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/tmp && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Create volume mount points
VOLUME ["/app/logs", "/app/data"]

# Expose port
EXPOSE 8080

# Health check for production - optimized for sliplane
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Add labels for sliplane deployment
LABEL org.opencontainers.image.title="NiceGUI Chat Application" \
      org.opencontainers.image.description="A modern chat application built with NiceGUI and Python" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="Sliplane" \
      org.opencontainers.image.source="https://github.com/your-username/nicegui-chat" \
      org.opencontainers.image.licenses="MIT"

# Default command for production
CMD ["python", "main.py"]