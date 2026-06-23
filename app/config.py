import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()


class Settings(BaseModel):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    csv_path: str = "data/incident.csv"
    agent_name: str = "servicenow_incident_agent"
    agent_port: int = 8001


@lru_cache
def get_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        csv_path=os.getenv("CSV_PATH", "data/incident.csv"),
        agent_name=os.getenv("AGENT_NAME", "servicenow_incident_agent"),
        agent_port=int(os.getenv("AGENT_PORT", "8001")),
    )


def resolve_csv_path(csv_path: str) -> str:
    if os.path.isabs(csv_path):
        return csv_path

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, csv_path)
