"""Restaura PII sobre un flujo de texto (streaming).

Los tokens en la respuesta tienen forma `[<uuid>]` y pueden quedar partidos entre
dos chunks del stream. Este buffer retiene el texto desde un `[` sin cerrar hasta
ver el `]`, de modo que nunca emite un token a medio reemplazar.
"""

from app.services.privacy.restorer import restore
from app.services.privacy.scrubber import TokenMap


class StreamingRestorer:
    def __init__(self, token_map: TokenMap) -> None:
        self._tm = token_map
        self._buf = ""

    def feed(self, delta: str) -> str:
        """Acepta un chunk del LLM y devuelve el texto seguro para emitir."""
        self._buf += delta
        out: list[str] = []
        while True:
            i = self._buf.find("[")
            if i == -1:
                out.append(self._buf)
                self._buf = ""
                break
            if i > 0:
                out.append(self._buf[:i])
                self._buf = self._buf[i:]
            j = self._buf.find("]")
            if j == -1:
                # token incompleto: esperar más chunks
                break
            token_text = self._buf[: j + 1]
            inner = token_text[1:-1]
            out.append(self._tm.get(inner, token_text))
            self._buf = self._buf[j + 1 :]
        return "".join(out)

    def flush(self) -> str:
        """Emite lo que quede en el buffer al terminar el stream."""
        remaining = restore(self._buf, self._tm)
        self._buf = ""
        return remaining
