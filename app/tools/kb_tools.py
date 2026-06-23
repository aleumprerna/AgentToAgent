from typing import Any

import pandas as pd

from app.config import resolve_csv_path


KB_CSV = "data/kb.csv"
SEARCH_COLUMNS = ["title", "category", "keywords", "content"]


def _load_kb() -> pd.DataFrame:
    return pd.read_csv(resolve_csv_path(KB_CSV), dtype=str).fillna("")


def _score_article(row: pd.Series, query_terms: list[str]) -> int:
    searchable_text = " ".join(str(row.get(column, "")) for column in SEARCH_COLUMNS).lower()
    return sum(1 for term in query_terms if term in searchable_text)


def search_knowledge_base(query: str) -> list[dict[str, Any]]:
    query_terms = [term for term in query.lower().split() if term]
    if not query_terms:
        return []

    df = _load_kb()
    scored_articles: list[tuple[int, dict[str, Any]]] = []
    for _, row in df.iterrows():
        score = _score_article(row, query_terms)
        if score > 0:
            article = row.to_dict()
            article["score"] = score
            scored_articles.append((score, article))

    scored_articles.sort(key=lambda item: item[0], reverse=True)
    return [article for _, article in scored_articles[:3]]


def suggest_resolution(incident_description: str) -> dict[str, Any]:
    matches = search_knowledge_base(incident_description)
    if not matches:
        return {
            "success": False,
            "message": "No matching KB article found.",
            "suggestion": None,
        }

    best_article = matches[0]
    return {
        "success": True,
        "message": f"Suggested resolution from KB article {best_article.get('id')}.",
        "article": best_article,
        "suggestion": best_article.get("content", ""),
    }
