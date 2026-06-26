import hashlib
import hmac
import time
import uuid as uuid_module
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import SYSTEM_PROMPT
from app.core.logging import get_logger
from app.services.cache.query_cache import CacheService, make_cache_key
from app.services.compression import compress_context
from app.services.ingestion.embedder import embed_query
from app.services.llm.base import LLMProvider
from app.services.privacy.restorer import restore
from app.services.privacy.scrubber import PIIScrubber
from app.services.privacy.stream_restorer import StreamingRestorer
from app.services.vector_store import SearchResult, search

logger = get_logger(__name__)


def _get_llm() -> LLMProvider:
    if settings.llm_provider == "anthropic":
        from app.services.llm.anthropic_client import AnthropicClient  # noqa: PLC0415

        return AnthropicClient()
    if settings.llm_provider == "groq":
        from app.services.llm.groq_client import GroqClient  # noqa: PLC0415

        return GroqClient()
    from app.services.llm.openai_client import OpenAIClient  # noqa: PLC0415

    return OpenAIClient()


_scrubber: PIIScrubber | None = None


def _get_scrubber() -> PIIScrubber:
    global _scrubber
    if _scrubber is None:
        _scrubber = PIIScrubber(spacy_enabled=settings.spacy_enabled)
    return _scrubber


class QueryResult:
    def __init__(
        self,
        answer: str,
        clean_query: str,
        session_id: str,
        cache_hit: bool,
        latency_ms: int,
        chunks: list[SearchResult],
        pii_found: bool,
        pii_types: list[str],
        provider: str,
        original_tokens: int | None,
        compressed_tokens: int | None,
    ) -> None:
        self.answer = answer
        self.clean_query = clean_query  # PII-stripped version safe for logging/notifications
        self.session_id = session_id
        self.cache_hit = cache_hit
        self.latency_ms = latency_ms
        self.chunks = chunks
        self.pii_found = pii_found
        self.pii_types = pii_types
        self.provider = provider
        self.original_tokens = original_tokens
        self.compressed_tokens = compressed_tokens

    @property
    def tokens_saved_pct(self) -> float | None:
        if self.original_tokens and self.compressed_tokens:
            return round((1 - self.compressed_tokens / self.original_tokens) * 100, 1)
        return None


