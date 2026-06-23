import re
from datetime import datetime, timedelta
from typing import Any, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from app.config import get_settings
from app.csv_tools import lookup_incident_by_number
from app.tool_registry import call_tool


class IncidentState(TypedDict, total=False):
    task_id: str | None
    message: str
    incident_number: str | None
    tool_name: str | None
    tool_arguments: dict[str, Any] | None
    tool_result: dict[str, Any] | None
    row: dict[str, Any] | None
    status: str
    content: str


INCIDENT_PATTERN = re.compile(r"INC\d+", re.IGNORECASE)
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
BOOKING_PATTERN = re.compile(r"BK-[A-Z0-9]+", re.IGNORECASE)
PRIORITY_PATTERN = re.compile(r"\b(low|medium|high|critical)\b", re.IGNORECASE)
ROOM_TYPES = ("standard", "deluxe", "suite", "single", "double")


def _extract_dates(message: str) -> list[str]:
    return DATE_PATTERN.findall(message)


def _next_day(date: str) -> str:
    parsed = datetime.strptime(date, "%Y-%m-%d")
    return (parsed + timedelta(days=1)).strftime("%Y-%m-%d")


def _extract_room_type(message: str) -> str | None:
    lowered = message.lower()
    for room_type in ROOM_TYPES:
        if room_type in lowered:
            return room_type
    return None


def _extract_limit(message: str, default: int = 10) -> int:
    match = re.search(r"\btop\s+(\d+)\b|\blimit\s+(\d+)\b", message, re.IGNORECASE)
    if not match:
        return default
    return int(next(group for group in match.groups() if group))


def _extract_after_keywords(message: str, keywords: tuple[str, ...]) -> str:
    lowered = message.lower()
    for keyword in keywords:
        index = lowered.find(keyword)
        if index != -1:
            return message[index + len(keyword) :].strip(" :.-")
    return message.strip()


def _clean_short_value(value: str) -> str:
    return value.strip(" \t\r\n?.!,")


def _parse_tool_request(message: str) -> tuple[str | None, dict[str, Any] | None]:
    lowered = message.lower()
    dates = _extract_dates(message)
    incident_match = INCIDENT_PATTERN.search(message)

    if "weather" in lowered:
        city = _extract_after_keywords(message, ("weather in", "weather for"))
        city = re.sub(r"^(today'?s|current)\s+", "", city, flags=re.IGNORECASE).strip()
        city = _clean_short_value(city)
        if city:
            return "get_weather", {"city": city}

    if "cancel" in lowered and "booking" in lowered:
        booking_match = BOOKING_PATTERN.search(message)
        if booking_match:
            return "cancel_booking", {"booking_id": booking_match.group(0).upper()}

    if "book" in lowered and "room" in lowered:
        room_match = re.search(r"\broom\s+([A-Za-z0-9-]+)\b", message, re.IGNORECASE)
        guest_match = re.search(r"\bfor\s+([A-Za-z ]+?)(?:\s+from|\s+on|$)", message, re.IGNORECASE)
        if room_match and guest_match and dates:
            check_in = dates[0]
            check_out = dates[1] if len(dates) > 1 else _next_day(check_in)
            return "book_room", {
                "room_no": room_match.group(1),
                "guest_name": guest_match.group(1).strip(),
                "check_in": check_in,
                "check_out": check_out,
            }

    if ("available" in lowered or "availability" in lowered) and "room" in lowered and dates:
        if len(dates) > 1 or "from" in lowered:
            arguments: dict[str, Any] = {
                "check_in": dates[0],
                "check_out": dates[1] if len(dates) > 1 else _next_day(dates[0]),
            }
            room_type = _extract_room_type(message)
            if room_type:
                arguments["room_type"] = room_type
            return "check_room_availability", arguments
        return "list_available_rooms", {"date": dates[0]}

    if "knowledge" in lowered or "kb" in lowered:
        if "suggest" in lowered or "resolution" in lowered:
            description = _extract_after_keywords(message, ("for", "resolution for"))
            return "suggest_resolution", {"incident_description": description}
        query = _extract_after_keywords(message, ("for", "about", "search"))
        return "search_knowledge_base", {"query": query}

    if "movie" in lowered or "movies" in lowered:
        limit = _extract_limit(message)
        if "csv" in lowered or "generate" in lowered:
            genre = _extract_after_keywords(message, ("genre", "of", "top"))
            genre = re.sub(r"^\d+\s+", "", genre, flags=re.IGNORECASE).strip()
            return "generate_movie_csv", {"genre": genre or "Action", "limit": limit}
        if "top" in lowered:
            genre_match = re.search(r"\b(?:top\s+\d+\s+)?([A-Za-z]+)\s+movies\b", message, re.IGNORECASE)
            genre = genre_match.group(1) if genre_match else "Action"
            return "top_movies_by_genre", {"genre": genre, "limit": limit}
        title = _extract_after_keywords(message, ("movie", "for", "search"))
        return "search_movie", {"title": title}

    if "create" in lowered and "incident" in lowered:
        priority_match = PRIORITY_PATTERN.search(message)
        description = _extract_after_keywords(message, ("for", "incident"))
        return "create_incident", {
            "short_description": description or message,
            "priority": priority_match.group(1).title() if priority_match else "Medium",
            "caller": "A2A User",
            "category": "General",
        }

    if ("update" in lowered or "change" in lowered) and incident_match:
        priority_match = PRIORITY_PATTERN.search(message)
        if "priority" in lowered and priority_match:
            return "update_incident", {
                "incident_number": incident_match.group(0).upper(),
                "field": "priority",
                "value": priority_match.group(1).title(),
            }

    if "list" in lowered and "incident" in lowered:
        priority_match = PRIORITY_PATTERN.search(message)
        status_match = re.search(r"\b(?:status|state)\s+([A-Za-z]+)\b", message, re.IGNORECASE)
        arguments = {}
        if status_match:
            arguments["status"] = status_match.group(1)
        if priority_match:
            arguments["priority"] = priority_match.group(1).title()
        return "list_incidents", arguments

    return None, None


