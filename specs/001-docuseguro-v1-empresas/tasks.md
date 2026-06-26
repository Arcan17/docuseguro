# Tareas — DocuSeguro v1 para Empresas

**Feature:** `001-docuseguro-v1-empresas`
**Plan:** [plan.md](plan.md) · **Spec:** [spec.md](spec.md) · **Data model:** [data-model.md](data-model.md)

Las fases mapean a las historias de usuario del spec. Cada fase es desplegable de forma
independiente. `[P]` = paralelizable (archivos distintos, sin dependencias pendientes).

---

## Fase 1 — Desplegar cuentas de usuario (US1) · MVP

**Objetivo:** Registro/login funcionando en producción.
**Test independiente:** Un visitante puede registrarse, cerrar sesión y volver a entrar; `/auth/me` devuelve su usuario.
**Estado del código:** ya construido en rama `001-user-accounts`. Esta fase es despliegue, no desarrollo.

- [ ] T001 [US1] Correr Migración A en Railway PostgreSQL (crear tabla `users`, modificar `documents`) según [data-model.md](data-model.md)
- [ ] T002 [US1] Generar un `JWT_SECRET` aleatorio (64+ chars) y agregarlo como variable de entorno en Railway
- [ ] T003 [US1] Crear PR de `001-user-accounts` → `main` y mergear
- [ ] T004 [US1] Verificar en producción: `POST /auth/register` devuelve token, `POST /auth/login` funciona, `GET /auth/me` devuelve el usuario
- [ ] T005 [US1] Verificar aislamiento: documentos de un usuario no aparecen en consultas de otro

---

## Fase 2 — Trial gratuito de 14 días (US2)

**Objetivo:** Bloquear `/ingest` y `/query` cuando el trial venció.
**Test independiente:** Una cuenta cuyo `created_at` es de hace 15+ días recibe HTTP 402 al subir o consultar; una cuenta nueva funciona normal.
**Depende de:** Fase 1 (necesita usuarios).

### Backend
- [ ] T006 [US2] Crear `app/core/trial.py` con `trial_status(user) -> {active, days_remaining, expires_at}` (14 días desde `created_at`)
- [ ] T007 [US2] En `app/api/routers/ingest.py`: si usuario autenticado y trial vencido, responder HTTP 402 con mensaje de contacto
- [ ] T008 [US2] En `app/api/routers/query.py`: mismo control 402 que ingest
- [ ] T009 [US2] Agregar `GET /auth/stats` en `app/api/routers/auth.py` devolviendo email, trial_active, trial_days_remaining, trial_expires_at, documents_count (queries_count y pii_events_count se completan en Fase 4)
- [ ] T010 [P] [US2] Agregar schema `StatsResponse` en `app/api/schemas/auth.py`

### Frontend
- [ ] T011 [US2] En `frontend/lib/auth.ts`: agregar `getStats()` que llama a `/auth/stats` con el Bearer token
- [ ] T012 [US2] En la barra de sesión del usuario autenticado: mostrar "Te quedan N días de prueba" (nota: tras T015 la barra de sesión vive en `frontend/app/app/page.tsx`)
- [ ] T013 [US2] Mostrar banner de trial vencido con link `mailto:bast-1996@hotmail.com` cuando el backend responda 402

### Verificación
- [ ] T014 [US2] Probar con cuenta cuyo trial expiró: confirmar 402 en ingest/query y que el historial sigue visible

---

## Fase 3 — Landing page profesional (US3)

**Objetivo:** Página de inicio que convierta visitantes en registros.
**Test independiente:** Una persona del rubro objetivo entiende qué es DocuSeguro en <30s y encuentra el CTA de registro sin ayuda.
**Depende de:** Fase 1 (el CTA lleva al registro). Puede construirse en paralelo a Fase 2.

### Reorganización de rutas
- [ ] T015 [US3] Mover la demo actual de `frontend/app/page.tsx` a nueva ruta `frontend/app/app/page.tsx`
- [ ] T016 [P] [US3] Crear `frontend/app/register/page.tsx` (formulario de registro → `/auth/register` → guarda sesión → redirige a `/app`)
- [ ] T017 [P] [US3] Crear `frontend/app/login/page.tsx` (formulario de login → `/auth/login` → guarda sesión → redirige a `/app`)

