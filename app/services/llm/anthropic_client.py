from collections.abc import AsyncIterator

import anthropic

from app.core.config import settings
from app.core.constants import ANTHROPIC_MODEL

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


class AnthropicClient:
    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def complete(self, system: str, user: str) -> str:
        client = _get_client()
        message = await client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        content = message.content[0]
        return content.text if hasattr(content, "text") else str(content)

    async def stream(self, system: str, user: str) -> AsyncIterator[str]:
        client = _get_client()
        async with client.messages.stream(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            async for text in stream.text_stream:
                yield text
