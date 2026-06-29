from typing import Any

from integrations.master_integration.a2a_client import call_a2a_agent
from integrations.master_integration.config import get_integration_settings
from integrations.master_integration.mcp_client import call_email_mcp


ROUTES = [
    (
        "email_mcp",
        "mcp",
        ["send email", "send mail", "notify by email", "draft email"],
    ),
    (
        "hr_agent",
        "a2a",
        ["hr", "employee", "privacy", "policy", "information collect", "personal data", "leave", "onboarding", "salary policy", "attendance"],
    ),
    (
        "it_agent",
        "a2a",
        ["system design", "architecture", "qa", "test case", "testing", "project cost", "estimate", "effort", "sprint", "module", "technical design"],
    ),
    (
        "servicenow_agent",
        "a2a",
        ["incident", "problem", "inc", "vpn", "password", "login issue", "email down", "email service", "servicenow", "ticket", "kb", "issue", "error"],
    ),
    (
        "hotel_agent",
        "a2a",
        ["hotel", "room", "booking", "available", "availability", "check-in", "checkout", "deluxe", "suite"],
    ),
]


def _match_route(message: str) -> tuple[str, str, str] | None:
    lowered = message.lower()
    for agent, integration_type, keywords in ROUTES:
        for keyword in keywords:
            if keyword in lowered:
                return agent, integration_type, keyword
    return None


def _agent_url(agent: str) -> str:
    settings = get_integration_settings()
    urls = {
        "hr_agent": settings.hr_agent_url,
        "it_agent": settings.it_agent_url,
        "servicenow_agent": settings.servicenow_agent_url,
        "hotel_agent": settings.hotel_agent_url,
    }
    return urls[agent]


async def route_user_message(message: str, conversation_id: str | None = None) -> dict[str, Any]:
    match = _match_route(message)
    if not match:
        print("[ROUTER] selected_agent=none reason=no keyword match")
        return {
            "selected_integration_type": None,
            "selected_agent": None,
            "answer": "",
            "raw_response": None,
            "routed": False,
        }

    selected_agent, integration_type, keyword = match
    print(f"[ROUTER] selected_agent={selected_agent} reason=matched keyword {keyword}")

    if integration_type == "mcp":
        raw_response = await call_email_mcp(message)
        response = raw_response.get("response") or {}
        to_address = (raw_response.get("payload") or {}).get("to", "admin@admin.com")
        answer = (
            f"Your message has been sent to {to_address}."
            if raw_response["success"]
            else f"Email MCP call failed: {raw_response['error']}"
        )
        return {
            "selected_integration_type": "mcp",
            "selected_agent": selected_agent,
            "answer": answer,
            "raw_response": raw_response if response is not None else raw_response,
            "routed": True,
        }

    raw_response = await call_a2a_agent(
        _agent_url(selected_agent),
        message=message,
        conversation_id=conversation_id,
    )
    if raw_response["success"]:
        response_body = raw_response.get("response") or {}
        answer = response_body.get("content") or response_body.get("answer", "")
    else:
        answer = f"{selected_agent} call failed: {raw_response['error']}"
    return {
        "selected_integration_type": "a2a",
        "selected_agent": selected_agent,
        "answer": answer,
        "raw_response": raw_response,
        "routed": True,
    }
