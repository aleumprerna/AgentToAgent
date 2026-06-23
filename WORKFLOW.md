# ServiceNow Incident Agent Workflow

This file explains the complete step-by-step workflow for running and testing the `a2a-servicenow-incident-agent` POC.

## 1. What This Agent Does

This is a small external agent that behaves like a ServiceNow Incident Agent.

It exposes HTTP endpoints so another master agent can:

1. Check if this agent is running.
2. Discover what this agent can do.
3. Send a task message like `Give me details on INC99004`.
4. Receive incident details from `data/incident.csv`.

The incident lookup is done using the CSV column:

```text
number
```

Example:

```text
INC99004
```

## 2. Project Structure

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
├── README.md
└── WORKFLOW.md
```

## 3. Step 1: Open The Project Folder

Go to the project folder:

```bash
cd a2a-servicenow-incident-agent
```

## 4. Step 2: Create Python Virtual Environment

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

## 5. Step 3: Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

The main packages are:

```text
fastapi
uvicorn
langgraph
langchain-openai
pandas
python-dotenv
pydantic
```

## 6. Step 4: Create `.env`

Copy `.env.example` to `.env`.

Windows PowerShell:

```bash
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Your `.env` should look like this:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
CSV_PATH=data/incident.csv
AGENT_NAME=servicenow_incident_agent
AGENT_PORT=8001
```

For a quick local POC, the agent can still return incident data without `OPENAI_API_KEY`. OpenAI is only used to make the final response text cleaner.

## 7. Step 5: Add Or Update `incident.csv`

The CSV file should be located here:

```text
data/incident.csv
```

The CSV must contain a column named:

```text
number
```

Example CSV:

```csv
number,short_description,state,priority,assignment_group,assigned_to,caller,opened_at
INC99004,Email service is unavailable,In Progress,2 - High,Service Desk,Asha Rao,Pat Lee,2026-06-15 09:20:00
INC90455,Laptop VPN client fails to connect,New,3 - Moderate,Network Support,Dev Kumar,Jamie Chen,2026-06-15 11:05:00
```

When the user asks for `INC99004`, the agent searches:

```text
number == INC99004
```

The search is case-insensitive.

## 8. Step 6: Start The Agent Server

Run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

The agent will start at:

```text
http://localhost:8001
```

If the agent is running on another computer, use that computer's IP address:

```text
http://<SERVICENOW_COMPUTER_IP>:8001
```

Example:

```text
http://192.168.1.25:8001
```

## 9. Step 7: Test Health Endpoint

Use this command:

```bash
curl http://localhost:8001/health
```

Expected response:

```json
{
  "status": "ok",
  "agent": "servicenow_incident_agent"
}
```

This confirms the agent server is running.

## 10. Step 8: Test Agent Discovery

Use this command:

```bash
curl http://localhost:8001/.well-known/agent-card.json
```

Expected response:

```json
{
  "name": "servicenow_incident_agent",
  "description": "Finds ServiceNow incident details from incident.csv using the incident number column.",
  "capabilities": ["incident_lookup", "csv_record_search"],
  "endpoint": "/a2a/tasks",
  "input_examples": [
    "Give me details on INC99004",
    "Tell me about incident INC90455"
  ]
}
```

This tells the master agent what this external agent can do.

## 11. Step 9: Test Incident Lookup

Use this command:

```bash
curl -X POST http://localhost:8001/a2a/tasks \
  -H "Content-Type: application/json" \
  -d "{\"task_id\":\"test-1\",\"message\":\"Give me details on INC99004\"}"
```

Expected response:

```json
{
  "task_id": "test-1",
  "agent": "servicenow_incident_agent",
  "status": "completed",
  "content": "Incident INC99004 found. Here are the details: ...",
  "data": {
    "number": "INC99004",
    "short_description": "Email service is unavailable",
    "state": "In Progress",
    "priority": "2 - High"
  }
}
```

The exact `data` fields depend on your CSV columns.

## 12. Step 10: Test Not Found Case

Use an incident number that does not exist in the CSV:

```bash
curl -X POST http://localhost:8001/a2a/tasks \
  -H "Content-Type: application/json" \
  -d "{\"task_id\":\"test-2\",\"message\":\"Give me details on INC12345\"}"
