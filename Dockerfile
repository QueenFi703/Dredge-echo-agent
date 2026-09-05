FROM python:3.12-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy build-dependency lockfile and project metadata first (better layer caching)
COPY requirements-build.txt ./
COPY pyproject.toml ./
COPY README.md ./
COPY language/ ./language/
COPY compiler/ ./compiler/
COPY bridge/ ./bridge/
COPY examples/ ./examples/

# Install the package
RUN pip install --no-cache-dir --require-hashes -r requirements-build.txt && \
    pip install --no-cache-dir -e .

# Default: run a health check
CMD ["python", "-c", "import language; print('Aster language runtime ready')"]
