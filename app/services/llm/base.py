from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    async def complete(self, system: str, user: str) -> str:
        ...

    def stream(self, system: str, user: str) -> AsyncIterator[str]:
        """Yield the answer in text deltas as they are generated."""
        ...

    @property
    def provider_name(self) -> str:
        ...
