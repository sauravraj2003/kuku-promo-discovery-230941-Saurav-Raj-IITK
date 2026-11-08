FROM python:3.12-slim

WORKDIR /app

# Copy dependency configuration
COPY pyproject.toml .

# Copy backend, frontend build, screenplay sources, and docs
COPY backend ./backend
COPY frontend ./frontend
COPY docs ./docs
COPY data ./data
COPY "I Married a Broken Soldier. He was a Duke" "./I Married a Broken Soldier. He was a Duke"

# Install application dependencies
RUN pip install --no-cache-dir .

# Expose default web port
EXPOSE 7860

# Auto-seed on container boot if fresh, and support both HF Spaces (7860) and Render/Railway ($PORT)
ENV KUKU_AUTO_SEED=1
ENV PORT=7860
CMD ["sh", "-c", "uvicorn kuku.api:app --host 0.0.0.0 --port ${PORT:-7860}"]
