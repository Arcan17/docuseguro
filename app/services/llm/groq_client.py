"""Groq LLM provider — free tier, OpenAI-compatible API."""
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.constants import GROQ_MODEL


class GroqClient:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    @property
    def provider_name(self) -> str:
        return "groq"

    async def complete(self, system: str, user: str) -> str:
        response = await self._client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""

    async def stream(self, system: str, user: str) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=GROQ_MODEL,
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
