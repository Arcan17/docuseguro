"""Groq LLM provider — free tier, OpenAI-compatible API."""
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
