from typing import Any

import pandas as pd

from app.config import resolve_csv_path


def lookup_incident_by_number(csv_path: str, incident_number: str) -> dict[str, Any] | None:
    path = resolve_csv_path(csv_path)
    df = pd.read_csv(path, dtype=str).fillna("")

    if "number" not in df.columns:
        raise ValueError("CSV file must contain a 'number' column.")

    normalized_target = incident_number.strip().upper()
    matches = df[df["number"].str.strip().str.upper() == normalized_target]

    if matches.empty:
        return None

    return matches.iloc[0].to_dict()
