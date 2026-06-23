from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"]
    agent: str


class AgentCard(BaseModel):
    name: str
    description: str
    capabilities: list[str]
    endpoint: str
    input_examples: list[str]


class TaskRequest(BaseModel):
    task_id: str | None = None
    message: str


class TaskResponse(BaseModel):
    task_id: str | None = None
    agent: str
    status: Literal["completed", "not_found", "failed"]
    content: str
    data: dict[str, Any] | None = None


class ToolRunRequest(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolRunResponse(BaseModel):
    tool_name: str
    status: Literal["completed", "failed"]
    result: Any | None = None
    error: str | None = None
