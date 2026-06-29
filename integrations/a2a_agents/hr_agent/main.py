import os
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field


AGENT_NAME = "hr_agent"
DATA_PATH = Path(os.getenv("HR_POLICY_PATH", Path(__file__).parent / "data" / "hr_policy.txt"))

app = FastAPI(title="HR A2A Agent")


class ChatRequest(BaseModel):
    task_id: str = ""
    message: str
    conversation_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class TaskResponse(BaseModel):
    task_id: str
    agent: str
    status: str
    content: str
    data: dict = Field(default_factory=dict)


def _load_policy_text() -> tuple[str, bool]:
    if DATA_PATH.exists():
        return DATA_PATH.read_text(encoding="utf-8"), False
    return (
        "HR stores basic employee profile, onboarding, attendance, leave, payroll, "
        "benefits, and compliance information. Personal data is used only for "
        "employment operations and policy compliance.",
        True,
    )


@app.get("/health")
def health() -> dict:
    return {"status": "healthy", "agent": AGENT_NAME}


@app.get("/.well-known/agent-card.json")
def agent_card() -> dict:
    return {
        "name": AGENT_NAME,
        "description": "Answers HR policy, privacy, onboarding, leave, and employee data questions.",
        "version": "1.0.0",
        "capabilities": [
            "employee_data_policy",
            "privacy_policy",
            "leave_policy",
            "onboarding_guidance",
        ],
        "endpoint": "/a2a/chat",
    }


@app.post("/a2a/chat", response_model=TaskResponse)
def chat(request: ChatRequest) -> TaskResponse:
    policy_text, used_mock = _load_policy_text()
    content = (
        "As an HR policy assistant, here is the current POC guidance:\n\n"
        f"{policy_text}\n\n"
        "For production, this response can be replaced with document search over HR PDFs, DOC files, "
        "and policy repositories."
    )
    return TaskResponse(
        task_id=request.task_id,
        agent=AGENT_NAME,
        status="completed",
        content=content,
        data={"intent": "hr_policy", "mock": used_mock, "sources": [str(DATA_PATH)] if not used_mock else []},
    )
