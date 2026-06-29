# Enterprise AI Integration POC

This folder adds a lightweight integration layer for the Enterprise AI master app.
The remote A2A agents and MCP server are intentionally independent services. The
master app calls them through HTTP or MCP endpoint URLs.

## Architecture

- `a2a_agents/hr_agent`: HR policy and employee data questions.
- `a2a_agents/it_agent`: IT design, QA, effort, architecture, and risk guidance.
- `a2a_agents/servicenow_agent`: ServiceNow incident/problem consulting using the existing CSV logic from `app/csv_tools.py`.
- `a2a_agents/hotel_agent`: Mock hotel availability and booking.
- `mcp_servers/email_mcp`: FastMCP mock email tool.
- `master_integration`: Master-side config, A2A client, MCP client, and keyword router.

The master test endpoint is:

```text
POST /integrations/test
```

It routes to an integration when a keyword matches. If nothing matches, it returns
a no-route response so existing master behavior can continue.

## A2A Contract

Every A2A agent exposes:

- `GET /health`
- `GET /.well-known/agent-card.json`
- `POST /a2a/chat`

The chat request shape is:

```json
{
  "task_id": "string",
  "message": "user question"
}
```

The chat response shape is:

```json
{
  "task_id": "same task_id from the request",
  "agent": "agent_name",
  "status": "completed",
  "content": "human-readable answer",
  "data": {}
}
```

## MCP Contract

The Email MCP server runs with FastMCP streamable HTTP and exposes:

- `send_mock_email(to, subject, body, cc="")`
- `health()`

No real email is sent. The tool returns the email payload and `mock_email_sent: true`.

## Ports

| Service | Port |
| --- | --- |
| HR Agent | `8101` |
| IT Agent | `8102` |
| ServiceNow Consultant Agent | `8103` |
| Hotel Booking Agent | `8104` |
| Email MCP Server | `8201` |

Email MCP streamable HTTP path:

```text
http://localhost:8201/mcp
```

Use `/mcp`. The Email MCP server does not expose `/api/mcp`.

## Environment Variables

The master router reads:

```text
HR_AGENT_URL=http://localhost:8101
IT_AGENT_URL=http://localhost:8102
SERVICENOW_AGENT_URL=http://localhost:8103
HOTEL_AGENT_URL=http://localhost:8104
EMAIL_MCP_URL=http://localhost:8201/mcp
INTEGRATION_TIMEOUT_SECONDS=10
```

The ServiceNow agent also supports:

```text
CSV_PATH=data/incident.csv
SERVICENOW_INCIDENT_CSV_PATH=data/incident.csv
SERVICENOW_PROBLEM_CSV_PATH=data/problem.csv
```

## Run Manually

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start each service in a separate terminal:

```powershell
uvicorn integrations.a2a_agents.hr_agent.main:app --host 0.0.0.0 --port 8101
uvicorn integrations.a2a_agents.it_agent.main:app --host 0.0.0.0 --port 8102
uvicorn integrations.a2a_agents.servicenow_agent.main:app --host 0.0.0.0 --port 8103
uvicorn integrations.a2a_agents.hotel_agent.main:app --host 0.0.0.0 --port 8104
python -m integrations.mcp_servers.email_mcp.server
```

Start the master app:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## Run With Docker Compose

```powershell
docker compose -f docker-compose.integrations.yml up --build
```

This starts only the remote integration services. Run the master application
separately with the normal project command or existing `docker-compose.yml`.

If you see `Invalid Host header` from the Email MCP container, rebuild with the
latest Docker compose file and call the server through `localhost` from the same
machine:

```powershell
docker compose -f docker-compose.integrations.yml up --build email-mcp
```

## Example Curl Commands

Health:

```powershell
curl http://localhost:8101/health
curl http://localhost:8102/health
curl http://localhost:8103/health
curl http://localhost:8104/health
```

ServiceNow A2A:

```powershell
curl -X POST http://localhost:8103/a2a/chat `
  -H "Content-Type: application/json" `
  -d "{\"task_id\":\"test-1\",\"message\":\"Tell me about incident INC0028802\"}"
```

Hotel A2A:

```powershell
curl -X POST http://localhost:8104/a2a/chat `
  -H "Content-Type: application/json" `
  -d "{\"task_id\":\"test-2\",\"message\":\"Book room 22 for Shantanu\"}"
```

Master integration router:

```powershell
curl -X POST http://localhost:8001/integrations/test `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"Send email to test@example.com saying meeting confirmed\"}"
```

## Test Messages

- `What information do you collect from employees?` -> HR Agent
- `Create QA test cases for login module` -> IT Agent
- `Tell me about incident INC10399538` -> ServiceNow Consultant Agent
- `My VPN is not working` -> ServiceNow Consultant Agent
- `Is deluxe room available?` -> Hotel Booking Agent
- `Book room 22 for Shantanu` -> Hotel Booking Agent
- `Send email to test@example.com saying meeting is confirmed` -> Email MCP Server

Router logs look like:

```text
[ROUTER] selected_agent=servicenow_agent reason=matched keyword incident
```
