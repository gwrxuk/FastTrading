# Rust Matching Engine Dockerfile
# Multi-stage build for optimized production image

# Build stage
FROM rust:1.74-slim-bookworm as builder

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Copy workspace files
COPY Cargo.toml Cargo.lock ./
COPY common/Cargo.toml ./common/
COPY matching-engine/Cargo.toml ./matching-engine/
COPY data-pipeline/Cargo.toml ./data-pipeline/
COPY exchange-gateway/Cargo.toml ./exchange-gateway/

# Create dummy source files for dependency caching
RUN mkdir -p common/src matching-engine/src data-pipeline/src exchange-gateway/src && \
    echo "pub fn main() {}" > common/src/lib.rs && \
    echo "fn main() {}" > matching-engine/src/main.rs && \
    echo "fn main() {}" > data-pipeline/src/main.rs && \
    echo "fn main() {}" > exchange-gateway/src/main.rs

# Build dependencies only
RUN cargo build --release -p matching-engine && \
    rm -rf common/src matching-engine/src data-pipeline/src exchange-gateway/src

# Copy actual source
COPY common/ ./common/
COPY matching-engine/ ./matching-engine/

# Build the actual binary
RUN cargo build --release -p matching-engine

# Runtime stage
FROM debian:bookworm-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy binary
COPY --from=builder /app/target/release/matching-engine /app/matching-engine

# Set ownership
RUN chown -R appuser:appuser /app

USER appuser

# Expose ports
EXPOSE 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run
CMD ["/app/matching-engine"]

