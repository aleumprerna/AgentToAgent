# Testing Guide

Use this file to test the existing A2A endpoint and the new local tools endpoint.

## 1. Start The Server

From the project root:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

API base URL:

```text
http://localhost:8001
```

## 2. Health Check

```bash
curl http://localhost:8001/health
```

Expected:

```json
{
  "status": "ok",
  "agent": "servicenow_incident_agent"
}
```

## 3. Agent Card

```bash
curl http://localhost:8001/.well-known/agent-card.json
```

## 4. Old A2A Incident Lookup

The A2A endpoint accepts natural-language messages and routes supported tool-style requests.
Incident lookup still works:

```bash
curl -X POST http://localhost:8001/a2a/tasks \
  -H "Content-Type: application/json" \
  -d "{\"task_id\":\"test-1\",\"message\":\"Tell me about INC99004\"}"
```

Windows PowerShell one-line version:

```powershell
curl -X POST http://localhost:8001/a2a/tasks -H "Content-Type: application/json" -d "{\"task_id\":\"test-1\",\"message\":\"Tell me about INC99004\"}"
```

Hotel availability through A2A:

```powershell
curl -X POST http://localhost:8001/a2a/tasks -H "Content-Type: application/json" -d "{\"task_id\":\"hotel-1\",\"message\":\"Check deluxe room availability from 2026-06-25 to 2026-06-26\"}"
```

Hotel booking through A2A:

```powershell
curl -X POST http://localhost:8001/a2a/tasks -H "Content-Type: application/json" -d "{\"task_id\":\"hotel-2\",\"message\":\"Book room 22 for Shantanu from 2026-06-25 to 2026-06-26\"}"
```

Weather through A2A:

```powershell
curl -X POST http://localhost:8001/a2a/tasks -H "Content-Type: application/json" -d "{\"task_id\":\"weather-1\",\"message\":\"What is the weather in Jaipur?\"}"
```

Movies through A2A:

```powershell
curl -X POST http://localhost:8001/a2a/tasks -H "Content-Type: application/json" -d "{\"task_id\":\"movie-1\",\"message\":\"Show top 10 Action movies\"}"
```

## 5. New Tool Endpoint

All new tools are tested using:

```text
POST /tools/run
```

Request format:

```json
{
  "tool_name": "search_incident",
  "arguments": {
    "incident_number": "INC99004"
  }
}
```

## 6. Incident Tools

### Search Incident

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"search_incident\",\"arguments\":{\"incident_number\":\"INC99004\"}}"
```

### Create Incident

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"create_incident\",\"arguments\":{\"short_description\":\"Laptop not working\",\"priority\":\"High\",\"caller\":\"Shantanu\",\"category\":\"Hardware\"}}"
```

### Update Incident

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"update_incident\",\"arguments\":{\"incident_number\":\"INC99004\",\"field\":\"priority\",\"value\":\"High\"}}"
```

### List Incidents

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"list_incidents\",\"arguments\":{\"status\":\"New\"}}"
```

## 7. Knowledge Base Tools

### Search KB

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"search_knowledge_base\",\"arguments\":{\"query\":\"VPN issue\"}}"
```

### Suggest Resolution

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"suggest_resolution\",\"arguments\":{\"incident_description\":\"laptop is slow\"}}"
```

## 8. Hotel Booking Tools

### Check Room Availability

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"check_room_availability\",\"arguments\":{\"check_in\":\"2026-06-25\",\"check_out\":\"2026-06-26\",\"room_type\":\"deluxe\"}}"
```

### Book Room

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"book_room\",\"arguments\":{\"room_no\":\"22\",\"guest_name\":\"Shantanu\",\"check_in\":\"2026-06-25\",\"check_out\":\"2026-06-26\"}}"
```

### Cancel Booking

Replace `BK-XXXXXXXX` with the booking ID returned by `book_room`.

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"cancel_booking\",\"arguments\":{\"booking_id\":\"BK-XXXXXXXX\"}}"
```

### List Available Rooms

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"list_available_rooms\",\"arguments\":{\"date\":\"2026-06-25\"}}"
```

## 9. Movie Tools

### Search Movie

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"search_movie\",\"arguments\":{\"title\":\"Matrix\"}}"
```

### Top Movies By Genre

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"top_movies_by_genre\",\"arguments\":{\"genre\":\"Action\",\"limit\":10}}"
```

### Generate Movie CSV

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"generate_movie_csv\",\"arguments\":{\"genre\":\"Action\",\"limit\":10}}"
```

Generated files are saved under:

```text
exports/
```

## 10. Weather Tool

This uses the free Open-Meteo API and needs internet access.

```bash
curl -X POST http://localhost:8001/tools/run \
  -H "Content-Type: application/json" \
  -d "{\"tool_name\":\"get_weather\",\"arguments\":{\"city\":\"Jaipur\"}}"
```

If internet/API is not available, the response will contain a clear error message.

## 11. Quick PowerShell One-Line Examples

Incident:

```powershell
curl -X POST http://localhost:8001/tools/run -H "Content-Type: application/json" -d "{\"tool_name\":\"search_incident\",\"arguments\":{\"incident_number\":\"INC99004\"}}"
```

KB:

```powershell
curl -X POST http://localhost:8001/tools/run -H "Content-Type: application/json" -d "{\"tool_name\":\"search_knowledge_base\",\"arguments\":{\"query\":\"VPN issue\"}}"
```

Hotel:

```powershell
curl -X POST http://localhost:8001/tools/run -H "Content-Type: application/json" -d "{\"tool_name\":\"check_room_availability\",\"arguments\":{\"check_in\":\"2026-06-25\",\"check_out\":\"2026-06-26\",\"room_type\":\"deluxe\"}}"
```

Movies:

```powershell
curl -X POST http://localhost:8001/tools/run -H "Content-Type: application/json" -d "{\"tool_name\":\"top_movies_by_genre\",\"arguments\":{\"genre\":\"Action\",\"limit\":10}}"
```

Weather:

```powershell
curl -X POST http://localhost:8001/tools/run -H "Content-Type: application/json" -d "{\"tool_name\":\"get_weather\",\"arguments\":{\"city\":\"Jaipur\"}}"
```
