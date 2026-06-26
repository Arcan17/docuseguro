from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.constants import OPENAI_MODEL

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


class OpenAIClient:
    @property
    def provider_name(self) -> str:
        return "openai"

    async def complete(self, system: str, user: str) -> str:
        client = _get_client()
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""

    async def stream(self, system: str, user: str) -> AsyncIterator[str]:
        client = _get_client()
        stream = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=1024,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
