# A2A ServiceNow Incident Agent

Runnable FastAPI + LangGraph POC that exposes A2A-style incident lookup plus local tools for incidents, KB search, hotel booking, movie CSV reports, and weather lookup.

## Project structure

```text
a2a-servicenow-incident-agent/
|
├── app/
│   ├── main.py
│   ├── graph.py
│   ├── csv_tools.py
│   ├── schemas.py
│   └── config.py
|
├── data/
│   └── incident.csv
|
├── .env.example
├── requirements.txt
└── README.md
```

## Setup

```bash
cd a2a-servicenow-incident-agent
python -m venv .venv
```

Activate the virtual environment.

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
CSV_PATH=data/incident.csv
AGENT_NAME=servicenow_incident_agent
AGENT_PORT=8001
```

If `OPENAI_API_KEY` is not set, the app still returns a simple fallback response for found incidents. Set the key to use OpenAI for final response formatting.

## Add incident.csv

The incident agent reads:

```text
data/incident.csv
```

The CSV includes:

```text
number,short_description,priority,state,caller,category,assigned_to,opened_at
```

The other local tools use:

```text
data/kb.csv
data/rooms.csv
data/movies.csv
```

## Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

The API will be available at:

```text
http://localhost:8001
```

When running on another computer, the master agent should call this agent using:

```text
http://<SERVICENOW_COMPUTER_IP>:8001
```

## Test with curl

Health:

```bash
curl http://localhost:8001/health
```

Agent card:

```bash
curl http://localhost:8001/.well-known/agent-card.json
```

Task lookup:

```bash
curl -X POST http://localhost:8001/a2a/tasks \
  -H "Content-Type: application/json" \
  -d "{\"task_id\":\"test-1\",\"message\":\"Give me details on INC99004\"}"
```

Not found:

```bash
curl -X POST http://localhost:8001/a2a/tasks \
  -H "Content-Type: application/json" \
  -d "{\"task_id\":\"test-2\",\"message\":\"Give me details on INC12345\"}"
```

No incident number:

```bash
curl -X POST http://localhost:8001/a2a/tasks \
  -H "Content-Type: application/json" \
  -d "{\"task_id\":\"test-3\",\"message\":\"Give me incident details\"}"
```

## Tool endpoint examples

Run any registered tool with:

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"search_incident\",\"arguments\":{\"incident_number\":\"INC99004\"}}"
```

Create incident:

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"create_incident\",\"arguments\":{\"short_description\":\"Laptop not working\",\"priority\":\"High\",\"caller\":\"Shantanu\",\"category\":\"Hardware\"}}"
```

Update incident:

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"update_incident\",\"arguments\":{\"incident_number\":\"INC99004\",\"field\":\"priority\",\"value\":\"High\"}}"
```

Search KB:

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"search_knowledge_base\",\"arguments\":{\"query\":\"VPN issue\"}}"
```

Check room availability:

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"check_room_availability\",\"arguments\":{\"check_in\":\"2026-06-25\",\"check_out\":\"2026-06-26\",\"room_type\":\"deluxe\"}}"
```

Book room:

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"book_room\",\"arguments\":{\"room_no\":\"22\",\"guest_name\":\"Shantanu\",\"check_in\":\"2026-06-25\",\"check_out\":\"2026-06-26\"}}"
```

Top movies by genre:

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"top_movies_by_genre\",\"arguments\":{\"genre\":\"Action\",\"limit\":10}}"
```

Generate movie CSV:

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"generate_movie_csv\",\"arguments\":{\"genre\":\"Action\",\"limit\":10}}"
```

Get weather:

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"get_weather\",\"arguments\":{\"city\":\"Jaipur\"}}"
```

## Endpoints

### GET /health

```json
{
  "status": "ok",
  "agent": "servicenow_incident_agent"
}
```

### GET /.well-known/agent-card.json

```json
{
  "name": "servicenow_incident_agent",
  "description": "Runs local CSV/API tools for incident management, knowledge base search, hotel booking, movie data analysis, weather lookup, and CSV report generation.",
  "capabilities": [
    "incident_lookup",
    "csv_record_search",
    "incident_management",
    "knowledge_base_search",
    "hotel_booking",
    "movie_data_analysis",
    "weather_lookup",
    "csv_report_generation"
  ],
  "endpoint": "/a2a/tasks",
  "input_examples": [
    "Tell me about INC99004",
    "Create an incident for laptop not working",
    "Update INC99004 priority to High",
    "Find KB article for VPN issue",
    "Suggest resolution for laptop is slow",
    "Is deluxe room available on 2026-06-25?",
    "Book room 22 for Shantanu on 2026-06-25",
    "Create CSV of top 10 action movies",
    "What is the weather in Jaipur?"
  ]
}
```

### POST /a2a/tasks

Request:

```json
{
  "task_id": "optional-task-id",
  "message": "Give me details on INC99004"
}
```

Found response:

```json
{
  "task_id": "optional-task-id",
  "agent": "servicenow_incident_agent",
  "status": "completed",
  "content": "Incident INC99004 found. Here are the details: ...",
  "data": {
    "number": "INC99004"
  }
}
```

Not found response:

```json
{
  "task_id": "optional-task-id",
  "agent": "servicenow_incident_agent",
  "status": "not_found",
  "content": "No incident found for INC99004.",
  "data": null
}
```

No incident number response:

```json
{
  "task_id": "optional-task-id",
  "agent": "servicenow_incident_agent",
  "status": "failed",
  "content": "No incident number found in the request. Please provide an incident number like INC99004.",
  "data": null
}
```
