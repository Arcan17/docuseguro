from app.services.privacy.patterns import EMAIL_RE, PHONE_CL_RE, PII_PATTERNS, RUT_RE

# token_map maps readable_marker → original_value (e.g. "RUT_1" → "12.345.678-9")
TokenMap = dict[str, str]
ScrubResult = tuple[str, TokenMap, list[str]]

# Readable, type-tagged marker labels. Semantic + short markers (e.g. [RUT_1]) let
# the LLM keep track of which value is which and reproduce them verbatim — random
# UUIDs were indistinguishable and got swapped, scrambling the data.
_TYPE_LABEL = {"rut": "RUT", "email": "CORREO", "phone": "TELEFONO"}
_NER_LABEL = "NOMBRE"


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
        """Replace PII with readable type-tagged markers.

        Returns (clean_text, token_map, detected_types), where token_map maps each
        marker ("RUT_1", "CORREO_1", …) back to its original value. The same value
        always gets the same marker; different values of the same type increment the
        index.
        """
        original_text = text
        token_map: TokenMap = {}
        clean = text

        # Reverse lookup so the same value reuses its marker, and per-type counters.
        value_to_token: dict[str, str] = {}
        counters: dict[str, int] = {}

        def new_marker(label: str) -> str:
            counters[label] = counters.get(label, 0) + 1
            return f"{label}_{counters[label]}"

        for pattern, pii_type in PII_PATTERNS:
            label = _TYPE_LABEL.get(pii_type, "DATO")
            for match in pattern.finditer(original_text):
                original = match.group()
                if original not in value_to_token:
                    token = new_marker(label)
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
                        token = new_marker(_NER_LABEL)
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
