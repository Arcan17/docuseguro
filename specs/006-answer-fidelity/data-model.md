# Phase 1 — Data Model: Respuestas Fieles + PII Legible (P1)

## 1. Cambios a `pii_tokens` (modelo existente `PIIToken`)

Hoy `PIIToken` guarda el mapa de PII de la **consulta**, con `token` **único global** y TTL. Para
guardar también el mapa por **documento** sin colisiones:

| Campo | Cambio | Descripción |
|-------|--------|-------------|
| `doc_id` | **NUEVO** (String, nullable, indexado) | Documento dueño del marcador. `NULL` = mapa de consulta (comportamiento actual). |
| `token` | **quitar unique global** | El marcador legible (`RUT_1`) se repite entre documentos; deja de ser único global. La unicidad pasa a ser por `(doc_id, token)` / `(session_id, token)`. |
| `original_value` | igual | Valor real (RUT/correo/teléfono). Vive solo en PostgreSQL. |
| `pii_type` | igual | rut / email / phone. |
| `expires_at` | igual | TTL. Para documento = vida del documento (efímero anónimo; persistente con spec 002). |

Migración Alembic: agrega `doc_id`, ajusta índices/constraint de unicidad. Compatible hacia atrás
(filas de consulta existentes tienen `doc_id = NULL`).

> Nota: `token` es `String(36)` hoy (largo de UUID). Los marcadores legibles son más cortos; el
> tipo sigue sirviendo. Se puede reducir el largo, pero no es necesario.

## 2. Entidades lógicas del flujo (no todas persistidas)

### Marcador de almacenamiento (por documento)

- Vive en el texto de los chunks del documento (en Chroma) y como fila en `pii_tokens` con `doc_id`.
- Formato legible por tipo e índice **dentro de ese documento**: `RUT_1`, `CORREO_1`, `TELEFONO_1`.
- Mapea a su `original_value` en PostgreSQL.

### Marcador de presentación (por consulta)

- Se construye **en memoria en cada consulta**, secuencial por tipo, único sobre todo el contexto
  ensamblado + la consulta. Es lo único que ve el LLM.
- `display_map: dict[marcador_presentación -> original]` — usado para restaurar la respuesta.
- No se persiste.

### Mapa de PII de consulta (existente)

- El `token_map` que hoy produce `scrub()` sobre el texto de la consulta. Se integra al espacio de
  marcadores de presentación (deduplicando por `original_value`).

## 3. Configuración nueva

| Ajuste | Dónde | Default | Descripción |
|--------|-------|---------|-------------|
| `answer_min_similarity` | `app/core/config.py` | ~0.63 | Umbral de la mejor similitud bajo el cual se responde "no está en tus documentos" sin llamar al LLM. Configurable (calibrable con evals). |

`SYSTEM_PROMPT` (en `app/core/constants.py`) se reescribe endurecido; no es "dato" pero es parte del
contrato de comportamiento.

## 4. Flujo de datos (consulta, con PII de documento)

```
scrub(query) ──► token_map de consulta ─┐
                                         ├─► espacio de marcadores de PRESENTACIÓN (dedupe por valor)
search() ──► chunks (con doc_id) ──► cargar pii_tokens por doc_id ─┘         │
   │                                                                         ▼
   └─ mejor_similitud < answer_min_similarity ? ──► SÍ ──► "no está en tus documentos" (sin LLM)
                                                    │
                                                    NO
                                                    ▼
   contexto con marcadores de presentación ──► compress_context ──► LLM (SYSTEM_PROMPT endurecido)
                                                                        │
                                              restore(respuesta, display_map) ──► respuesta final legible
```

**Invariantes:**
- El texto que llega al LLM (contexto + consulta) **no contiene ningún `original_value`** (SC-004).
- La respuesta final no contiene marcadores sin restaurar ni valores intercambiados (SC-003).
- Si `mejor_similitud < answer_min_similarity`, no hay llamada al LLM y la respuesta es la frase
  canónica de negativa (SC-001).
