FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    EMAIL_MCP_PORT=8201

WORKDIR /app

COPY integrations/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY integrations ./integrations

EXPOSE 8201

CMD ["python", "-m", "integrations.mcp_servers.email_mcp.server"]
