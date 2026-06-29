import os
import re
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.config import resolve_csv_path
from app.csv_tools import lookup_incident_by_number


AGENT_NAME = "servicenow_agent"
INCIDENT_CSV_PATH = os.getenv("SERVICENOW_INCIDENT_CSV_PATH", os.getenv("CSV_PATH", "data/incident.csv"))
PROBLEM_CSV_PATH = os.getenv("SERVICENOW_PROBLEM_CSV_PATH", "data/problem.csv")
INCIDENT_PATTERN = re.compile(r"\bINC\d+\b", re.IGNORECASE)
PROBLEM_PATTERN = re.compile(r"\bPRB\d+\b", re.IGNORECASE)

app = FastAPI(title="ServiceNow Consultant A2A Agent")


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
    data: dict[str, Any] = Field(default_factory=dict)


def _csv_exists(csv_path: str) -> bool:
    return Path(resolve_csv_path(csv_path)).exists()


def _load_csv(csv_path: str) -> pd.DataFrame | None:
    path = resolve_csv_path(csv_path)
    if not Path(path).exists():
        return None
    try:
        return pd.read_csv(path, dtype=str).fillna("")
    except UnicodeDecodeError:
        return pd.read_csv(path, dtype=str, encoding="cp1252").fillna("")


def _lookup_record_by_number(csv_path: str, record_number: str) -> dict[str, Any] | None:
    df = _load_csv(csv_path)
    if df is None or "number" not in df.columns:
        return None
    normalized_target = record_number.strip().upper()
    matches = df[df["number"].str.strip().str.upper() == normalized_target]
    if matches.empty:
        return None
    return matches.iloc[0].to_dict()


def _search_csv_keywords(message: str, csv_path: str, record_type: str) -> dict[str, Any] | None:
    df = _load_csv(csv_path)
    if df is None:
        return None
    searchable_columns = [
        column
        for column in [
            "number",
            "short_description",
            "description",
            "state",
            "priority",
            "caller_id",
            "assignment_group",
            "assigned_to",
            "category",
            "resolution_code",
            "cmdb_ci",
            "related_incidents",
            "solution",
            "resolution_notes",
        ]
        if column in df.columns
    ]
    terms = [term for term in re.findall(r"[a-z0-9]+", message.lower()) if len(term) > 2]
    best_row = None
    best_score = 0
    for _, row in df.iterrows():
        haystack = " ".join(str(row[column]).lower() for column in searchable_columns)
        score = sum(1 for term in terms if term in haystack)
        if score > best_score:
            best_row = row.to_dict()
            best_score = score
    if not best_row:
        return None
    return {"record_type": record_type, "row": best_row, "score": best_score}


def _format_record(row: dict[str, Any], record_type: str) -> str:
    number = row.get("number", "matching record")
    useful_fields = [
        "short_description",
        "state",
        "priority",
        "category",
        "assignment_group",
        "assigned_to",
        "caller_id",
        "opened_at",
        "sys_updated_on",
        "resolution_code",
        "cmdb_ci",
        "related_incidents",
    ]
    details = [f"- {key}: {row[key]}" for key in useful_fields if row.get(key)]
    label = "incident" if record_type == "incident" else "problem"
    if not details:
        details = [f"- {key}: {value}" for key, value in row.items() if value]
    return f"ServiceNow {label} record {number} found.\n" + "\n".join(details)


def _source_for_record_type(record_type: str) -> str:
    return resolve_csv_path(INCIDENT_CSV_PATH if record_type == "incident" else PROBLEM_CSV_PATH)


@app.get("/health")
def health() -> dict:
    return {"status": "healthy", "agent": AGENT_NAME}


@app.get("/.well-known/agent-card.json")
def agent_card() -> dict:
    return {
        "name": AGENT_NAME,
        "description": "Looks up incidents/problems and gives mock ServiceNow consultant guidance.",
        "version": "1.0.0",
        "capabilities": [
            "incident_lookup",
            "problem_search",
            "issue_resolution_guidance",
            "csv_record_search",
        ],
        "endpoint": "/a2a/chat",
    }


@app.post("/a2a/chat", response_model=TaskResponse)
def chat(request: ChatRequest) -> TaskResponse:
    metadata = {
        "intent": "servicenow_consulting",
        "mock": True,
        "incident_csv_found": _csv_exists(INCIDENT_CSV_PATH),
        "problem_csv_found": _csv_exists(PROBLEM_CSV_PATH),
    }
    incident_match = INCIDENT_PATTERN.search(request.message)
    if incident_match and metadata["incident_csv_found"]:
        incident_number = incident_match.group(0).upper()
        row = lookup_incident_by_number(INCIDENT_CSV_PATH, incident_number)
        if row:
            return TaskResponse(
                task_id=request.task_id,
                agent=AGENT_NAME,
                status="completed",
                content=_format_record(row, "incident"),
                data={
                    **metadata,
                    "matched_record": incident_number,
                    "record_type": "incident",
                    "source": _source_for_record_type("incident"),
                    "record": row,
                },
            )

    problem_match = PROBLEM_PATTERN.search(request.message)
    if problem_match and metadata["problem_csv_found"]:
        problem_number = problem_match.group(0).upper()
        row = _lookup_record_by_number(PROBLEM_CSV_PATH, problem_number)
        if row:
            return TaskResponse(
                task_id=request.task_id,
                agent=AGENT_NAME,
                status="completed",
                content=_format_record(row, "problem"),
                data={
                    **metadata,
                    "matched_record": problem_number,
                    "record_type": "problem",
                    "source": _source_for_record_type("problem"),
                    "record": row,
                },
            )

    matches = [
        match
        for match in [
            _search_csv_keywords(request.message, INCIDENT_CSV_PATH, "incident"),
            _search_csv_keywords(request.message, PROBLEM_CSV_PATH, "problem"),
        ]
        if match
    ]
    if matches:
        best_match = max(matches, key=lambda item: item["score"])
        row = best_match["row"]
        record_type = best_match["record_type"]
        return TaskResponse(
            task_id=request.task_id,
            agent=AGENT_NAME,
            status="completed",
            content=_format_record(row, record_type),
            data={
                **metadata,
                "matched_record": row.get("number"),
                "record_type": record_type,
                "source": _source_for_record_type(record_type),
                "record": row,
            },
        )

    answer = (
        "I could not find a matching incident/problem in the CSV for this POC. "
        "As a ServiceNow consultant, I would capture the affected service, impact, urgency, recent changes, "
        "error messages, and troubleshooting already attempted, then map it to a likely incident or KB article."
    )
    return TaskResponse(
        task_id=request.task_id,
        agent=AGENT_NAME,
        status="not_found",
        content=answer,
        data=metadata,
    )
