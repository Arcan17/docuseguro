# Contrato — Endpoint de Reporte de Costo

## `GET /costs`

Reporte de costo de IA por cliente y período. **Solo operador.**

### Autenticación

Header `X-API-Key: <api_key>` — mismo mecanismo que `GET /metrics` (`require_api_key`). Sin clave
válida → `401`/`403`.

### Parámetros (query)

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `hours` | int (1–8760) | 720 | Ventana hacia atrás desde ahora. Ignorado si se pasan `from`/`to`. |
| `from` | fecha-hora ISO | — | Inicio del período (opcional). |
| `to` | fecha-hora ISO | — | Fin del período (opcional). |
| `client_key` | string | — | Filtra a un solo agrupador (opcional). |

### Respuesta `200` — `CostReport`

```json
{
  "period_from": "2026-06-01T00:00:00Z",
  "period_to": "2026-06-30T23:59:59Z",
  "usd_clp_rate": 950.0,
  "rate_stale": false,
  "clients": [
    {
      "client_key": "user-42",
      "queries": 320,
      "input_tokens": 640000,
      "output_tokens": 160000,
      "cost_usd": 0.62,
      "cost_clp": 589.0,
      "cost_usd_unmasked": 0.81,
      "savings_clp": 180.0,
      "billable_to_operator": true,
      "estimated": false,
      "price_missing": false
    },
    {
      "client_key": "anon-demo",
      "queries": 95,
      "input_tokens": 190000,
      "output_tokens": 47000,
      "cost_usd": 0.18,
      "cost_clp": 171.0,
      "cost_usd_unmasked": 0.24,
      "savings_clp": 57.0,
      "billable_to_operator": true,
      "estimated": true,
      "price_missing": false
    }
  ],
  "total_cost_usd_operator": 0.80,
  "total_cost_clp_operator": 760.0,
  "total_cost_clp_byo": 0.0,
  "total_savings_clp": 237.0
}
```

### Reglas del contrato

- **Sin datos personales:** la respuesta solo contiene agregados (conteos, tokens, montos) y la clave
  abstracta `client_key`. NUNCA contenido de documentos, RUT, correos, teléfonos ni `query_hash`.
- **Período vacío:** si no hay consultas, `clients: []` y todos los totales en `0`, con `200` (no
  error).
- **Tarifa faltante:** las filas afectadas traen `price_missing: true`; su costo se reporta como lo
  costeable y se señala el faltante (no se asume cero silencioso).
- **Estimación:** filas con datos históricos sin desglose input/output traen `estimated: true`.
- **Tipo de cambio vencido/ausente:** `rate_stale: true`; los montos USD se entregan igual.
- **Cuadre:** la suma de `cost_clp` de todas las filas iguala el costo total del período (invariante
  SC-005).

### Errores

| Código | Cuándo |
|--------|--------|
| `401` / `403` | Falta o es inválida la `X-API-Key`. |
| `422` | Parámetros inválidos (rango de fechas mal formado, `hours` fuera de rango). |
| `500` | Archivo de tarifas ausente o malformado (mensaje claro para que el operador lo corrija). |
