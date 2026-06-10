FROM python:3.12-slim

WORKDIR /app

# Install system compilation headers natively in the container
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev

# Create a secure, non-privileged system user/group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10000 -g appgroup -m -s /bin/false appuser

COPY requirements.txt .

# Let pip cleanly resolve the entire dependency tree natively inside the container
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and adjust ownership permissions
COPY --chown=appuser:appgroup app/ ./app/

# Switch the execution context to the secure non-root worker user
USER appuser

# Expose FastAPI's standard network socket port
EXPOSE 8000