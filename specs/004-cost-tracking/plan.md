# Implementation Plan: Medidor de Costo de IA por Cliente

**Branch**: `004-cost-tracking` | **Date**: 2026-06-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-cost-tracking/spec.md`

## Summary

Agregar una capa de **costeo** que convierte el consumo de tokens ya registrado en `QueryLog` a
costo monetario (USD y CLP) agrupado por cliente y período, para que el operador decida precios de
mantención. Es backend de solo lectura para el operador, reutilizando la protección de acceso del
endpoint `/metrics`. Los precios por proveedor/modelo y el tipo de cambio USD→CLP viven en un
**archivo de tarifas editable sin redeploy**. Requiere una pequeña extensión de `QueryLog` (modelo
de IA y, opcionalmente, desglose input/output de tokens) con su migración Alembic.

## Technical Context

**Language/Version**: Python 3.11 (backend existente)

**Primary Dependencies**: FastAPI, SQLAlchemy async, Alembic, pydantic-settings (todo ya en el repo)

**Storage**: PostgreSQL (tabla `query_log` existente) + un archivo de tarifas JSON versionado/editable

**Testing**: pytest (suite existente en `tests/`)

**Target Platform**: Linux server (backend FastAPI)

**Project Type**: Web service (backend); el frontend Next.js queda fuera del alcance de esta v1

**Performance Goals**: Un reporte de costo de un período mensual responde en < 2 s para volúmenes de
demo/piloto (miles de filas en `query_log`)

**Constraints**: El reporte NO expone datos personales (solo agregados). Precios y tipo de cambio
editables sin redeploy. Reutiliza la autenticación de operador (`require_api_key`).

**Scale/Scope**: Un operador (Bastián). Volumen actual: bajo (piloto/demo). Diseño debe soportar
crecer a decenas de clientes sin rediseño.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | ¿Aplica? | Cumplimiento en este plan |
|-----------|----------|---------------------------|
| **I. Privacidad Primero** | Sí | El reporte agrega solo conteos de tokens y costos; NO lee ni expone contenido de documentos, RUT, correos ni teléfonos. `query_hash` ya es un hash, no se muestra. ✅ |
| **II. IA con Costo Flexible** | Sí (central) | El medidor calcula costo por proveedor/modelo y marca, por consulta/cliente, si el costo lo paga el operador o el cliente (BYO/on-prem). Es lo que habilita decidir el cobro. ✅ |
| **III. Configurable por Cliente** | Parcial | Las tarifas y el tipo de cambio son configurables (archivo de tarifas). Personalización por tenant plena llega con la organización (spec 002). ✅ |
| **IV. Madurez de Datos por Fase** | Sí | No maneja datos confidenciales; solo métricas de uso. Sin impacto en el tier de datos. ✅ |
| **V. Entrega por Fases** | Sí | Es un incremento aislado que no requiere hosting nuevo ni storage nuevo; corre sobre lo existente. ✅ |
| **VI. Spec-Driven** | Sí | Se sigue el flujo: spec → plan (este) → tasks → implement. ✅ |

**Resultado del gate**: PASA. Sin violaciones que justificar.

## Project Structure

### Documentation (this feature)

```text
specs/004-cost-tracking/
├── plan.md              # Este archivo
├── research.md          # Phase 0 — decisiones técnicas
├── data-model.md        # Phase 1 — modelo de datos y entidades
├── quickstart.md        # Phase 1 — cómo usar/probar la feature
├── contracts/
│   └── cost-report.md   # Phase 1 — contrato del endpoint de reporte de costo
└── tasks.md             # Phase 2 — lo genera /speckit-tasks (no este comando)
```

### Source Code (repository root)

```text
app/
├── api/
│   ├── routers/
│   │   ├── metrics.py          # existe (referencia de patrón + auth)
│   │   └── costs.py            # NUEVO — GET /costs (protegido por require_api_key)
│   └── schemas/
│       ├── metrics.py          # existe
│       └── costs.py            # NUEVO — CostReport, ClientCostRow
├── core/
│   ├── auth.py                 # existe — require_api_key (se reutiliza)
│   └── config.py               # existe — se agrega ruta del archivo de tarifas
├── models/
│   └── query_log.py            # MODIFICAR — agregar llm_model, input_tokens, output_tokens
└── services/
    ├── metrics_service.py      # existe (referencia)
    ├── cost/
    │   ├── __init__.py         # NUEVO
    │   ├── pricing.py          # NUEVO — carga el archivo de tarifas, lookup por proveedor/modelo
    │   └── cost_service.py     # NUEVO — compute_cost_report(db, period, group_by, ...)
    └── ...

config/
└── pricing.json                # NUEVO — tarifas por proveedor/modelo + tipo de cambio + supuestos

alembic/
└── versions/
    └── XXXX_add_cost_fields_to_query_log.py   # NUEVO — migración de los campos nuevos

tests/
├── unit/
│   └── test_cost_service.py    # NUEVO — cálculo de costo, estimación, cuadre de totales
└── integration/
    └── test_costs_endpoint.py  # NUEVO — auth, agrupación, sin PII en la salida
```

**Structure Decision**: Web service de un solo proyecto (backend `app/`). Se sigue el patrón
existente: router delgado → service con la lógica → schema pydantic para la salida. El costeo va en
un subpaquete `app/services/cost/` para separar la carga de tarifas (`pricing.py`) del cálculo
(`cost_service.py`). El frontend no se toca en v1 (el reporte se consume vía endpoint autenticado).

## Complexity Tracking

No hay violaciones de la constitución que justificar. Sin entradas.
