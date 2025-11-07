# Production-ready Dockerfile (Alpine, with PUID/PGID support via entrypoint)

FROM python:3.11-alpine

# Install build/runtime dependencies + su-exec for user switching
RUN apk add --no-cache gcc musl-dev libffi-dev su-exec

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    apk del gcc musl-dev

# Copy core bot code, version, and only plugins README (no .py plugins)
COPY bot/ ./bot/
COPY VERSION /app/VERSION
COPY plugins/README.md plugins/
# COPY plugins/.keep plugins/  # uncomment if you use it

# Copy entrypoint with PUID/PGID support
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create runtime dirs (ownership fixed by entrypoint), no user here
RUN mkdir -p sessions data plugins logs

ENV PYTHONUNBUFFERED=1

# Use entrypoint to handle PUID/PGID and chown at container start
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "bot"]