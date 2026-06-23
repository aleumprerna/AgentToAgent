FROM python:3.12-slim
 
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AGENT_PORT=8001 \
    CSV_PATH=data/incident.csv \
    AGENT_BASE_URL=http://localhost:8001
 
WORKDIR /app
 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
COPY app ./app
COPY data ./data
RUN mkdir -p exports
 
EXPOSE 8001
 
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=3).read()"
 
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${AGENT_PORT:-8001}"]
