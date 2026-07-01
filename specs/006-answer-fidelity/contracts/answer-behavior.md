# Contrato de comportamiento — Respuestas (P1)

No cambia el contrato HTTP del endpoint de consulta; cambia el **comportamiento** de la respuesta.

## Fidelidad al documento

- **Pregunta cuya respuesta NO está en los documentos** (matemáticas, historia, conocimiento general,
  o dato no incluido) → la respuesta es la **frase canónica de negativa**, p.ej.:
  > "Esa información no está en tus documentos."
  No se entrega el resultado de conocimiento del mundo ni un valor inventado.
- **Sin contexto relevante** (mejor similitud < `answer_min_similarity`) → misma frase canónica,
  **sin llamar al LLM**.
- **Pregunta cuya respuesta SÍ está** → respuesta normal apoyada en el contexto.
- **Pregunta mixta** (parte en el documento, parte externa) → responde la parte del documento y
  aclara que la parte externa no está en los documentos.

## PII legible

- Todo dato personal citado en la respuesta aparece **legible y correcto** (ej. `12.345.678-9`), no
  como marcador crudo.
- Con varios datos del mismo tipo (dos RUT), la respuesta devuelve el **correcto**, sin intercambio.
- Garantía de privacidad: el texto enviado al LLM contiene **solo marcadores** (`[RUT_1]`, …), nunca
  el valor real.

## Verificable por tests (sin LLM real)

- Guardarraíl de similitud: con chunks bajo umbral → frase canónica, LLM no invocado (mock sin
  llamadas).
- Prompt/negativa: con LLM mockeado devolviendo la frase canónica ante contexto insuficiente.
- PII: doc con dos RUT + un correo → preguntar por cada uno devuelve el valor correcto y legible; el
  prompt capturado (mock) no contiene ningún `original_value`.
