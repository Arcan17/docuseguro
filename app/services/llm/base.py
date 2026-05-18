from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    async def complete(self, system: str, user: str) -> str:
        ...

    @property
    def provider_name(self) -> str:
        ...
