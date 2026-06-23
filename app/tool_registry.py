from typing import Any, Callable

from app.tools.hotel_tools import (
    book_room,
    cancel_booking,
    check_room_availability,
    list_available_rooms,
)
from app.tools.incident_tools import (
    create_incident,
    list_incidents,
    search_incident,
    update_incident,
)
from app.tools.kb_tools import search_knowledge_base, suggest_resolution
from app.tools.movie_tools import generate_movie_csv, search_movie, top_movies_by_genre
from app.tools.weather_tools import get_weather


AVAILABLE_TOOLS: dict[str, Callable[..., Any]] = {
    "search_incident": search_incident,
    "create_incident": create_incident,
    "update_incident": update_incident,
    "list_incidents": list_incidents,
    "search_knowledge_base": search_knowledge_base,
    "suggest_resolution": suggest_resolution,
    "check_room_availability": check_room_availability,
    "book_room": book_room,
    "cancel_booking": cancel_booking,
    "list_available_rooms": list_available_rooms,
    "search_movie": search_movie,
    "top_movies_by_genre": top_movies_by_genre,
    "generate_movie_csv": generate_movie_csv,
    "get_weather": get_weather,
}


def call_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    tool = AVAILABLE_TOOLS.get(tool_name)
    if tool is None:
        return {
            "status": "failed",
            "error": f"Tool '{tool_name}' is not available.",
            "available_tools": sorted(AVAILABLE_TOOLS),
        }

    try:
        result = tool(**(arguments or {}))
        return {"status": "completed", "result": result}
    except TypeError as exc:
        return {
            "status": "failed",
            "error": f"Invalid arguments for tool '{tool_name}': {exc}",
        }
    except Exception as exc:
        return {"status": "failed", "error": f"Tool '{tool_name}' failed: {exc}"}
