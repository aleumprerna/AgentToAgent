from typing import Any

import httpx

from integrations.master_integration.config import get_integration_settings


async def call_a2a_agent(
    agent_url: str,
    message: str,
    conversation_id: str | None = None,
    metadata: dict | None = None,
) -> dict[str, Any]:
    settings = get_integration_settings()
    url = f"{agent_url.rstrip('/')}/a2a/chat"
    payload = {
        "task_id": conversation_id or "",
        "message": message,
    }
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return {
                "success": True,
                "agent_url": agent_url,
                "response": response.json(),
                "error": None,
            }
    except httpx.TimeoutException:
        return {"success": False, "agent_url": agent_url, "response": None, "error": "A2A request timed out."}
    except httpx.HTTPStatusError as exc:
        return {
            "success": False,
            "agent_url": agent_url,
            "response": None,
            "error": f"A2A request failed with HTTP {exc.response.status_code}: {exc.response.text}",
        }
    except ValueError:
        return {"success": False, "agent_url": agent_url, "response": None, "error": "A2A agent returned invalid JSON."}
    except httpx.RequestError as exc:
        return {"success": False, "agent_url": agent_url, "response": None, "error": f"A2A connection failed: {exc}"}
