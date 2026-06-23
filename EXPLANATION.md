# Project Explanation

## 1. Ye Project Kya Hai?

Ye project ek **Python FastAPI + LangGraph A2A POC agent** hai.

Simple words me:

> Ye ek local agent service hai jo HTTP API ke through request leti hai, CSV files ya free API se data nikalti hai, aur JSON response return karti hai.

Pehle project sirf ek simple ServiceNow-style incident lookup demo tha.

Pehle flow:

```text
User message -> Incident number extract -> incident.csv me search -> response
```

Example:

```text
Tell me about INC99004
```

Agent `INC99004` extract karta tha aur `data/incident.csv` me us incident ko search karta tha.

Ab project ko upgrade karke **real-world tools-based POC** banaya gaya hai.

Ab ye sirf incident lookup nahi karta, balki multiple actual tools run kar sakta hai.

## 2. Ab Project Kya Kar Raha Hai?

Ab project me do main capabilities hain:

1. Existing A2A incident lookup
2. New tools-based execution endpoint

## 3. Main Endpoints

### Endpoint 1: Old A2A Endpoint

```text
POST /a2a/tasks
```

Ye existing endpoint hai.

Iska kaam:

1. User ka message receive karna
2. Message me incident number find karna
3. `data/incident.csv` me incident search karna
4. Incident details return karna

Example request:

```json
{
  "task_id": "test-1",
  "message": "Tell me about INC99004"
}
```

Example response:

```json
{
  "task_id": "test-1",
  "agent": "servicenow_incident_agent",
  "status": "completed",
  "content": "Incident INC99004 found. Here are the details...",
  "data": {
    "number": "INC99004"
  }
}
```

### Endpoint 2: New Tools Endpoint

```text
POST /tools/run
```

Ye new endpoint hai.

Iska kaam:

1. Request me `tool_name` receive karna
2. Request me `arguments` receive karna
3. `app/tool_registry.py` se correct tool find karna
4. Tool function ko run karna
5. Result JSON me return karna

Example request:

```json
{
  "tool_name": "search_incident",
  "arguments": {
    "incident_number": "INC99004"
  }
}
```

Example response:

```json
{
  "tool_name": "search_incident",
  "status": "completed",
  "result": {
    "success": true,
    "incident": {
      "number": "INC99004",
      "short_description": "Email service is unavailable"
    }
  }
}
```

## 4. Request Flow Kaise Kaam Karta Hai?

### A2A Flow

```text
Client/Postman/curl
        |
        v
FastAPI /a2a/tasks
        |
        v
LangGraph incident_graph
        |
        v
Extract incident number from message
        |
        v
Search data/incident.csv
        |
        v
Return incident response
```

### Tool Flow

```text
Client/Postman/curl
        |
        v
FastAPI /tools/run
        |
        v
tool_registry.py
        |
        v
Find tool by tool_name
        |
        v
Run tool function with arguments
        |
        v
Read/write CSV or call free API
        |
        v
Return JSON response
```

## 5. Important Files

### app/main.py

Ye FastAPI application ka main file hai.

Isme endpoints defined hain:

```text
GET /health
GET /.well-known/agent-card.json
POST /a2a/tasks
POST /tools/run
```

`/tools/run` isi file me add kiya gaya hai.

### app/graph.py

Ye LangGraph flow handle karta hai.

Iska kaam:

1. User message se incident number extract karna
2. CSV me incident lookup karna
3. Response compose karna

Example:

```text
Tell me about INC99004
```

Graph `INC99004` nikalta hai aur CSV me search karta hai.

### app/csv_tools.py

Ye existing incident lookup helper hai.

Iska kaam:

```text
incident.csv me number column ke basis par incident find karna
```

### app/schemas.py

Ye request/response models define karta hai.

Examples:

```text
TaskRequest
TaskResponse
ToolRunRequest
ToolRunResponse
```

FastAPI in models ka use request validate karne aur response format maintain karne ke liye karta hai.

### app/tool_registry.py

Ye new tools ka central router hai.

Isme dictionary hai:

```python
AVAILABLE_TOOLS = {
    "search_incident": search_incident,
    "create_incident": create_incident,
    "search_knowledge_base": search_knowledge_base,
    "book_room": book_room,
    "get_weather": get_weather,
}
```

Jab `/tools/run` call hota hai, tool registry `tool_name` ke basis par correct function run karti hai.

Example:

```json
{
  "tool_name": "search_incident"
}
```

To registry `search_incident()` function call karegi.

## 6. Tools Kya-Kya Karte Hain?

## Incident Tools

File:

```text
app/tools/incident_tools.py
```

CSV:

```text
data/incident.csv
```

Available tools:

```text
search_incident
create_incident
update_incident
list_incidents
```

### search_incident

Incident number ke basis par incident search karta hai.

Example:

```json
{
  "tool_name": "search_incident",
  "arguments": {
    "incident_number": "INC99004"
  }
}
```

### create_incident

Naya incident create karta hai.

Ye automatically new incident number generate karta hai, jaise:

```text
INC10001
INC10002
```

Created incident CSV me save ho jata hai.

### update_incident

Existing incident ka allowed field update karta hai.

Allowed fields:

```text
short_description
priority
state
status
caller
category
assigned_to
```

### list_incidents

Incidents list karta hai.

Optional filters:

```text
status
priority
```

## Knowledge Base Tools

File:

```text
app/tools/kb_tools.py
```

CSV:

```text
data/kb.csv
```

Available tools:

```text
search_knowledge_base
suggest_resolution
```

### search_knowledge_base

Query ke basis par KB articles search karta hai.

Ye fields me search karta hai:

```text
title
category
keywords
content
```

Example:

