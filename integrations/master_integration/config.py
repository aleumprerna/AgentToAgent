import os
from functools import lru_cache

from pydantic import BaseModel


class IntegrationSettings(BaseModel):
    hr_agent_url: str = "http://localhost:8101"
    it_agent_url: str = "http://localhost:8102"
    servicenow_agent_url: str = "http://localhost:8103"
    hotel_agent_url: str = "http://localhost:8104"
    email_mcp_url: str = "http://localhost:8201/mcp"
    request_timeout_seconds: float = 10.0


@lru_cache
def get_integration_settings() -> IntegrationSettings:
    return IntegrationSettings(
        hr_agent_url=os.getenv("HR_AGENT_URL", "http://localhost:8101"),
        it_agent_url=os.getenv("IT_AGENT_URL", "http://localhost:8102"),
        servicenow_agent_url=os.getenv("SERVICENOW_AGENT_URL", "http://localhost:8103"),
        hotel_agent_url=os.getenv("HOTEL_AGENT_URL", "http://localhost:8104"),
        email_mcp_url=os.getenv("EMAIL_MCP_URL", "http://localhost:8201/mcp"),
        request_timeout_seconds=float(os.getenv("INTEGRATION_TIMEOUT_SECONDS", "10")),
    )
