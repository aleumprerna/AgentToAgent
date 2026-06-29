FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY integrations/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY integrations ./integrations

EXPOSE 8104

CMD ["uvicorn", "integrations.a2a_agents.hotel_agent.main:app", "--host", "0.0.0.0", "--port", "8104"]
