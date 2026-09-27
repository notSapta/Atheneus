from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field
from app.core.config import settings


class SearchResultItem(BaseModel):
    title: str = Field(..., description="Web page title")
    url: str = Field(..., description="Target URL")
    content: str = Field(..., description="Extracted textual snippet")
    score: float = Field(default=0.0, description="Relevance score from search engine")


class TavilySearchClient:
    """Asynchronous client for querying the Tavily Search API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.TAVILY_API_KEY
        self.endpoint = "https://api.tavily.com/search"

    async def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> List[SearchResultItem]:
        """
        Executes an asynchronous search query via Tavily.
        """
        if not self.api_key or self.api_key.startswith("tvly-your_actual"):
            raise ValueError("A valid TAVILY_API_KEY must be configured in .env")

        payload: Dict[str, Any] = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results or settings.DEFAULT_MAX_SEARCH_RESULTS,
            "include_answer": False,
            "include_raw_content": False,
        }

        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains

        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(self.endpoint, json=payload)
            response.raise_for_status()
            data = response.json()

        results: List[SearchResultItem] = []
        for raw in data.get("results", []):
            results.append(
                SearchResultItem(
                    title=raw.get("title", "No Title"),
                    url=raw.get("url", ""),
                    content=raw.get("content", ""),
                    score=float(raw.get("score", 0.0)),
                )
            )
        return results