```

Expected response:

```json
{
  "task_id": "test-2",
  "agent": "servicenow_incident_agent",
  "status": "not_found",
  "content": "No incident found for INC12345.",
  "data": null
}
```

## 13. Step 11: Test Missing Incident Number

Use a message without an incident number:

```bash
curl -X POST http://localhost:8001/a2a/tasks \
  -H "Content-Type: application/json" \
  -d "{\"task_id\":\"test-3\",\"message\":\"Give me incident details\"}"
```

Expected response:

```json
{
  "task_id": "test-3",
  "agent": "servicenow_incident_agent",
  "status": "failed",
  "content": "No incident number found in the request. Please provide an incident number like INC99004.",
  "data": null
}
```

## 14. Internal Workflow

When `/a2a/tasks` receives a message, the flow is:

```text
User or master agent sends message
        |
        v
POST /a2a/tasks
        |
        v
LangGraph starts
        |
        v
extract_incident_number
        |
        v
lookup_incident_csv
        |
        v
compose_response
        |
        v
Return JSON response
```

## 15. LangGraph Node Details

### Node 1: `extract_incident_number`

This node uses regex:

```text
INC\d+
```

It extracts values like:

```text
INC99004
INC90455
INC12345
```

### Node 2: `lookup_incident_csv`

This node:

1. Loads `data/incident.csv` using pandas.
2. Checks the `number` column.
3. Performs case-insensitive exact match.
4. Returns the matched row as a dictionary.

### Node 3: `compose_response`

This node:

1. Returns a failed response if no incident number was found.
2. Returns a not found response if the CSV has no matching row.
3. Uses OpenAI to format a short readable response if the row was found.
4. Uses a fallback response if `OPENAI_API_KEY` is empty.

## 16. Console Logs

When a request comes in, the app prints simple logs:

```text
Incoming message: Give me details on INC99004
Extracted incident number: INC99004
CSV row found: True
```

These logs are useful during the demo to show the external agent is receiving and processing requests.

## 17. Master Agent Integration

If this agent runs on a separate ServiceNow computer, the master agent should call:

```text
http://<SERVICENOW_COMPUTER_IP>:8001
```

The master agent can discover capabilities using:

```text
GET http://<SERVICENOW_COMPUTER_IP>:8001/.well-known/agent-card.json
```

Then send tasks using:

```text
POST http://<SERVICENOW_COMPUTER_IP>:8001/a2a/tasks
```

Example request body:

```json
{
  "task_id": "master-task-1",
  "message": "Give me details on INC99004"
}
```

## 18. Common Problems

### Port already in use

If port `8001` is already used, run on another port:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

Then call:

```text
http://localhost:8002
```

### CSV file not found

Check this value in `.env`:

```env
CSV_PATH=data/incident.csv
```

Also confirm the file exists:

```text
data/incident.csv
```

### CSV missing `number` column

The CSV must have:

```text
number
```

Column names are important.

### OpenAI key missing

If `OPENAI_API_KEY` is empty, the app still works and returns a fallback response.

To enable OpenAI formatting, update `.env`:

```env
OPENAI_API_KEY=your_real_key_here
```

Then restart the server.

## 19. Demo Script

Use this flow in a demo:

1. Start the external ServiceNow incident agent.
2. Call `/health`.
3. Call `/.well-known/agent-card.json`.
4. Send task: `Give me details on INC99004`.
5. Show that the agent extracted `INC99004`.
6. Show that it searched `incident.csv`.
7. Show the completed response with incident row data.
8. Explain that a master agent can call the same endpoint from another computer.

## 20. Quick Command Summary

```bash
cd a2a-servicenow-incident-agent
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Test:

```bash
curl http://localhost:8001/health
curl http://localhost:8001/.well-known/agent-card.json
curl -X POST http://localhost:8001/a2a/tasks -H "Content-Type: application/json" -d "{\"task_id\":\"test-1\",\"message\":\"Give me details on INC99004\"}"
```
