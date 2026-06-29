import re
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field


AGENT_NAME = "hotel_agent"
ROOMS: list[dict[str, Any]] = [
    {"room_no": "22", "type": "Deluxe", "available": True, "price_per_night": 2500},
    {"room_no": "31", "type": "Standard", "available": True, "price_per_night": 1500},
    {"room_no": "40", "type": "Suite", "available": False, "price_per_night": 5000},
]

app = FastAPI(title="Hotel Booking A2A Agent")


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


def _available_rooms(room_type: str | None = None) -> list[dict[str, Any]]:
    rooms = [room for room in ROOMS if room["available"]]
    if room_type:
        rooms = [room for room in rooms if room["type"].lower() == room_type.lower()]
    return rooms


def _book_room(message: str) -> dict[str, Any] | None:
    room_match = re.search(r"\broom\s+([A-Za-z0-9-]+)\b", message, re.IGNORECASE)
    guest_match = re.search(r"\bfor\s+([A-Za-z ]+?)(?:\s+on|\s+from|\s*$)", message, re.IGNORECASE)
    if not room_match:
        return None
    room_no = room_match.group(1)
    guest_name = guest_match.group(1).strip() if guest_match else "Guest"
    room = next((item for item in ROOMS if item["room_no"] == room_no), None)
    if not room:
        return {"booking_status": "not_found", "room_no": room_no, "guest_name": guest_name}
    if not room["available"]:
        return {"booking_status": "unavailable", "room_no": room_no, "guest_name": guest_name}
    room["available"] = False
    return {"booking_status": "confirmed_mock", "room_no": room_no, "guest_name": guest_name}


@app.get("/health")
def health() -> dict:
    return {"status": "healthy", "agent": AGENT_NAME}


@app.get("/.well-known/agent-card.json")
def agent_card() -> dict:
    return {
        "name": AGENT_NAME,
        "description": "Checks mock hotel availability and creates mock room bookings.",
        "version": "1.0.0",
        "capabilities": ["room_availability", "mock_room_booking", "room_price_lookup"],
        "endpoint": "/a2a/chat",
    }


@app.post("/a2a/chat", response_model=TaskResponse)
def chat(request: ChatRequest) -> TaskResponse:
    lowered = request.message.lower()
    if "book" in lowered and "room" in lowered:
        booking = _book_room(request.message)
        status = "completed" if booking and booking.get("booking_status") == "confirmed_mock" else "not_found"
        return TaskResponse(
            task_id=request.task_id,
            agent=AGENT_NAME,
            status=status,
            content=f"Mock booking result: {booking}",
            data={"intent": "hotel_booking", "mock": True, "booking": booking or {}},
        )

    room_type = next((kind for kind in ["deluxe", "standard", "suite"] if kind in lowered), None)
    rooms = _available_rooms(room_type)
    if rooms:
        answer = f"Available rooms: {rooms}"
    else:
        answer = "No matching rooms are currently available in the mock inventory."
    return TaskResponse(
        task_id=request.task_id,
        agent=AGENT_NAME,
        status="completed" if rooms else "not_found",
        content=answer,
        data={"intent": "hotel_availability", "mock": True, "available_rooms": rooms},
    )