```json
{
  "tool_name": "search_knowledge_base",
  "arguments": {
    "query": "VPN issue"
  }
}
```

### suggest_resolution

Incident description ke basis par best matching KB article find karta hai.

Example:

```json
{
  "tool_name": "suggest_resolution",
  "arguments": {
    "incident_description": "laptop is slow"
  }
}
```

## Hotel Booking Tools

File:

```text
app/tools/hotel_tools.py
```

CSV:

```text
data/rooms.csv
```

Available tools:

```text
check_room_availability
book_room
cancel_booking
list_available_rooms
```

### check_room_availability

Check-in, check-out aur optional room type ke basis par available rooms find karta hai.

Example:

```json
{
  "tool_name": "check_room_availability",
  "arguments": {
    "check_in": "2026-06-25",
    "check_out": "2026-06-26",
    "room_type": "deluxe"
  }
}
```

### book_room

Room book karta hai.

Booking ke time:

1. Room status `booked` ho jata hai
2. Guest name save hota hai
3. Booking ID generate hoti hai
4. CSV update hoti hai

Example:

```json
{
  "tool_name": "book_room",
  "arguments": {
    "room_no": "22",
    "guest_name": "Shantanu",
    "check_in": "2026-06-25",
    "check_out": "2026-06-26"
  }
}
```

### cancel_booking

Booking ID ke basis par booking cancel karta hai.

Cancel hone par:

1. Room status `available` ho jata hai
2. Guest name clear ho jata hai
3. Booking ID clear ho jati hai

### list_available_rooms

Given date ke liye available rooms list karta hai.

## Movie Tools

File:

```text
app/tools/movie_tools.py
```

CSV:

```text
data/movies.csv
```

Available tools:

```text
search_movie
top_movies_by_genre
generate_movie_csv
```

### search_movie

Movie title ke basis par movies search karta hai.

### top_movies_by_genre

Genre ke basis par top movies list karta hai.

Sorting:

```text
rating descending
votes descending
```

### generate_movie_csv

Top movies ka CSV report generate karta hai.

Generated file save hoti hai:

```text
exports/
```

Example:

```text
exports/top_10_action_movies.csv
```

## Weather Tool

File:

```text
app/tools/weather_tools.py
```

Available tool:

```text
get_weather
```

Ye free Open-Meteo API use karta hai.

Steps:

1. City name se latitude/longitude find karta hai
2. Latitude/longitude se current weather fetch karta hai
3. Weather response return karta hai

Example:

```json
{
  "tool_name": "get_weather",
  "arguments": {
    "city": "Jaipur"
  }
}
```

Note:

```text
Weather tool ke liye internet chahiye.
Internet/API fail hua to clear error response milega.
```

## 7. Data Files

### data/incident.csv

Incident records store karta hai.

Columns:

```text
number,short_description,priority,state,caller,category,assigned_to,opened_at
```

### data/kb.csv

Knowledge base articles store karta hai.

Columns:

```text
id,title,category,keywords,content
```

### data/rooms.csv

Hotel room inventory and booking data store karta hai.

Columns:

```text
room_no,type,price_per_night,status,available_from,available_to,guest_name,booking_id
```

### data/movies.csv

Movie data store karta hai.

Columns:

```text
title,genre,year,rating,votes,director
```

## 8. Agent Card Kya Hai?

Agent card endpoint:

```text
GET /.well-known/agent-card.json
```

Ye batata hai ki agent kya-kya kar sakta hai.

Capabilities:

```text
incident_management
knowledge_base_search
hotel_booking
movie_data_analysis
weather_lookup
csv_report_generation
```

Ye A2A style discovery ke liye useful hota hai.

## 9. Error Handling

Project me safe error handling add ki gayi hai.

Example:

Agar invalid tool name diya:

```json
{
  "tool_name": "wrong_tool",
  "arguments": {}
}
```

To API crash nahi hogi.

Response me error milega:

```json
{
  "tool_name": "wrong_tool",
  "status": "failed",
  "error": "Tool 'wrong_tool' is not available."
}
```

## 10. Demo Me Kya Bolna Hai?

Demo me aap aise explain kar sakti ho:

> Ye project ek FastAPI + LangGraph based A2A agent POC hai. Pehle ye sirf incident lookup karta tha. Ab humne isme tools-based architecture add kiya hai. Tools locally CSV files par kaam karte hain, isliye hume real ServiceNow, Jira, Slack, Teams ya email setup ki need nahi hai.

Phir bol sakti ho:

> `/a2a/tasks` existing agent flow ke liye hai. Ye natural message se incident number extract karta hai aur incident.csv me lookup karta hai. `/tools/run` new generic tool execution endpoint hai. Isme hum tool name aur arguments pass karte hain, aur backend correct Python function run karta hai.

Aur:

> Is POC me incident management, knowledge base search, hotel booking, movie data analysis, CSV report generation, aur weather lookup tools available hain. Sab tools directly testable hain through `/tools/run`.

## 11. Simple End-To-End Example

Request:

```json
{
  "tool_name": "search_incident",
  "arguments": {
    "incident_number": "INC99004"
  }
}
```

Flow:

```text
/tools/run receives request
        |
        v
tool_registry.py checks tool_name
        |
        v
search_incident function runs
        |
        v
data/incident.csv is searched
        |
        v
incident details returned as JSON
```

## 12. Short Summary

In short:

```text
FastAPI = API server
LangGraph = old incident lookup workflow
CSV files = local storage
Tool registry = tool router
Tools = actual executable functions
/tools/run = endpoint to test tools
```

Final one-line explanation:

> Ye POC show karta hai ki agent sirf chat response nahi deta, balki actual local tools execute karke business actions perform kar sakta hai.
