# Phase 1 — Data Model: Medidor de Costo de IA por Cliente

## 1. Cambios al modelo existente `QueryLog`

Tabla `query_log` (existente). Se agregan tres columnas, todas nullable (compatibilidad con filas
históricas), vía migración Alembic.

| Campo | Tipo | Null | Descripción |
|-------|------|------|-------------|
| `llm_model` | String(40) | sí | Modelo específico que atendió la consulta (p.ej. `llama-3.3-70b-versatile`). Necesario para tarifar por modelo. |
| `input_tokens` | Integer | sí | Tokens de entrada reales de la llamada al LLM, si el cliente los reporta. |
| `output_tokens` | Integer | sí | Tokens de salida reales de la llamada al LLM, si el cliente los reporta. |

Campos existentes reutilizados: `user_id` (agrupador), `llm_provider`, `original_tokens`,
`compressed_tokens`, `created_at`.

**Reglas de validación / llenado:**
- Al registrar una consulta nueva, se llena `llm_model` y, si el proveedor los entrega,
  `input_tokens`/`output_tokens`.
- Filas históricas (sin estos campos) se costean por estimación (ver `research.md`, Decisión 2).

---

## 2. Entidades de configuración (archivo `config/pricing.json`)

No son tablas de BD; viven en un archivo editable sin redeploy.

### Tarifa de proveedor (`ProviderRate`)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `provider` | string | Proveedor (`groq`, `openai`, `anthropic`). |
| `model` | string | Modelo específico al que aplica la tarifa. |
| `input_per_million_usd` | number | Precio USD por 1.000.000 de tokens de entrada. |
| `output_per_million_usd` | number | Precio USD por 1.000.000 de tokens de salida. |
| `effective_date` | string (fecha) | Desde cuándo rige la tarifa (permite no recalcular el pasado). |

### Configuración global de costeo (raíz del archivo)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `usd_clp_rate` | number | Tipo de cambio USD→CLP. |
| `usd_clp_rate_date` | string (fecha) | Fecha del tipo de cambio (para advertir si está vencido). |
| `assumed_output_ratio` | number | Proporción output/input para estimar cuando falta el desglose (default 0.25). |
| `byo_clients` | string[] | Lista de `client_key` cuyo costo NO lo paga el operador (BYO/on-premise). |
| `rates` | ProviderRate[] | Lista de tarifas. |

**Reglas:**
- Si una consulta usa un `provider`+`model` sin tarifa vigente → se marca `price_missing: true` (no
  se cuenta como costo cero).
- Si `usd_clp_rate` falta o su fecha está vencida → el reporte muestra USD igual y advierte sobre el
  CLP.

---

## 3. Entidades de salida (no persistidas — se calculan por reporte)

### `ClientCostRow` — costo de un agrupador en el período

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `client_key` | string | Identificador del agrupador (hoy = usuario; `"anon-demo"` para anónimos). |
| `queries` | int | Número de consultas en el período. |
| `input_tokens` | int | Tokens de entrada (reales + estimados). |
| `output_tokens` | int | Tokens de salida (reales + estimados). |
| `cost_usd` | number | Costo real estimado en USD (tokens comprimidos/enviados × tarifa). |
| `cost_clp` | number | Costo en CLP (USD × tipo de cambio). |
| `cost_usd_unmasked` | number | Costo que habría tenido SIN enmascarar (con `original_tokens`). |
| `savings_clp` | number | Ahorro por el scrubber en CLP (`cost_unmasked − cost_real`). |
| `billable_to_operator` | bool | `false` si el agrupador es BYO/on-premise. |
| `estimated` | bool | `true` si alguna fila del grupo se costeó por estimación. |
| `price_missing` | bool | `true` si alguna consulta no tenía tarifa configurada. |

### `CostReport` — respuesta completa

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `period_from` / `period_to` | fecha-hora | Rango cubierto. |
| `usd_clp_rate` | number | Tipo de cambio usado. |
| `rate_stale` | bool | `true` si el tipo de cambio está vencido o ausente. |
| `clients` | ClientCostRow[] | Filas por agrupador, ordenadas por costo descendente. |
| `total_cost_usd_operator` | number | Suma de costos facturables al operador. |
| `total_cost_clp_operator` | number | Idem en CLP. |
| `total_cost_clp_byo` | number | Costo informativo de clientes BYO (no lo paga el operador). |
| `total_savings_clp` | number | Ahorro total del scrubber en el período. |

**Invariante de cuadre (SC-005):** la suma de `cost` de todas las filas `clients` (operador + BYO +
anónimo) iguala el costo total del sistema en el período.

---

## 4. Relación entre entidades

```
QueryLog (BD, por consulta)
   │  agrupar por user_id (→ client_key)  +  filtrar por created_at (período)
   ▼
ClientCostRow (calculada)  ── usa ──►  ProviderRate / config global (config/pricing.json)
   │
   ▼
CostReport (calculada)  ── expone solo agregados, NUNCA datos personales ──►  endpoint GET /costs
```
