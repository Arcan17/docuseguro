# Quickstart — Medidor de Costo de IA por Cliente

Cómo usar y probar la feature una vez implementada.

## 1. Configurar las tarifas

Crear/editar `config/pricing.json` en el servidor (editable sin redeploy):

```json
{
  "usd_clp_rate": 950.0,
  "usd_clp_rate_date": "2026-06-30",
  "assumed_output_ratio": 0.25,
  "byo_clients": [],
  "rates": [
    {
      "provider": "groq",
      "model": "llama-3.3-70b-versatile",
      "input_per_million_usd": 0.59,
      "output_per_million_usd": 0.79,
      "effective_date": "2026-01-01"
    },
    {
      "provider": "openai",
      "model": "gpt-4o-mini",
      "input_per_million_usd": 0.15,
      "output_per_million_usd": 0.60,
      "effective_date": "2026-01-01"
    }
  ]
}
```

> Los precios son de ejemplo — verificá los actuales en la página de cada proveedor antes de fijar
> precios reales.

## 2. Aplicar la migración

```bash
alembic upgrade head   # agrega llm_model, input_tokens, output_tokens a query_log
```

## 3. Pedir un reporte

```bash
# Costo del último mes, todos los clientes
curl -s -H "X-API-Key: $API_KEY" "http://localhost:8000/costs?hours=720" | jq

# Un cliente específico, rango explícito
curl -s -H "X-API-Key: $API_KEY" \
  "http://localhost:8000/costs?from=2026-06-01T00:00:00Z&to=2026-06-30T23:59:59Z&client_key=user-42" | jq
```

## 4. Leer el resultado

- `clients[]` ordenado por costo descendente: cuánto te costó cada cliente.
- `total_cost_clp_operator`: lo que **tú** pagas de IA en el período → base para fijar la mantención.
- `total_cost_clp_byo`: costo informativo de clientes que pagan su propia IA (no lo pagas tú).
- `total_savings_clp`: cuánto te ahorró el enmascarado (argumento de venta).
- Banderas a vigilar: `estimated` (cifras aproximadas de datos históricos), `price_missing` (falta
  configurar la tarifa de ese modelo), `rate_stale` (actualizá el tipo de cambio).

## 5. Probar (criterios de aceptación)

```bash
pytest tests/unit/test_cost_service.py tests/integration/test_costs_endpoint.py
```

Las pruebas cubren:
- Cálculo correcto: `cost = tokens × tarifa × tipo de cambio` (margen < 1% con desglose real, SC-002).
- Cambiar un precio en `pricing.json` → el reporte cambia sin redeploy (SC-003).
- La salida no contiene ningún dato personal (SC-004).
- Cuadre de totales (SC-005).
- Período sin actividad → ceros, sin error.
- Cliente BYO marcado como no facturable al operador.
- Consulta con modelo sin tarifa → `price_missing: true`, no costo cero silencioso.
