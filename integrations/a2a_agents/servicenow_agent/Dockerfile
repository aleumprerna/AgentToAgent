FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CSV_PATH=data/incident.csv

WORKDIR /app

COPY integrations/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data
COPY integrations ./integrations

EXPOSE 8103

CMD ["uvicorn", "integrations.a2a_agents.servicenow_agent.main:app", "--host", "0.0.0.0", "--port", "8103"]
