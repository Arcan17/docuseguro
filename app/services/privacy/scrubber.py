from uuid import uuid4

from app.services.privacy.patterns import EMAIL_RE, PHONE_CL_RE, PII_PATTERNS, RUT_RE

# token_map maps uuid_token → original_value
TokenMap = dict[str, str]
ScrubResult = tuple[str, TokenMap, list[str]]


class PIIScrubber:
    def __init__(self, spacy_enabled: bool = False) -> None:
        self._nlp = None
        if spacy_enabled:
            try:
                import spacy  # type: ignore[import-untyped]

                self._nlp = spacy.load("es_core_news_sm")
            except Exception:
                pass  # fall back to regex only

    def scrub(self, text: str) -> ScrubResult:
        """Replace PII with UUID tokens. Returns (clean_text, token_map, detected_types)."""
        original_text = text
        token_map: TokenMap = {}
        clean = text

        # Build reverse lookup to avoid creating duplicate tokens for same value
        value_to_token: dict[str, str] = {}

        for pattern, _ in PII_PATTERNS:
            for match in pattern.finditer(original_text):
                original = match.group()
                if original not in value_to_token:
                    token = str(uuid4())
                    value_to_token[original] = token
                    token_map[token] = original

        # Apply substitutions — longest first to prevent partial overlaps
        for original, token in sorted(value_to_token.items(), key=lambda x: -len(x[0])):
            clean = clean.replace(original, f"[{token}]")

        # Optional spaCy NER for PERSON / ORG
        if self._nlp is not None:
            doc = self._nlp(clean)
            for ent in doc.ents:
                if ent.label_ in {"PER", "ORG"}:
                    original = ent.text
                    if original not in value_to_token and "[" not in original:
                        token = str(uuid4())
                        value_to_token[original] = token
                        token_map[token] = original
                        clean = clean.replace(original, f"[{token}]")

        detected = self._detected_types(original_text, bool(self._nlp and token_map))
        return clean, token_map, detected

    def _detected_types(self, text: str, has_ner_hits: bool) -> list[str]:
        types: set[str] = set()
        if RUT_RE.search(text):
            types.add("rut")
        if EMAIL_RE.search(text):
            types.add("email")
        if PHONE_CL_RE.search(text):
            types.add("phone")
        if has_ner_hits:
            types.add("ner")
        return sorted(types)
