from app.services.privacy.scrubber import TokenMap


def restore(text: str, token_map: TokenMap) -> str:
    """Replace UUID tokens back with original PII values in LLM response."""
    result = text
    for token, original in token_map.items():
        result = result.replace(f"[{token}]", original)
    return result
