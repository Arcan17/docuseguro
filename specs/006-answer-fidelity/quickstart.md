# Quickstart — Respuestas Fieles + PII Legible (P1)

Cómo quedará y cómo probarlo una vez implementado.

## Fidelidad al documento

1. Sube un documento (ej. un contrato) que no habla de matemáticas ni historia.
2. Pregunta "¿cuánto es 15 × 3?" → responde **"Esa información no está en tus documentos."**
3. Pregunta "¿en qué año llegó el hombre a la Luna?" → misma negativa.
4. Pregunta algo que **sí** está en el contrato (ej. "¿cuál es la renta mensual?") → responde
   correctamente.

Ajuste fino: si aparecen negativas en preguntas legítimas, bajar `answer_min_similarity` en la
configuración; si se cuela conocimiento general, subirlo. Calibrar con la suite de evals.

## PII legible

1. Sube un documento con dos RUT distintos (arrendador y arrendatario) y un correo.
2. Pregunta "¿cuál es el RUT del arrendatario?" → responde el RUT **correcto y legible**
   (`12.345.678-9`), no un marcador ni el RUT del arrendador.
3. Pregunta "¿cuál es el correo de contacto?" → devuelve el correo real.

Garantía: en los logs/tests, el texto enviado a la IA contiene solo `[RUT_1]`, `[RUT_2]`,
`[CORREO_1]` — nunca los valores reales.

## Migración

```bash
alembic upgrade head   # agrega doc_id a pii_tokens y ajusta la unicidad
```

## Pruebas

```bash
pytest tests/test_answer_fidelity.py tests/test_doc_pii_restore.py \
       tests/test_scrubber.py tests/test_stream_restorer.py -q
```

Cubren:
- Rechazo de matemáticas/historia sobre un documento que no las contiene (SC-001).
- Respuesta correcta cuando el dato sí está (SC-002).
- Dos RUT + correo: valores correctos, legibles, sin intercambio (SC-003).
- El prompt enviado a la IA no contiene ningún valor personal real (SC-004).
- Marcadores legibles `[RUT_1]` en el scrubber y su restauración (incl. streaming).
