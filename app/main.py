from fastapi import FastAPI

from app.config import get_settings
from app.graph import incident_graph
from app.schemas import (
    AgentCard,
    HealthResponse,
    TaskRequest,
    TaskResponse,
    ToolRunRequest,
    ToolRunResponse,
)
from app.tool_registry import call_tool


settings = get_settings()
app = FastAPI(title="A2A ServiceNow Incident Agent")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", agent=settings.agent_name)


@app.get("/.well-known/agent-card.json", response_model=AgentCard)
def agent_card() -> AgentCard:
    return AgentCard(
        name=settings.agent_name,
        description=(
            "Runs local CSV/API tools for incident management, knowledge base search, "
            "hotel booking, movie data analysis, weather lookup, and CSV report generation."
        ),
        capabilities=[
            "incident_lookup",
            "csv_record_search",
            "incident_management",
            "knowledge_base_search",
            "hotel_booking",
            "movie_data_analysis",
            "weather_lookup",
            "csv_report_generation",
        ],
        endpoint="/a2a/tasks",
        input_examples=[
            "Tell me about INC99004",
            "Create an incident for laptop not working",
            "Update INC99004 priority to High",
            "Find KB article for VPN issue",
            "Suggest resolution for laptop is slow",
            "Is deluxe room available on 2026-06-25?",
            "Book room 22 for Shantanu on 2026-06-25",
            "Create CSV of top 10 action movies",
            "What is the weather in Jaipur?",
        ],
    )


@app.post("/a2a/tasks", response_model=TaskResponse)
def run_task(request: TaskRequest) -> TaskResponse:
    result = incident_graph.invoke(
        {
            "task_id": request.task_id,
            "message": request.message,
        }
    )

    return TaskResponse(
        task_id=request.task_id,
        agent=settings.agent_name,
        status=result["status"],
        content=result["content"],
        data=result.get("row"),
    )


@app.post("/tools/run", response_model=ToolRunResponse)
def run_tool(request: ToolRunRequest) -> ToolRunResponse:
    tool_result = call_tool(request.tool_name, request.arguments)
    return ToolRunResponse(
        tool_name=request.tool_name,
        status=tool_result["status"],
        result=tool_result.get("result"),
        error=tool_result.get("error"),
    )
