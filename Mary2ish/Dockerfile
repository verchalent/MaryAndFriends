# Mary 2.0ish - Embeddable AI Chat & Web GUI
# Multi-stage Dockerfile for optimized containerized deployment

# Stage 1: Builder stage
FROM python:3.13-slim AS builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv for package management
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen

# Stage 2: Runtime stage
FROM python:3.13-slim AS runtime

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Install uv in runtime stage
RUN pip install --no-cache-dir uv

# Copy Python environment from builder stage
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy dependency files
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser main.py ./

# Copy example configuration files as defaults (can be overridden by mounting)
COPY --chown=appuser:appuser config_examples/fastagent.config.yaml ./fastagent.config.yaml
COPY --chown=appuser:appuser config_examples/system_prompt.txt ./system_prompt.txt
COPY --chown=appuser:appuser config_examples/ui.config.yaml ./ui.config.yaml
COPY --chown=appuser:appuser config_examples/knowledge_facts.txt.example ./knowledge_facts.txt
COPY --chown=appuser:appuser config_examples/fastagent.secrets.yaml.example ./fastagent.secrets.yaml

# Create directories for user cache
RUN mkdir -p /home/appuser/.cache && \
    chown -R appuser:appuser /app /home/appuser

# Switch to non-root user
USER appuser

# Expose Streamlit port
EXPOSE 8501

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Entry point to run the Streamlit application
CMD ["uv", "run", "streamlit", "run", "main.py"]
