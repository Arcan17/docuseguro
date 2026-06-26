# Plan técnico — DocuSeguro v1 para Empresas

## Stack actual
- **Backend:** FastAPI en Railway (Python)
- **Frontend:** Next.js en Vercel (TypeScript)
- **Base de datos:** PostgreSQL en Railway
- **Vector store:** ChromaDB (Railway)
- **Embeddings:** fastembed local (BAAI/bge-small-en-v1.5)
- **LLM:** Groq (openai/gpt-oss-20b)

---

## Fase 1 — Desplegar cuentas de usuario *(rama 001-user-accounts, ya construida)*

**Objetivo:** Tener registro/login funcionando en producción.

**Pasos:**
1. Correr Migración A en Railway PostgreSQL (ver data-model.md)
2. Agregar variable `JWT_SECRET` en Railway (string aleatorio seguro, 64+ chars)
3. Hacer PR de `001-user-accounts` → `main` y mergear
4. Verificar: registro → login → `/auth/me` responde con el usuario

**Archivos involucrados (ya escritos):**
- `app/models/user.py`
- `app/api/routers/auth.py`
- `app/api/deps.py`
- `app/core/security.py`, `login_guard.py`
- `frontend/lib/auth.ts`, `frontend/app/page.tsx` (barra de sesión)

---

## Fase 2 — Trial gratuito de 14 días

**Objetivo:** Bloquear /ingest y /query a usuarios con trial vencido.

**Backend — cambios:**
- `app/core/trial.py` (nuevo): función `trial_status(user) → {active, days_remaining, expires_at}`
- `app/api/routers/ingest.py`: si usuario autenticado y trial vencido → HTTP 402
- `app/api/routers/query.py`: mismo control
- `app/api/routers/auth.py`: nuevo endpoint `GET /auth/stats`

**Frontend — cambios:**
- `frontend/lib/auth.ts`: agregar `getStats()` que llama a `/auth/stats`
- `frontend/app/page.tsx`: mostrar días restantes en la barra de sesión
- `frontend/app/app/page.tsx` (app principal, después de mover demo): banner de trial vencido con link de contacto

**Migración:** ninguna (trial calculado desde `created_at`)

---

## Fase 3 — Landing page profesional

**Objetivo:** Página de inicio que convierta visitantes en usuarios registrados.

**Estructura de la nueva `/`:**

```
Hero
  Título: "Consulta tus documentos con IA. Sin exponer datos privados."
  Subtítulo: breve, orientado al problema
  CTA: "Empieza gratis — 14 días sin tarjeta"
  Visual: animación o mockup simple del flujo

Cómo funciona (3 pasos)
  1. Subes el documento
  2. Haces tu pregunta
  3. La app responde — con los datos sensibles protegidos

Por rubro (3 columnas o tabs)
  Abogados: contratos, escrituras, poderes
  Contadores: balances, declaraciones, facturas
  Seguros: pólizas, siniestros, liquidaciones

Demo (la app actual, integrada o en /app)
  "Pruébalo ahora sin registrarte"

CTA final
  "¿Listo para usarlo con tus propios documentos?"
  Botón → /register

Footer
  Links: Privacidad · Términos · contacto
```

**Principios de diseño:**
- Sin jerga técnica (no mencionar RAG, embeddings, ChromaDB, LLM)
- Tipografía bold, espaciado generoso, paleta oscura (mantener identidad actual)
- Secciones por rubro con íconos o ilustraciones simples, no genéricas
- El CTA principal es registro, no la demo

**Archivos:**
- `frontend/app/page.tsx` → reemplazar completamente con landing
- `frontend/app/app/page.tsx` → nueva ruta, contiene la demo actual
- `frontend/app/register/page.tsx` → nueva página de registro
- `frontend/app/login/page.tsx` → nueva página de login

---

## Fase 4 — Panel del usuario

**Objetivo:** Dashboard que muestre el valor recibido y el estado del trial.

**Backend:**
- Migración B: crear tabla `query_logs` (ver data-model.md)
- `app/models/query_log.py` (nuevo): modelo SQLAlchemy
- `app/api/routers/query.py`: registrar en `query_logs` después de cada consulta exitosa
- `GET /auth/stats`: incluir `queries_count` y `pii_events_count` desde query_logs

**Frontend:**
- `frontend/app/dashboard/page.tsx` (nuevo): panel con:
  - Tarjeta: días de trial restantes (o "Trial vencido")
  - Tarjeta: documentos subidos
  - Tarjeta: consultas realizadas
  - Tarjeta: eventos PII protegidos
  - Botón: eliminar cuenta
- Redirige a `/login` si no hay sesión activa

---

## Orden de implementación recomendado

```
Fase 1 (desplegar) → Fase 2 (trial) + Fase 3 (landing) en paralelo → Fase 4 (panel)
```

Fase 2 y 3 pueden construirse simultáneamente porque no comparten archivos críticos.
Fase 4 depende del endpoint `/auth/stats` (Fase 2) y de la tabla `query_logs`.

---

## Variables de entorno necesarias en Railway

| Variable | Descripción | Estado |
|----------|-------------|--------|
| `JWT_SECRET` | Secreto para firmar tokens JWT | **Falta agregar** |
| `DATABASE_URL` | PostgreSQL connection string | Ya existe |
| `GROQ_API_KEY` | API key de Groq | Ya existe |

---

## Checklist de despliegue por fase

### Fase 1
- [ ] Correr Migración A en Railway
- [ ] Agregar JWT_SECRET en Railway env vars
- [ ] PR 001-user-accounts → main + merge
- [ ] Verificar /auth/register y /auth/login en producción

### Fase 2
- [ ] Implementar `app/core/trial.py`
- [ ] Agregar control 402 en /ingest y /query
- [ ] Implementar GET /auth/stats
- [ ] Frontend: mostrar días restantes
- [ ] Probar con cuenta de prueba que expire

### Fase 3
- [ ] Diseñar wireframe de landing antes de codear
- [ ] Mover demo actual a /app
- [ ] Implementar nueva landing en /
- [ ] Crear páginas /register y /login
- [ ] Verificar que el CTA lleva al registro

### Fase 4
- [ ] Correr Migración B (query_logs)
- [ ] Registrar queries en la tabla
- [ ] Implementar /dashboard
- [ ] Verificar que los contadores son correctos
