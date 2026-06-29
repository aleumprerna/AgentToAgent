import re
from typing import Any

from integrations.master_integration.config import get_integration_settings


def extract_email_payload(message: str) -> dict[str, str]:
    email_match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", message)
    to = email_match.group(0) if email_match else "admin@admin.com"
    body = message
    say_match = re.search(r"\bsaying\s+(.+)$", message, re.IGNORECASE)
    if say_match:
        body = say_match.group(1).strip()
    return {"to": to, "subject": "Enterprise AI notification", "body": body, "cc": ""}


def _serialize_mcp_result(result: Any) -> Any:
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "dict"):
        return result.dict()
    return result


async def call_email_mcp(message: str) -> dict[str, Any]:
    settings = get_integration_settings()
    payload = extract_email_payload(message)
    try:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client

        async with streamablehttp_client(settings.email_mcp_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool("send_mock_email", payload)
                return {
                    "success": True,
                    "server_url": settings.email_mcp_url,
                    "tool": "send_mock_email",
                    "response": _serialize_mcp_result(result),
                    "payload": payload,
                    "error": None,
                }
    except Exception as exc:
        return {
            "success": False,
            "server_url": settings.email_mcp_url,
            "tool": "send_mock_email",
            "response": None,
            "payload": payload,
            "error": f"MCP call failed: {exc}",
        }
