import os
from typing import Any

import pandas as pd

from app.config import resolve_csv_path


MOVIES_CSV = "data/movies.csv"


def _load_movies() -> pd.DataFrame:
    df = pd.read_csv(resolve_csv_path(MOVIES_CSV), dtype=str).fillna("")
    df["rating_numeric"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0)
    df["votes_numeric"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0)
    return df


def _public_movie_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=["rating_numeric", "votes_numeric"], errors="ignore")


def search_movie(title: str) -> list[dict[str, Any]]:
    df = _load_movies()
    title_query = title.strip().lower()
    matches = df[df["title"].str.lower().str.contains(title_query, na=False)]
    return _public_movie_columns(matches).to_dict(orient="records")


def top_movies_by_genre(genre: str, limit: int = 10) -> list[dict[str, Any]]:
    df = _load_movies()
    wanted_genre = genre.strip().lower()
    matches = df[df["genre"].str.lower().str.contains(wanted_genre, na=False)]
    sorted_matches = matches.sort_values(
        by=["rating_numeric", "votes_numeric"],
        ascending=[False, False],
    ).head(limit)
    return _public_movie_columns(sorted_matches).to_dict(orient="records")


def generate_movie_csv(genre: str, limit: int = 10) -> dict[str, Any]:
    movies = top_movies_by_genre(genre, limit)
    os.makedirs(resolve_csv_path("exports"), exist_ok=True)
    safe_genre = "".join(char.lower() if char.isalnum() else "_" for char in genre).strip("_")
    output_path = resolve_csv_path(f"exports/top_{limit}_{safe_genre or 'movies'}_movies.csv")
    pd.DataFrame(movies).to_csv(output_path, index=False)
    return {
        "success": True,
        "message": f"Generated CSV with {len(movies)} movie rows.",
        "file_path": output_path,
        "rows": len(movies),
    }