### Nueva landing
- [ ] T018 [US3] Reescribir `frontend/app/page.tsx` como landing: Hero con CTA "Empieza gratis — 14 días sin tarjeta"
- [ ] T019 [US3] Sección "Cómo funciona" en 3 pasos (subes documento → preguntas → respuesta con datos protegidos)
- [ ] T020 [P] [US3] Sección "Por rubro" con abogados / contadores / seguros y ejemplos de documentos de cada uno
- [ ] T021 [P] [US3] Sección demo con botón "Pruébalo sin registrarte" → `/app`
- [ ] T021b [US3] En `/app`: tras la primera consulta de un visitante anónimo, mostrar un aviso invitando a registrarse para guardar su historial (cubre Escenario 3 del spec)
- [ ] T022 [US3] CTA final + footer con links a /privacidad, /terminos y contacto
- [ ] T023 [US3] Revisar todo el texto: sin jerga técnica (sin RAG, embeddings, LLM, ChromaDB)

### Verificación
- [ ] T024 [US3] Verificar en preview: el CTA principal lleva a `/register`, la demo sigue funcionando en `/app`, responsive en móvil

---

## Fase 4 — Panel del usuario (US4)

**Objetivo:** Dashboard que muestre valor recibido y estado del trial.
**Test independiente:** Un usuario con sesión ve sus contadores reales (documentos, consultas, PII protegida) y días restantes; sin sesión es redirigido a login.
**Depende de:** Fase 2 (`/auth/stats`) y la tabla `query_logs`.

### Backend
- [ ] T025 [US4] Correr Migración B en Railway: crear tabla `query_logs` según [data-model.md](data-model.md)
- [ ] T026 [US4] Crear `app/models/query_log.py` (modelo SQLAlchemy de `query_logs`)
- [ ] T027 [US4] En `app/api/routers/query.py`: registrar cada consulta exitosa en `query_logs` (sin guardar el texto, solo pii_found y pii_types)
- [ ] T028 [US4] Completar `GET /auth/stats` con `queries_count` y `pii_events_count` desde `query_logs`

### Frontend
- [ ] T029 [US4] Crear `frontend/app/dashboard/page.tsx` con tarjetas: días de trial, documentos subidos, consultas, conteo de eventos PII protegidos (mostrar el número total; el desglose por tipo —RUT, correo, teléfono— queda para una iteración futura)
- [ ] T030 [US4] Redirigir a `/login` si no hay sesión activa al entrar a `/dashboard`
- [ ] T031 [P] [US4] Botón "Eliminar cuenta" (con confirmación) → `DELETE /auth/account` → limpia sesión → redirige a `/`
- [ ] T032 [US4] Link al dashboard desde la barra de sesión cuando el usuario está autenticado

### Verificación
- [ ] T033 [US4] Verificar que los contadores coinciden con la actividad real del usuario

---

## Fase 5 — Pulido y transversal

- [ ] T034 [P] Actualizar `frontend/app/privacidad/page.tsx` si el flujo de cuentas cambió el tratamiento de datos
- [ ] T035 [P] Revisar que los tests existentes (`tests/`) siguen pasando tras los cambios de trial y logging
- [ ] T036 Revisar manualmente el flujo completo: landing → registro → subir documento → consultar → ver dashboard → trial

---

## Dependencias entre fases

```
Fase 1 (US1) ──┬──> Fase 2 (US2) ──┐
               │                    ├──> Fase 4 (US4)
               └──> Fase 3 (US3) ───┘
                                    └──> Fase 5 (pulido)
```

- **Fase 1** es prerequisito de todo (sin usuarios no hay trial, panel ni CTA real).
- **Fase 2 y 3** se pueden construir en paralelo (no comparten archivos críticos).
- **Fase 4** necesita el endpoint de stats (Fase 2) y la tabla query_logs.
- **Fase 5** al final.

---

## Estrategia de entrega (MVP primero)

| Hito | Fases | Qué se logra |
|------|-------|--------------|
| **MVP** | Fase 1 | Usuarios pueden registrarse y guardar su historial |
| **Vendible** | + Fase 2 + Fase 3 | Landing profesional + trial → se puede ofrecer a empresas |
| **Completo** | + Fase 4 | Panel con el valor visible para el usuario |

**Recomendación:** desplegar Fase 1 ya (solo requiere migración + JWT_SECRET + merge). Luego
Fase 3 (landing) es la de mayor impacto comercial; Fase 2 (trial) la acompaña. Fase 4 cierra.

---

## Oportunidades de paralelización

- Dentro de Fase 2: T010 (schema) en paralelo a T006–T009.
- Dentro de Fase 3: T016, T017 (register/login) y T020, T021 (secciones) en paralelo.
- Fase 2 completa y Fase 3 completa pueden avanzar simultáneamente con dos focos de trabajo.
