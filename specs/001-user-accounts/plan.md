# Implementation Plan: Cuentas de usuario y autenticación (Fase 1)

**Feature**: specs/001-user-accounts · **Branch**: `001-user-accounts` · **Date**: 2026-06-23

## Summary

Agregar cuentas persistentes con autenticación email + contraseña a PrivRAG, sin
romper el modo demo anónimo actual. Un usuario autenticado puede subir documentos
que quedan asociados a su cuenta (no se auto-eliminan) y que solo él puede consultar,
además de los documentos de demostración compartidos. Se reutiliza la infraestructura
ya construida (aislamiento por `owner` en ChromaDB, rate limiting, CORS, PII scrubbing).

## Technical Context

**Language/Version**: Python 3.11 (backend) · TypeScript / Next.js 14 (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async, PostgreSQL, ChromaDB; añadir: passlib[bcrypt] (hashing), PyJWT (tokens), pydantic EmailStr
**Storage**: PostgreSQL (cuentas, documentos), ChromaDB (vectores, ya con metadata de owner)
**Testing**: pytest (backend), build de Next.js (frontend)
**Target Platform**: Web (API en Railway, frontend en Vercel)
**Project Type**: Web application (backend + frontend)
**Constraints**: contraseñas hasheadas (nunca texto plano); login no revela si el email existe; convivencia anónimo + autenticado; compatibilidad con rate limiting / CORS / aviso de privacidad
**Scale/Scope**: decenas–cientos de usuarios iniciales (demo/early); 1 instancia

## Constitution Check

No existe `constitution.md` en el proyecto. Se siguen las convenciones ya presentes:
capas limpias (routers / services / models), SQLAlchemy async, tests con pytest,
sin secretos en el repo, y las garantías de privacidad ya documentadas.
**Gate: PASS** (sin violaciones; ningún principio formal que incumplir).

## Decisiones técnicas clave (ver research.md)

1. **Hashing de contraseñas:** `bcrypt` vía passlib. Estándar, lento a propósito (anti fuerza bruta).
2. **Sesión:** **JWT** (token firmado HS256) en el header `Authorization: Bearer`. Stateless → no requiere tabla de sesiones. `logout` = el cliente descarta el token. Secreto de firma desde env con fallback aleatorio por proceso (mismo patrón que `effective_audit_secret`).
3. **Owner de un documento:** se generaliza el aislamiento actual. La metadata de cada chunk lleva `owner` = `user:{id}` (autenticado) o `session:{sid}` (anónimo), más `source` (`demo` | `user` | `upload`). La búsqueda devuelve `source=demo` OR `owner == caller`.
4. **Retención:** el job de limpieza solo borra `source=upload` (anónimo). Los `source=user` (autenticados) **no** expiran → persisten.
5. **Token en el frontend:** se guarda en `localStorage` y se envía como Bearer. (Hardening futuro: cookie httpOnly; se anota, no se hace en Fase 1.)

## Project Structure

### Documentation (this feature)
```
specs/001-user-accounts/
├── spec.md
├── plan.md            # este archivo
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── auth-api.md
```

### Source Code (cambios)
```
app/
├── models/
│   └── user.py                # NUEVO: tabla User
│   └── document.py            # +columna user_id (nullable)
├── core/
│   ├── security.py            # NUEVO: hash/verify password, crear/validar JWT
│   └── config.py              # +jwt_secret, +jwt_expire_minutes, +password_min_length
├── api/
│   ├── routers/auth.py        # NUEVO: register, login, logout, me, delete account
│   ├── deps.py                # +get_current_user / +get_optional_user
│   ├── routers/ingest.py      # owner = usuario si autenticado, si no session
│   └── routers/query.py       # idem
├── services/
│   ├── vector_store.py        # search/upsert por `owner` (generaliza session_id)
│   └── auth_service.py        # NUEVO: lógica de registro/login
└── main.py                    # incluir router auth

frontend/app/
├── login/page.tsx             # NUEVO
├── registro/page.tsx          # NUEVO
├── lib/auth.ts                # NUEVO: guardar/leer token, estado de sesión
├── lib/api.ts                 # enviar Bearer; endpoints auth
└── page.tsx                   # barra de sesión (entrar / registrarse / cerrar sesión)
```

## Implementation Phases (alto nivel)

- **A. Modelo + seguridad (backend):** tabla User, columna `user_id` en Document, `core/security.py` (hash + JWT), config nueva.
- **B. Endpoints de auth:** `/auth/register`, `/auth/login`, `/auth/me`, `/auth/logout`, `DELETE /auth/account`, con rate limiting en register/login.
- **C. Integración de aislamiento:** generalizar `vector_store` y los routers ingest/query para usar `owner` (usuario o sesión). El cleanup sigue borrando solo lo anónimo.
- **D. Frontend:** páginas login/registro, manejo de token, barra de sesión, envío de Bearer.
- **E. Privacidad + tests:** actualizar aviso de privacidad (cuentas guardan email+docs persistentes); tests de registro, login, aislamiento entre cuentas, persistencia, y que el modo anónimo siga igual.

## Riesgos y mitigaciones

- **Migración de datos:** se agrega `user_id` nullable → no rompe documentos existentes ni el modo anónimo. La tabla se crea con `create_tables` (ya en uso).
- **Romper el flujo anónimo:** `get_optional_user` permite que ingest/query funcionen con o sin cuenta. Tests lo cubren.
- **Seguridad del token en localStorage (XSS):** aceptable para Fase 1; anotado como hardening (cookie httpOnly) para una fase futura.

## Post-Design Constitution Re-check
**PASS** — sin nuevas violaciones; el diseño mantiene capas limpias y las garantías de privacidad.