def route_tool_request(state: IncidentState) -> IncidentState:
    tool_name, tool_arguments = _parse_tool_request(state["message"])
    print(f"Resolved tool: {tool_name}")
    print(f"Resolved tool arguments: {tool_arguments}")
    return {**state, "tool_name": tool_name, "tool_arguments": tool_arguments}


def should_use_tool(state: IncidentState) -> str:
    return "tool" if state.get("tool_name") else "incident"


def execute_tool_request(state: IncidentState) -> IncidentState:
    tool_name = state.get("tool_name")
    tool_arguments = state.get("tool_arguments") or {}
    if not tool_name:
        return state
    tool_result = call_tool(tool_name, tool_arguments)
    print(f"Tool status: {tool_result.get('status')}")
    return {**state, "tool_result": tool_result}


def compose_tool_response(state: IncidentState) -> IncidentState:
    tool_name = state.get("tool_name")
    tool_result = state.get("tool_result") or {}
    result = tool_result.get("result")
    error = tool_result.get("error")

    if tool_result.get("status") == "failed":
        return {
            **state,
            "status": "failed",
            "content": error or f"Tool {tool_name} failed.",
            "row": None,
        }

    if isinstance(result, dict) and result.get("success") is False:
        return {
            **state,
            "status": "not_found",
            "content": result.get("error") or result.get("message") or f"{tool_name} returned no result.",
            "row": result,
        }

    return {
        **state,
        "status": "completed",
        "content": f"Tool {tool_name} completed successfully. Result: {result}",
        "row": result if isinstance(result, dict) else {"items": result},
    }


def extract_incident_number(state: IncidentState) -> IncidentState:
    message = state["message"]
    match = INCIDENT_PATTERN.search(message)
    incident_number = match.group(0).upper() if match else None

    print(f"Incoming message: {message}")
    print(f"Extracted incident number: {incident_number}")

    return {**state, "incident_number": incident_number}


def lookup_incident_csv(state: IncidentState) -> IncidentState:
    settings = get_settings()
    incident_number = state.get("incident_number")

    if not incident_number:
        print("CSV row found: false")
        return {**state, "row": None}

    row = lookup_incident_by_number(settings.csv_path, incident_number)
    print(f"CSV row found: {row is not None}")

    return {**state, "row": row}


def compose_response(state: IncidentState) -> IncidentState:
    settings = get_settings()
    incident_number = state.get("incident_number")
    row = state.get("row")

    if not incident_number:
        return {
            **state,
            "status": "failed",
            "content": "No incident number found in the request. Please provide an incident number like INC99004.",
        }

    if row is None:
        return {
            **state,
            "status": "not_found",
            "content": f"No incident found for {incident_number}.",
        }

    fallback_content = f"Incident {incident_number} found. Here are the details: {row}"

    if not settings.openai_api_key:
        return {**state, "status": "completed", "content": fallback_content}

    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
    )
    prompt = (
        "Format this ServiceNow incident row as a short, readable response. "
        f"Start with: Incident {incident_number} found. Here are the details:\n\n"
        f"Incident number: {incident_number}\n"
        f"Row data: {row}"
    )

    try:
        response = llm.invoke(prompt)
        return {**state, "status": "completed", "content": response.content}
    except Exception as exc:
        print(f"OpenAI response formatting failed, using fallback response: {exc}")
        return {**state, "status": "completed", "content": fallback_content}


def build_graph():
    graph = StateGraph(IncidentState)
    graph.add_node("route_tool_request", route_tool_request)
    graph.add_node("execute_tool_request", execute_tool_request)
    graph.add_node("compose_tool_response", compose_tool_response)
    graph.add_node("extract_incident_number", extract_incident_number)
    graph.add_node("lookup_incident_csv", lookup_incident_csv)
    graph.add_node("compose_response", compose_response)

    graph.set_entry_point("route_tool_request")
    graph.add_conditional_edges(
        "route_tool_request",
        should_use_tool,
        {
            "tool": "execute_tool_request",
            "incident": "extract_incident_number",
        },
    )
    graph.add_edge("execute_tool_request", "compose_tool_response")
    graph.add_edge("compose_tool_response", END)
    graph.add_edge("extract_incident_number", "lookup_incident_csv")
    graph.add_edge("lookup_incident_csv", "compose_response")
    graph.add_edge("compose_response", END)

    return graph.compile()


incident_graph = build_graph()
