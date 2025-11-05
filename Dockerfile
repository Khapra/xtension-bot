# Production-ready Dockerfile (alpine-based)
FROM python:3.11-alpine

RUN apk add --no-cache gcc musl-dev libffi-dev

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    apk del gcc musl-dev

# Copy code & version
COPY bot/ ./bot/
COPY plugins/ ./plugins/
COPY VERSION /app/VERSION

# Create runtime dirs and non-root user
RUN mkdir -p sessions data plugins && \
    adduser -D -u 1000 botuser && \
    chown -R botuser:botuser /app

USER botuser

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "bot"]