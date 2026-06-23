from datetime import datetime
import re
from typing import Any

import pandas as pd

from app.config import resolve_csv_path


INCIDENT_CSV = "data/incident.csv"
INCIDENT_COLUMNS = [
    "number",
    "short_description",
    "priority",
    "state",
    "caller",
    "category",
    "assigned_to",
    "opened_at",
]
ALLOWED_UPDATE_FIELDS = {
    "short_description",
    "priority",
    "state",
    "status",
    "caller",
    "category",
    "assigned_to",
}


def _load_incidents() -> pd.DataFrame:
    df = pd.read_csv(resolve_csv_path(INCIDENT_CSV), dtype=str).fillna("")
    for column in INCIDENT_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    return df[INCIDENT_COLUMNS]


def _save_incidents(df: pd.DataFrame) -> None:
    df.to_csv(resolve_csv_path(INCIDENT_CSV), index=False)


def _normalize_number(incident_number: str) -> str:
    return incident_number.strip().upper()


def _find_row(df: pd.DataFrame, incident_number: str) -> pd.Series | None:
    target = _normalize_number(incident_number)
    matches = df[df["number"].str.strip().str.upper() == target]
    if matches.empty:
        return None
    return matches.iloc[0]


def _next_incident_number(df: pd.DataFrame) -> str:
    max_number = 10000
    for number in df["number"].fillna(""):
        match = re.fullmatch(r"INC(\d+)", str(number).strip().upper())
        if match:
            max_number = max(max_number, int(match.group(1)))
    return f"INC{max_number + 1}"


def search_incident(incident_number: str) -> dict[str, Any]:
    df = _load_incidents()
    row = _find_row(df, incident_number)
    if row is None:
        return {
            "success": False,
            "error": f"Incident {_normalize_number(incident_number)} was not found.",
        }
    return {"success": True, "incident": row.to_dict()}


def create_incident(
    short_description: str,
    priority: str,
    caller: str,
    category: str,
) -> dict[str, Any]:
    df = _load_incidents()
    new_incident = {
        "number": _next_incident_number(df),
        "short_description": short_description.strip(),
        "priority": priority.strip(),
        "state": "New",
        "caller": caller.strip(),
        "category": category.strip(),
        "assigned_to": "",
        "opened_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    df = pd.concat([df, pd.DataFrame([new_incident])], ignore_index=True)
    _save_incidents(df)
    return {
        "success": True,
        "message": f"Incident {new_incident['number']} created.",
        "incident": new_incident,
    }


def update_incident(incident_number: str, field: str, value: str) -> dict[str, Any]:
    df = _load_incidents()
    normalized_field = field.strip().lower()
    if normalized_field == "status":
        normalized_field = "state"
    if normalized_field not in ALLOWED_UPDATE_FIELDS:
        return {
            "success": False,
            "error": f"Field '{field}' cannot be updated.",
            "allowed_fields": sorted(ALLOWED_UPDATE_FIELDS),
        }

    target = _normalize_number(incident_number)
    mask = df["number"].str.strip().str.upper() == target
    if not mask.any():
        return {"success": False, "error": f"Incident {target} was not found."}

    df.loc[mask, normalized_field] = value.strip()
    _save_incidents(df)
    updated = df.loc[mask].iloc[0].to_dict()
    return {
        "success": True,
        "message": f"Incident {target} updated.",
        "incident": updated,
    }


def list_incidents(
    status: str | None = None,
    priority: str | None = None,
) -> list[dict[str, Any]]:
    df = _load_incidents()
    if status:
        wanted_status = status.strip().lower()
        df = df[df["state"].str.strip().str.lower() == wanted_status]
    if priority:
        wanted_priority = priority.strip().lower()
        df = df[df["priority"].str.strip().str.lower() == wanted_priority]
    return df.to_dict(orient="records")
