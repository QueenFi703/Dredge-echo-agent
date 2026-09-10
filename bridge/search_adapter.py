"""Live web retrieval adapter for Dredge Echo using Tavily."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional


class SearchBackendError(Exception):
    """Raised when the configured search backend is unavailable."""


class TavilySearchAdapter:
    """Small, deterministic wrapper around Tavily Search for agent retrieval."""

    def __init__(self, api_key: Optional[str] = None, project: Optional[str] = None) -> None:
        self._api_key = (api_key or os.environ.get("TAVILY_API_KEY") or "").strip()
        self._project = (project or os.environ.get("TAVILY_PROJECT") or "").strip()

        if not self._api_key:
            raise SearchBackendError("TAVILY_API_KEY is not configured")

        try:
            from tavily import TavilyClient  # type: ignore
        except ImportError as exc:
            raise SearchBackendError(
                "tavily-python is not installed. Run: pip install 'aster-lang[research]'"
            ) from exc

        kwargs: Dict[str, Any] = {"api_key": self._api_key}
        if self._project:
            kwargs["project_id"] = self._project
        self._client = TavilyClient(**kwargs)

    def search(self, query: str, *, max_results: int = 5) -> Dict[str, Any]:
        """Search the live web and normalize evidence for downstream reasoning."""
        query = query.strip()
        if not query:
            raise ValueError("query must not be empty")
        if max_results < 1 or max_results > 10:
            raise ValueError("max_results must be between 1 and 10")

        response = self._client.search(
            query=query,
            auto_parameters=True,
            include_answer=True,
            include_raw_content=False,
            max_results=max_results,
        )

        raw_results = response.get("results") or []
        sources: List[Dict[str, Any]] = []
        for item in raw_results:
            sources.append(
                {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "content": item.get("content"),
                    "score": item.get("score"),
                }
            )

        return {
            "query": response.get("query") or query,
            "answer": response.get("answer"),
            "sources": sources,
            "response_time": response.get("response_time"),
        }
