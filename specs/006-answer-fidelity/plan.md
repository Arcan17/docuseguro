# Implementation Plan: Respuestas Fieles al Documento + PII Legible + Ingesta Robusta

**Branch**: `006-answer-fidelity` | **Date**: 2026-06-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/006-answer-fidelity/spec.md`

## Summary

Endurecer DocuSeguro para que (P1a) responda **solo** con lo que está en los documentos —negándose a
matemáticas/historia/conocimiento general— y (P1b) muestre los **datos personales del documento
legibles y correctos** en las respuestas, sin dejar de enmascararlos antes de la IA. Todo sobre el
pipeline RAG existente. Las fases P2/P3 (ingesta robusta, OCR local, más formatos) se documentan como
trabajo posterior.

El plan detalla las dos historias P1 (implementables ya) y deja P2/P3 en menor detalle.

## Technical Context

**Language/Version**: Python 3.11 (backend)

**Primary Dependencies**: FastAPI, SQLAlchemy async, Alembic, ChromaDB, tiktoken (todo ya presente).
OCR (P3) agregaría una dependencia **local** (no cloud) — fuera del alcance P1.

**Storage**: PostgreSQL (tabla `pii_tokens` existente) + ChromaDB (chunks). Los mapas de PII de
documento se guardan en PostgreSQL (no en el vector store) para no dejar valores reales en Chroma.

**Testing**: pytest. Se mockea el LLM para probar el guardarraíl y la restauración sin llamadas
externas (patrón ya usado en tests existentes).

**Target Platform**: Linux server (backend)

**Project Type**: Web service (backend). El frontend no cambia en P1 (mismo contrato de respuesta).

**Performance Goals**: El guardarraíl de fidelidad puede **ahorrar** llamadas al LLM (corto-circuito
cuando no hay contexto suficiente). Sin regresión de latencia perceptible en el camino normal.

**Constraints**: La IA nunca recibe datos personales reales (Principio I). El guardarraíl no debe
producir falsos "no está en tus documentos" en preguntas legítimamente respondibles.

**Scale/Scope**: Volumen piloto/demo. Diseño estable para crecer.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | ¿Aplica? | Cumplimiento |
|-----------|----------|--------------|
| **I. Privacidad Primero** | Sí (central) | La PII se sigue enmascarando ANTES del LLM; solo cambia el formato del marcador y que se restaure también la PII del documento. Los valores reales del documento se guardan en PostgreSQL, no en el vector store. ✅ |
| **II. IA con Costo Flexible** | Indirecto | El guardarraíl ahorra tokens (corto-circuito sin LLM cuando no hay contexto). Sin conflicto. ✅ |
| **III. Configurable por Cliente** | Parcial | El umbral de fidelidad y el prompt son configurables. ✅ |
| **IV. Madurez de Datos por Fase** | Sí | P1 no agrega manejo de datos nuevos. OCR (P3) de datos reales queda restringido a on-premise/Fase 4. ✅ |
| **V. Entrega por Fases** | Sí | P1 ahora; P2/P3 después. ✅ |
| **VI. Spec-Driven** | Sí | spec → plan (este) → tasks → implement. ✅ |

**Resultado del gate**: PASA.

## Project Structure

### Documentation (this feature)

```text
specs/006-answer-fidelity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── answer-behavior.md
└── tasks.md            # /speckit-tasks (no lo crea este comando)
```

### Source Code (repository root)

```text
app/
├── core/
│   ├── constants.py            # MODIFICAR — SYSTEM_PROMPT endurecido (español, negativa explícita)
│   └── config.py               # MODIFICAR — umbral de fidelidad configurable (answer_min_similarity)
├── services/
│   ├── rag_pipeline.py         # MODIFICAR — guardarraíl de fidelidad + restauración de PII de documento
│   └── privacy/
│       ├── scrubber.py         # MODIFICAR — marcadores legibles [RUT_1]/[CORREO_1]/[TELEFONO_1]
│       ├── restorer.py         # (sin cambio de API; sigue restaurando [token]→original)
│       ├── stream_restorer.py  # (igual; funciona con marcadores legibles)
│       └── doc_pii.py          # NUEVO — guardar/cargar el mapa de PII por documento + re-etiquetado
├── models/
│   └── pii_token.py            # MODIFICAR — permitir alcance por documento (doc_id, sin unique global)
└── api/routers/
    └── ingest.py               # MODIFICAR — conservar el token_map del documento (hoy se descarta)

alembic/versions/
└── XXXX_pii_token_doc_scope.py # NUEVO — migración para el alcance por documento

tests/
├── test_answer_fidelity.py     # NUEVO — rechaza matemáticas/historia; responde lo que sí está
├── test_scrubber.py            # MODIFICAR — marcadores legibles
├── test_stream_restorer.py     # MODIFICAR — marcadores legibles
└── test_doc_pii_restore.py     # NUEVO — 2 RUT + correo: legibles, sin intercambio; IA no ve PII
```

**Structure Decision**: Web service de un proyecto. Se toca el pipeline y el módulo de privacidad,
reutilizando todo lo existente. La lógica nueva de PII de documento vive en `app/services/privacy/
doc_pii.py` para no inflar `rag_pipeline.py`.

## Fases P2/P3 (menor detalle — trabajo posterior)

- **P2 Ingesta robusta**: la política de archivos ilegibles/no soportados (mensajes 422 en español)
  ya está implementada; queda consolidarla y cubrir con tests de router.
- **P3 OCR local**: agregar OCR **en el servidor** (nunca cloud, por Principio I) para imágenes y
  PDFs escaneados; solo habilitado en on-premise / nube Fase 4 para datos reales. Decisión de motor
  (p.ej. Tesseract local) y dependencia se resuelven en un plan propio cuando se aborde.
- **P3 Formatos**: `.csv` (preservando filas/columnas como ya hace el extractor de xlsx) y `.pptx`.

## Complexity Tracking

Sin violaciones de la constitución que justificar.
