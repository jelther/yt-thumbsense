# Build stage
FROM python:3.13-slim as builder

# Add labels
LABEL org.opencontainers.image.source="https://github.com/jelther/yt_thumbsense"
LABEL org.opencontainers.image.description="An AI-powered YouTube API that predicts likes/dislikes ratios through comment sentiment analysis."
LABEL org.opencontainers.image.licenses="MIT"

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install PDM
RUN pip install --no-cache-dir pdm

# Set the working directory
WORKDIR /build

# Copy only dependency files first to leverage cache
COPY pyproject.toml pdm.lock README.md ./

# Install dependencies
RUN pdm install --prod --no-lock --no-editable

# Copy source code
COPY ./src ./src

# Build the package
RUN pdm build

# Final stage
FROM python:3.13-slim

# Add labels
LABEL org.opencontainers.image.source="https://github.com/jelther/yt_thumbsense"
LABEL org.opencontainers.image.description="An AI-powered YouTube API that predicts likes/dislikes ratios through comment sentiment analysis."
LABEL org.opencontainers.image.licenses="MIT"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash appuser

WORKDIR /app

# Copy the built package from builder
COPY --from=builder /build/dist/*.whl .

# Install the package and its dependencies
RUN pip install --no-cache-dir *.whl && \
    rm -f *.whl

# Switch to non-root user
USER appuser

# Make port 8080 available
EXPOSE 8080

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "yt_thumbsense.main:app", "--host", "0.0.0.0", "--port", "8080"]
