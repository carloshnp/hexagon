FROM python:3.12-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY research/ research/
COPY .env.example .env

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# Run
CMD ["uvicorn", "research.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
