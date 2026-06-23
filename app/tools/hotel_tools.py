from datetime import datetime
from typing import Any
from uuid import uuid4

import pandas as pd

from app.config import resolve_csv_path


ROOMS_CSV = "data/rooms.csv"
DATE_FORMAT = "%Y-%m-%d"


def _load_rooms() -> pd.DataFrame:
    return pd.read_csv(resolve_csv_path(ROOMS_CSV), dtype=str).fillna("")


def _save_rooms(df: pd.DataFrame) -> None:
    df.to_csv(resolve_csv_path(ROOMS_CSV), index=False)


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, DATE_FORMAT)


def _validate_date_range(check_in: str, check_out: str) -> tuple[datetime, datetime]:
    start = _parse_date(check_in)
    end = _parse_date(check_out)
    if end <= start:
        raise ValueError("check_out must be after check_in.")
    return start, end


def _covers_dates(row: pd.Series, check_in: datetime, check_out: datetime) -> bool:
    available_from = _parse_date(str(row["available_from"]))
    available_to = _parse_date(str(row["available_to"]))
    return available_from <= check_in and available_to >= check_out


def check_room_availability(
    check_in: str,
    check_out: str,
    room_type: str | None = None,
) -> list[dict[str, Any]]:
    start, end = _validate_date_range(check_in, check_out)
    df = _load_rooms()
    df = df[df["status"].str.lower() == "available"]
    if room_type:
        wanted_type = room_type.strip().lower()
        df = df[df["type"].str.strip().str.lower() == wanted_type]

    available = [
        row.to_dict()
        for _, row in df.iterrows()
        if _covers_dates(row, start, end)
    ]
    return available


def book_room(
    room_no: str,
    guest_name: str,
    check_in: str,
    check_out: str,
) -> dict[str, Any]:
    _validate_date_range(check_in, check_out)
    df = _load_rooms()
    target = room_no.strip()
    mask = df["room_no"].str.strip() == target
    if not mask.any():
        return {"success": False, "error": f"Room {target} was not found."}

    room = df.loc[mask].iloc[0]
    if str(room["status"]).lower() != "available":
        return {"success": False, "error": f"Room {target} is not available."}

    if not check_room_availability(check_in, check_out):
        return {"success": False, "error": "No rooms are available for those dates."}

    start, end = _validate_date_range(check_in, check_out)
    if not _covers_dates(room, start, end):
        return {"success": False, "error": f"Room {target} is not available for those dates."}

    booking_id = f"BK-{uuid4().hex[:8].upper()}"
    df.loc[mask, "status"] = "booked"
    df.loc[mask, "guest_name"] = guest_name.strip()
    df.loc[mask, "booking_id"] = booking_id
    df.loc[mask, "available_from"] = check_in
    df.loc[mask, "available_to"] = check_out
    _save_rooms(df)

    booked_room = df.loc[mask].iloc[0].to_dict()
    return {
        "success": True,
        "message": f"Room {target} booked.",
        "booking_id": booking_id,
        "room": booked_room,
    }


def cancel_booking(booking_id: str) -> dict[str, Any]:
    df = _load_rooms()
    target = booking_id.strip().upper()
    mask = df["booking_id"].str.strip().str.upper() == target
    if not mask.any():
        return {"success": False, "error": f"Booking {target} was not found."}

    df.loc[mask, "status"] = "available"
    df.loc[mask, "guest_name"] = ""
    df.loc[mask, "booking_id"] = ""
    _save_rooms(df)
    return {"success": True, "message": f"Booking {target} cancelled."}


def list_available_rooms(date: str) -> list[dict[str, Any]]:
    wanted_date = _parse_date(date)
    df = _load_rooms()
    df = df[df["status"].str.lower() == "available"]
    return [
        row.to_dict()
        for _, row in df.iterrows()
        if _covers_dates(row, wanted_date, wanted_date)
    ]