class RAGPipeline:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._cache = CacheService(db)
        self._llm = _get_llm()
        self._scrubber = _get_scrubber()

    async def query(
        self, session_id: str, query_text: str, owner: str | None = None
    ) -> QueryResult:
        t0 = time.monotonic()
        # `owner` scopes retrieval (account or anonymous session). Defaults to the
        # session_id to preserve the previous anonymous-only behaviour.
        search_owner = owner if owner is not None else session_id
        # Extract the user id from an authenticated owner ("user:{id}") for logging.
        user_id = (
            int(owner.split(":", 1)[1])
            if owner is not None and owner.startswith("user:")
            else None
        )

        # Step 1: Strip PII from query before touching external services
        clean_query, token_map, pii_types = self._scrubber.scrub(query_text)
        pii_found = bool(token_map)

        # Persist PII tokens to DB for audit/debug visibility with TTL
        if pii_found:
            await self._persist_pii_tokens(session_id, token_map, pii_types)

        # Step 2: Embed (uses clean query — no PII sent to OpenAI embeddings)
        query_embedding = await embed_query(clean_query)

        # Step 3: Retrieve chunks with cosine similarity threshold.
        # Scoped to this owner: demo docs + only this owner's own uploads.
        chunks = await search(query_embedding, n_results=5, session_id=search_owner)

        if not chunks:
            latency = int((time.monotonic() - t0) * 1000)
            logger.info("no_context_found", session_id=session_id, latency_ms=latency)
            answer = "No encontré contexto relevante para responder esta consulta."
            await self._log_query(
                session_id=session_id,
                user_id=user_id,
                query_text=query_text,
                cache_hit=False,
                chunk_count=0,
                latency_ms=latency,
                provider="none",
                pii_found=pii_found,
                pii_types=pii_types,
            )
            return QueryResult(
                answer=answer,
                clean_query=clean_query,
                session_id=session_id,
                cache_hit=False,
                latency_ms=latency,
                chunks=[],
                pii_found=pii_found,
                pii_types=pii_types,
                provider="none",
                original_tokens=None,
                compressed_tokens=None,
            )

        # Step 4: Build cache key (sorted chunks for stability)
        sorted_chunks = sorted(chunks, key=lambda c: c.chunk_id)
        context_str = "\n".join(c.text for c in sorted_chunks)
        cache_key = make_cache_key(clean_query, context_str)

        # Step 5: Cache lookup
        cached = await self._cache.get(cache_key)
        if cached is not None:
            answer = restore(cached, token_map)
            latency = int((time.monotonic() - t0) * 1000)
            logger.info("cache_hit", session_id=session_id, latency_ms=latency)
            await self._log_query(
                session_id=session_id,
                user_id=user_id,
                query_text=query_text,
                cache_hit=True,
                chunk_count=len(chunks),
                latency_ms=latency,
                provider="cache",
                pii_found=pii_found,
                pii_types=pii_types,
            )
            return QueryResult(
                answer=answer,
                clean_query=clean_query,
                session_id=session_id,
                cache_hit=True,
                latency_ms=latency,
                chunks=chunks,
                pii_found=pii_found,
                pii_types=pii_types,
                provider="cache",
                original_tokens=None,
                compressed_tokens=None,
            )

        # Step 6: Compress context (cache miss path)
        compressed, original_tokens, compressed_tokens = compress_context(sorted_chunks)

        # Step 7: LLM call — no PII in compressed context or clean_query
        user_prompt = f"Context:\n{compressed}\n\nQuestion: {clean_query}"
        raw_answer = await self._llm.complete(system=SYSTEM_PROMPT, user=user_prompt)

        # Step 8: Restore PII in response
        answer = restore(raw_answer, token_map)

        # Step 9: Write to cache
        await self._cache.set(cache_key, raw_answer)

        latency = int((time.monotonic() - t0) * 1000)
        logger.info(
            "query_complete",
            session_id=session_id,
            cache_hit=False,
            provider=self._llm.provider_name,
            latency_ms=latency,
            chunks=len(chunks),
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
        )

        await self._log_query(
            session_id=session_id,
            query_text=query_text,
            cache_hit=False,
            chunk_count=len(chunks),
            latency_ms=latency,
            provider=self._llm.provider_name,
            pii_found=pii_found,
            pii_types=pii_types,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
        )

        return QueryResult(
            answer=answer,
            clean_query=clean_query,
            session_id=session_id,
            cache_hit=False,
            latency_ms=latency,
            chunks=chunks,
            pii_found=pii_found,
            pii_types=pii_types,
            provider=self._llm.provider_name,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
        )

    @staticmethod
    def _source_payload(chunks: list[SearchResult]) -> list[dict]:
        return [
            {
                "chunk_id": c.chunk_id,
                "doc_id": c.doc_id,
                "similarity": round(c.similarity, 4),
                # Longer preview so the highlighted passage keeps context.
                "text_preview": c.text[:400] + "…" if len(c.text) > 400 else c.text,
            }
            for c in chunks
        ]

    async def query_stream(
        self,
        session_id: str,
        query_text: str,
        owner: str | None = None,
        history: list[dict] | None = None,
    ):
        """Async generator que emite eventos dict: {"type":"delta"|"done", ...}.

        Replica el pipeline de query() pero transmite la respuesta del LLM token a
        token, restaurando PII sobre el flujo. El evento "done" lleva las métricas.
        Si `history` trae turnos previos, los incluye (sin PII) para seguimientos.
        """
        t0 = time.monotonic()
        history = history[-6:] if history else []
        # Scrub prior turns too — PII must not reach the LLM via the history.
        history_lines: list[str] = []
        for turn in history:
            clean_turn, _, _ = self._scrubber.scrub(str(turn.get("content", "")))
            speaker = "Usuario" if turn.get("role") == "user" else "Asistente"
            history_lines.append(f"{speaker}: {clean_turn}")
        history_block = "\n".join(history_lines)
        search_owner = owner if owner is not None else session_id
        user_id = (
            int(owner.split(":", 1)[1])
            if owner is not None and owner.startswith("user:")
            else None
        )

        clean_query, token_map, pii_types = self._scrubber.scrub(query_text)
        pii_found = bool(token_map)
        if pii_found:
            await self._persist_pii_tokens(session_id, token_map, pii_types)

        query_embedding = await embed_query(clean_query)
        chunks = await search(query_embedding, n_results=5, session_id=search_owner)

        if not chunks:
            yield {"type": "delta", "text": "No encontré contexto relevante para responder esta consulta."}
            latency = int((time.monotonic() - t0) * 1000)
            await self._log_query(
                session_id=session_id, query_text=query_text, user_id=user_id,
                cache_hit=False, chunk_count=0, latency_ms=latency, provider="none",
                pii_found=pii_found, pii_types=pii_types,
            )
            yield {
                "type": "done", "cache_hit": False, "latency_ms": latency, "chunk_count": 0,
                "pii_found": pii_found, "pii_types": pii_types, "provider": "none", "source_chunks": [],
            }
            return

        sorted_chunks = sorted(chunks, key=lambda c: c.chunk_id)
        context_str = "\n".join(c.text for c in sorted_chunks)
        cache_key = make_cache_key(clean_query, context_str)

        # Follow-ups depend on the conversation, so they bypass the answer cache.
        cached = None if history else await self._cache.get(cache_key)
        if cached is not None:
            yield {"type": "delta", "text": restore(cached, token_map)}
            latency = int((time.monotonic() - t0) * 1000)
            await self._log_query(
                session_id=session_id, query_text=query_text, user_id=user_id,
                cache_hit=True, chunk_count=len(chunks), latency_ms=latency, provider="cache",
                pii_found=pii_found, pii_types=pii_types,
            )
            yield {
                "type": "done", "cache_hit": True, "latency_ms": latency, "chunk_count": len(chunks),
                "pii_found": pii_found, "pii_types": pii_types, "provider": "cache",
                "source_chunks": self._source_payload(chunks),
            }
            return

        compressed, original_tokens, compressed_tokens = compress_context(sorted_chunks)
        convo = f"Conversación previa:\n{history_block}\n\n" if history_block else ""
        user_prompt = f"{convo}Context:\n{compressed}\n\nQuestion: {clean_query}"

        restorer = StreamingRestorer(token_map)
        raw_parts: list[str] = []
        async for delta in self._llm.stream(system=SYSTEM_PROMPT, user=user_prompt):
            raw_parts.append(delta)
            emit = restorer.feed(delta)
            if emit:
                yield {"type": "delta", "text": emit}
        tail = restorer.flush()
        if tail:
            yield {"type": "delta", "text": tail}

        raw_answer = "".join(raw_parts)
        await self._cache.set(cache_key, raw_answer)
        latency = int((time.monotonic() - t0) * 1000)
        await self._log_query(
            session_id=session_id, query_text=query_text, user_id=user_id,
            cache_hit=False, chunk_count=len(chunks), latency_ms=latency,
            provider=self._llm.provider_name, pii_found=pii_found, pii_types=pii_types,
            original_tokens=original_tokens, compressed_tokens=compressed_tokens,
        )
        yield {
            "type": "done", "cache_hit": False, "latency_ms": latency, "chunk_count": len(chunks),
            "pii_found": pii_found, "pii_types": pii_types, "provider": self._llm.provider_name,
            "source_chunks": self._source_payload(chunks),
        }

    async def _persist_pii_tokens(
        self, session_id: str, token_map: dict[str, str], pii_types: list[str]
    ) -> None:
        from app.models.pii_token import PIIToken  # noqa: PLC0415

        sid = self._parse_uuid(session_id)
        expires_at = datetime.now(UTC) + timedelta(seconds=settings.pii_token_ttl_seconds)

        # Infer pii_type per token from patterns
        from app.services.privacy.patterns import EMAIL_RE, PHONE_CL_RE, RUT_RE  # noqa: PLC0415

        for token, original in token_map.items():
            if RUT_RE.fullmatch(original.strip()):
                pii_type = "rut"
            elif EMAIL_RE.fullmatch(original.strip()):
                pii_type = "email"
            elif PHONE_CL_RE.search(original.strip()):
                pii_type = "phone"
            else:
                pii_type = "ner"

            row = PIIToken(
                session_id=sid,
                token=token,
                original_value=original,
                pii_type=pii_type,
                expires_at=expires_at,
            )
            self._db.add(row)

        try:
            await self._db.commit()
        except Exception as e:
            await self._db.rollback()
            logger.warning("pii_token_persist_failed", error=str(e))

    async def _log_query(
        self,
        session_id: str,
        query_text: str,
        cache_hit: bool,
        chunk_count: int,
        latency_ms: int,
        provider: str,
        pii_found: bool,
        pii_types: list[str],
        user_id: int | None = None,
        original_tokens: int | None = None,
        compressed_tokens: int | None = None,
    ) -> None:
        from app.models.query_log import QueryLog  # noqa: PLC0415

        sid = self._parse_uuid(session_id)
        secret = settings.effective_audit_secret.encode()
        log = QueryLog(
            user_id=user_id,
            session_id=sid,
            query_hash=hmac.new(secret, query_text.encode(), hashlib.sha256).hexdigest(),
            cache_hit=cache_hit,
            chunk_count=chunk_count,
            latency_ms=latency_ms,
            llm_provider=provider,
            pii_found=pii_found,
            pii_types=",".join(pii_types) if pii_types else None,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
        )
        self._db.add(log)
        try:
            await self._db.commit()
        except Exception as e:
            await self._db.rollback()
            logger.warning("query_log_failed", error=str(e))

    @staticmethod
    def _parse_uuid(session_id: str) -> UUID:
        try:
            return UUID(session_id) if "-" in session_id else UUID(int=int(session_id, 16))
        except (ValueError, AttributeError):
            return uuid_module.uuid4()
