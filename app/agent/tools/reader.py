from typing import Optional
import httpx
from pydantic import BaseModel, Field
from app.core.config import settings


class ScrapedDocument(BaseModel):
    url: str
    title: Optional[str] = None
    markdown_content: str
    status_code: int


class JinaReaderClient:
    """Asynchronous client for converting web pages into clean LLM-friendly markdown."""

    def __init__(self, base_url: str = "https://r.jina.ai"):
        self.base_url = base_url.rstrip("/")

    async def fetch_markdown(self, target_url: str, max_chars: int = 8000) -> ScrapedDocument:
        """
        Prepends https://r.jina.ai/ to the target URL and retrieves cleaned markdown.
        Truncates at max_chars to preserve LLM token context.
        """
        clean_url = target_url.strip()
        if not clean_url.startswith(("http://", "https://")):
            clean_url = "https://" + clean_url

        jina_url = f"{self.base_url}/{clean_url}"

        headers = {
            "Accept": "text/event-stream, text/markdown, text/plain",
            "User-Agent": "ATHENEUS-Verification-Engine/1.0"
        }

        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = await client.get(jina_url, headers=headers)
            response.raise_for_status()
            content = response.text

        # Truncate to avoid context window explosion
        truncated_content = content[:max_chars]

        return ScrapedDocument(
            url=clean_url,
            markdown_content=truncated_content,
            status_code=response.status_code,
        )