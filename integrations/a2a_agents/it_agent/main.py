from fastapi import FastAPI
from pydantic import BaseModel, Field


AGENT_NAME = "it_agent"
app = FastAPI(title="IT Consultant A2A Agent")


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


@app.get("/health")
def health() -> dict:
    return {"status": "healthy", "agent": AGENT_NAME}


@app.get("/.well-known/agent-card.json")
def agent_card() -> dict:
    return {
        "name": AGENT_NAME,
        "description": "Provides IT system design, QA, estimation, architecture, and risk guidance.",
        "version": "1.0.0",
        "capabilities": [
            "system_design_advisor",
            "qa_test_case_generator",
            "project_estimation_assistant",
            "risk_and_dependency_analyzer",
            "basic_architecture_reviewer",
        ],
        "endpoint": "/a2a/chat",
    }


def _answer(message: str) -> str:
    lowered = message.lower()
    if "test" in lowered or "qa" in lowered:
        return (
            "Here is a POC QA response:\n"
            "1. Validate happy-path login with valid username and password.\n"
            "2. Validate incorrect password, unknown user, locked account, and empty field errors.\n"
            "3. Verify password masking, session creation, audit logging, and rate limiting.\n"
            "4. Check security cases such as SQL injection strings, brute-force attempts, and expired sessions.\n"
            "5. Cover browser, mobile, accessibility, and performance smoke scenarios."
        )
    if "cost" in lowered or "estimate" in lowered or "effort" in lowered:
        return (
            "For a POC estimate, split the project into discovery, design, implementation, testing, "
            "deployment, and support. A small integration POC is typically 2-4 weeks depending on API "
            "readiness, security review, data quality, and test environment access."
        )
    return (
        "As an IT consultant, I recommend starting with clear functional boundaries, a simple API contract, "
        "stateless services, centralized logging, environment-based configuration, and focused test cases. "
        "For this POC, keep the architecture lightweight and validate integration behavior before adding "
        "production RAG, workflow orchestration, or persistence."
    )


@app.post("/a2a/chat", response_model=TaskResponse)
def chat(request: ChatRequest) -> TaskResponse:
    return TaskResponse(
        task_id=request.task_id,
        agent=AGENT_NAME,
        status="completed",
        content=_answer(request.message),
        data={"intent": "it_consulting", "mock": True},
    )
