"""Arcade action runtime and normalized live-news retrieval for Dredge."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse


ARCADE_NEWS_TOOL = "GoogleNews.SearchNewsStories"


class ArcadeRuntimeError(RuntimeError):
    """Raised when Arcade cannot safely complete a tool execution."""


class ArcadeAuthorizationRequired(ArcadeRuntimeError):
    """Signal that the user must finish Arcade authorization and retry."""

    def __init__(self, tool_name: str, authorization_url: Optional[str]) -> None:
        self.tool_name = tool_name
        self.authorization_url = _safe_https_url(authorization_url)
        super().__init__(f"Authorization required for {tool_name}")


@dataclass(frozen=True)
class ArcadeToolResult:
    tool_name: str
    value: Any
    execution_id: Optional[str] = None
    duration: Optional[float] = None


class ArcadeRuntime:
    """Execute a small allowlist of Arcade tools with per-user authorization."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        client: Any = None,
        allowed_tools: Optional[Iterable[str]] = None,
    ) -> None:
        configured_tools = allowed_tools or _configured_tools()
        self.allowed_tools = frozenset(
            tool.strip() for tool in configured_tools if tool and tool.strip()
        )
        if client is not None:
            self._client = client
            return

        resolved_key = (api_key or os.environ.get("ARCADE_API_KEY") or "").strip()
        if not resolved_key:
            raise ArcadeRuntimeError("ARCADE_API_KEY is not configured")
        try:
            from arcadepy import Arcade
        except ImportError as exc:
            raise ArcadeRuntimeError(
                "arcadepy is not installed. Run: pip install arcadepy"
            ) from exc
        self._client = Arcade(api_key=resolved_key)

    def execute(
        self, *, tool_name: str, input: Dict[str, Any], user_id: str
    ) -> ArcadeToolResult:
        """Authorize and execute one allowlisted tool without exposing tokens."""

        if tool_name not in self.allowed_tools:
            raise ArcadeRuntimeError("The requested Arcade tool is not allowlisted")
        if not user_id.strip():
            raise ArcadeRuntimeError("A session user ID is required for Arcade")

        authorization = self._client.tools.authorize(
            tool_name=tool_name,
            user_id=user_id,
        )
        if getattr(authorization, "status", None) != "completed":
            raise ArcadeAuthorizationRequired(
                tool_name,
                getattr(authorization, "url", None),
            )

        response = self._client.tools.execute(
            tool_name=tool_name,
            input=input,
            user_id=user_id,
        )
        if not getattr(response, "success", False):
            raise ArcadeRuntimeError("Arcade could not complete the selected tool")
        output = getattr(response, "output", None)
        return ArcadeToolResult(
            tool_name=tool_name,
            value=getattr(output, "value", None),
            execution_id=getattr(response, "execution_id", None),
            duration=getattr(response, "duration", None),
        )


class ArcadeNewsSearchAdapter:
    """Use Arcade's Google News tool as a Dredge evidence source."""

    def __init__(self, runtime: ArcadeRuntime, *, user_id: str) -> None:
        self.runtime = runtime
        self.user_id = user_id

    def search(self, query: str, *, max_results: int = 5) -> Dict[str, Any]:
        query = query.strip()
        if not query:
            raise ValueError("query must not be empty")
        if max_results < 1 or max_results > 10:
            raise ValueError("max_results must be between 1 and 10")

        execution = self.runtime.execute(
            tool_name=ARCADE_NEWS_TOOL,
            input={"keywords": query},
            user_id=self.user_id,
        )
        payload = execution.value if isinstance(execution.value, dict) else {}
        stories = payload.get("news_results") or []
        if not isinstance(stories, list):
            stories = []
        sources: List[Dict[str, Any]] = []
        for index, story in enumerate(stories[:max_results], start=1):
            if not isinstance(story, dict):
                continue
            sources.append(
                {
                    "id": f"source-{index}",
                    "title": story.get("title"),
                    "url": story.get("link"),
                    "content": story.get("snippet") or story.get("title"),
                    "publisher": story.get("source"),
                }
            )
        return {
            "query": query,
            "answer": None,
            "sources": sources,
            "provider": "Arcade",
            "tool": execution.tool_name,
            "execution_id": execution.execution_id,
            "duration": execution.duration,
        }


def _configured_tools() -> List[str]:
    raw = os.environ.get("ARCADE_TOOL_ALLOWLIST") or ARCADE_NEWS_TOOL
    return raw.split(",")


def _safe_https_url(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme == "https" and parsed.netloc:
        return value
    return None
