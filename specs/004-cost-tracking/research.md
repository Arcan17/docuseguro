# Phase 0 — Research: Medidor de Costo de IA por Cliente

Resuelve las incógnitas técnicas de la spec 004, en especial la marcada como crítica: qué guarda hoy
`QueryLog` y qué falta para costear bien.

---

## Decisión 1 — Datos de tokens disponibles y qué falta

**Hallazgo (verificado en `app/models/query_log.py`):** `QueryLog` ya guarda:
`user_id` (nullable), `session_id`, `query_hash`, `cache_hit`, `chunk_count`, `original_tokens`,
`compressed_tokens`, `latency_ms`, **`llm_provider`** (nullable), `pii_found`, `pii_types`,
`created_at`.

- `original_tokens` y `compressed_tokens` miden el **ahorro del scrubber/compresión de contexto**
  (antes vs después de enmascarar/comprimir), NO el desglose input/output de la llamada al LLM.
- **`llm_provider` existe**, pero **NO existe `llm_model`** (modelo específico, p.ej.
  `llama-3.3-70b` vs `gpt-4o-mini`), que es necesario porque los precios son por modelo.
- **NO se registran `input_tokens` ni `output_tokens`** de la respuesta del LLM.

**Decisión:** extender `QueryLog` con:
- `llm_model: str | None` — modelo específico usado.
- `input_tokens: int | None` — tokens de entrada reales de la llamada (cuando el cliente LLM los
  reporte).
- `output_tokens: int | None` — tokens de salida reales.

Migración Alembic nueva, todos los campos **nullable** (las filas históricas quedan sin desglose y
se costean por estimación). Llenar estos campos al registrar la consulta es parte del alcance.

**Rationale:** sin el modelo y sin input/output reales, el costo es solo una estimación gruesa. Con
los campos nuevos el costo de las consultas futuras es exacto; las viejas se estiman y se marcan.

**Alternativas descartadas:** (a) inferir el modelo desde `llm_provider` — falla si un proveedor
ofrece varios modelos; (b) no guardar input/output y estimar siempre — pierde precisión para
siempre.

---

## Decisión 2 — Cómo estimar cuando falta el desglose input/output

**Decisión:** cuando `input_tokens`/`output_tokens` no estén, estimar:
- input ≈ `compressed_tokens` (lo que efectivamente se envió tras comprimir), y si falta,
  `original_tokens`.
- output ≈ input × `assumed_output_ratio` (configurable, por defecto un valor conservador, p.ej.
  0,25).
- El resultado se marca con un flag `estimated: true` en la salida.

**Rationale:** da un costo razonable para datos históricos sin inventar precisión. El flag deja
claro qué cifras son exactas y cuáles aproximadas (FR-002).

**Alternativas descartadas:** asumir output = 0 (subestima el costo real, peligroso para fijar
precios); pedir re-procesar el histórico (imposible, no se guardó la respuesta).

---

## Decisión 3 — Dónde viven los precios y el tipo de cambio ("sin redeploy")

**Hallazgo:** la config actual (`app/core/config.py`) es `pydantic-settings` desde `.env`. Cambiar un
valor en `.env` exige reiniciar/redeployar — incumple FR-003 ("sin redeploy").

**Decisión:** un **archivo de tarifas JSON** (`config/pricing.json`) leído **fresco en cada
reporte** (no cacheado en arranque). Contiene:
- lista de tarifas `{provider, model, input_per_million_usd, output_per_million_usd, effective_date}`
- `usd_clp_rate` (tipo de cambio) y su fecha
- `assumed_output_ratio` (para la estimación)

El operador edita el JSON en el servidor y el siguiente reporte ya usa los valores nuevos, sin
reiniciar. La ruta del archivo se define en `config.py` (`pricing_config_path`, default
`config/pricing.json`).

**Rationale:** la solución más simple que cumple "sin redeploy" para un operador único, y funciona
igual en on-premise. Editar un JSON es trivial.

**Alternativas descartadas:** (a) tabla en BD + endpoints CRUD de tarifas — más robusto pero mucho
más trabajo para un solo operador; queda como evolución futura; (b) variables de entorno — incumple
el requisito.

---

## Decisión 4 — Agrupación por cliente sin que exista "organización" todavía

**Hallazgo:** el concepto de organización lo trae la spec 002, aún sin implementar. `QueryLog` ya
tiene `user_id` (nullable).

**Decisión:** agrupar por `user_id`. Las consultas con `user_id = NULL` (anónimas/demo) caen a un
cubo **"anónimo/demo"** separado. La salida usa una clave de agrupación abstracta (`client_key`) para
que, cuando llegue la organización (002), se migre de agrupar por usuario a agrupar por org sin
cambiar el contrato del reporte.

**Rationale:** entrega valor hoy y no se pinta a una esquina: el contrato no menciona "usuario", sino
"cliente/agrupador".

**Alternativas descartadas:** esperar a la spec 002 — bloquea innecesariamente una feature que ya
puede dar valor.

---

## Decisión 5 — Quién paga el costo (operador vs cliente BYO/on-prem)

**Decisión:** marcar cada grupo con `billable_to_operator: bool`. Por defecto `true` (IA gestionada
por el operador). Una lista configurable en `pricing.json` (`byo_clients`) marca qué agrupadores son
BYO/on-premise → `false` (su costo es informativo, no lo paga el operador). El total del reporte
separa "costo que pago yo" de "costo informativo del cliente".

**Rationale:** cumple FR-010 (los 3 modos) sin necesidad de un modelo de facturación completo en v1.

**Alternativas descartadas:** inferir el modo desde la API key usada — no hay ese dato confiable hoy;
una lista explícita es simple y correcta.

---

## Decisión 6 — Endpoint y autenticación

**Decisión:** nuevo router `GET /costs` en `app/api/routers/costs.py`, protegido por
`require_api_key` (mismo mecanismo que `/metrics`). Parámetros: rango de fechas (o `hours`),
`group_by` (por ahora cliente), y filtro opcional por `client_key`. Devuelve un `CostReport`.

**Rationale:** reutiliza el patrón y la seguridad existentes; cero superficie nueva de auth.

**Alternativas descartadas:** extender `/metrics` — mezcla responsabilidades (métricas de
rendimiento vs costo); mejor un endpoint propio.

---

## Resumen de incógnitas resueltas

- ✅ `QueryLog` tiene `llm_provider` y `user_id`; faltan `llm_model`, `input_tokens`,
  `output_tokens` → se agregan con migración.
- ✅ Estimación marcada cuando falta el desglose.
- ✅ Precios y tipo de cambio en `config/pricing.json`, leído sin redeploy.
- ✅ Agrupar por `user_id` con cubo anónimo/demo, vía `client_key` abstracta.
- ✅ Marca operador-paga vs cliente-BYO.
- ✅ Endpoint propio `/costs` con la auth existente.

Sin `NEEDS CLARIFICATION` pendientes.
