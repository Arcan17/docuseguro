# Tasks: Cuentas de usuario y autenticación (Fase 1)

**Feature**: specs/001-user-accounts · **Branch**: `001-user-accounts`
**Input**: spec.md, plan.md, data-model.md, contracts/auth-api.md

Formato: `- [ ] [ID] [P?] [Story?] descripción (ruta)`. `[P]` = paralelizable (archivos
distintos, sin dependencias pendientes).

---

## Phase 1: Setup

- [ ] T001 Añadir dependencias de auth a `requirements.txt`: `passlib[bcrypt]`, `PyJWT`, `email-validator` (para `pydantic.EmailStr`)
- [ ] T002 Añadir settings nuevas en `app/core/config.py`: `jwt_secret` (con `effective_jwt_secret` aleatorio si vacío, patrón de `effective_audit_secret`), `jwt_expire_minutes` (default 10080 = 7 días), `password_min_length` (default 8)
- [ ] T003 [P] Documentar las variables nuevas en `.env.example`

## Phase 2: Foundational (bloquea todas las historias)

- [ ] T004 [P] Crear modelo `User` en `app/models/user.py` (id, email único en minúsculas, password_hash, created_at) según data-model.md
- [ ] T005 Registrar el modelo `User` en `app/models/__init__.py` y asegurar que `create_tables` lo crea
- [ ] T006 Añadir columna nullable `user_id` (FK→users) a `Document` en `app/models/document.py`
- [ ] T007 [P] Crear `app/core/security.py`: `hash_password`, `verify_password` (bcrypt vía passlib), `create_access_token` y `decode_access_token` (JWT HS256 con `settings.effective_jwt_secret`)
- [ ] T008 Crear dependencias de auth en `app/api/deps.py`: `get_current_user` (exige Bearer válido → User o 401) y `get_optional_user` (devuelve User o None, sin obligar login)
- [ ] T009 Generalizar el aislamiento en `app/services/vector_store.py`: aceptar `owner` (`user:{id}` | `session:{sid}`) en `upsert_chunks` y filtrar en `search` por `source=="demo" OR owner==caller` (manteniendo el borrado de solo `source=="upload"`)

## Phase 3: User Story 1 — Crear una cuenta (P1)

**Meta**: registrarse con email + contraseña y quedar logueado.
**Test independiente**: registrar email nuevo → recibe token; email repetido → 409.

- [ ] T010 [US1] Crear `app/services/auth_service.py` con `register(email, password)`: valida largo de contraseña, normaliza email, rechaza duplicado, hashea y crea el `User`
- [ ] T011 [US1] Crear schemas en `app/api/schemas/auth.py`: `RegisterRequest` (EmailStr, password), `AuthResponse` (access_token, token_type, email)
- [ ] T012 [US1] Crear `app/api/routers/auth.py` con `POST /auth/register` (201 / 400 / 409 / 422) y rate limiting; incluir el router en `app/main.py`
- [ ] T013 [P] [US1] Crear página de registro `frontend/app/registro/page.tsx` (form email + contraseña, llama a `/auth/register`, guarda el token)

## Phase 4: User Story 2 — Iniciar y cerrar sesión (P1)

**Meta**: login/logout con sesión por token.
**Test independiente**: login correcto entra; incorrecto → 401 genérico; logout deja fuera.

- [ ] T014 [US2] Añadir `authenticate(email, password)` a `app/services/auth_service.py` (verifica hash; falla genérica sin revelar si el email existe)
- [ ] T015 [US2] Añadir a `app/api/routers/auth.py`: `POST /auth/login` (200 / 401 / 429) con rate limiting, `GET /auth/me`, `POST /auth/logout` (204)
- [ ] T016 [P] [US2] Crear `frontend/lib/auth.ts`: guardar/leer/borrar token, helper `getToken()` y estado de sesión
- [ ] T017 [P] [US2] Crear página de login `frontend/app/login/page.tsx`
- [ ] T018 [US2] Barra de sesión en `frontend/app/page.tsx`: mostrar "entrar / registrarse" si anónimo, o email + "cerrar sesión" si logueado

## Phase 5: User Story 3 — Documentos persistentes y privados por cuenta (P1)

**Meta**: los docs de un usuario persisten y solo él los ve; el modo anónimo sigue igual.
**Test independiente**: A sube y vuelve → siguen; B no los ve; demo visible.

- [ ] T019 [US3] En `app/api/routers/ingest.py`: usar `get_optional_user`; si hay usuario → `owner=user:{id}`, `source=user`, `user_id` en Document, sin TTL; si no → comportamiento anónimo actual
- [ ] T020 [US3] En `app/api/routers/query.py`: pasar el `owner` del usuario autenticado (o de la sesión anónima) a `search`
- [ ] T021 [US3] Añadir `DELETE /auth/account` en `app/api/routers/auth.py`: borra el `User`, sus `Document` y sus chunks (`owner==user:{id}`) del vector store
- [ ] T022 [P] [US3] En `frontend/lib/api.ts`: enviar `Authorization: Bearer` cuando haya token, en `ingest` y `query`

## Phase 6: Polish & Cross-Cutting

- [ ] T023 [P] Actualizar `frontend/app/privacidad/page.tsx`: declarar que las cuentas guardan email + documentos de forma persistente hasta que el usuario los elimine (FR-015)
- [ ] T024 [P] Test: registro y login en `tests/test_auth_router.py` (éxito, email duplicado, contraseña corta, login inválido genérico)
- [ ] T025 [P] Test: aislamiento entre cuentas y persistencia en `tests/test_account_isolation.py` (A ve lo suyo, B no; demo visible; doc de cuenta no expira)
- [ ] T026 [P] Test: el modo anónimo sigue funcionando igual en `tests/test_anonymous_mode.py`
- [ ] T027 Verificar `ruff check .` limpio y `pytest` verde antes de mergear

---

## Dependencias

- **Setup (T001-T003)** → antes de todo.
- **Foundational (T004-T009)** → bloquea US1, US2, US3.
- **US1 (T010-T013)** → independiente tras foundational.
- **US2 (T014-T018)** → usa el `User` y security; tras foundational. (T014 depende de T010 por compartir `auth_service.py`.)
- **US3 (T019-T022)** → usa `get_optional_user` (T008) y el `owner` en vector_store (T009).
- **Polish (T023-T027)** → al final.

## Estrategia de entrega (MVP incremental)

- **MVP mínimo demostrable**: Foundational + US1 + US2 (registrarse, entrar, salir). Ya muestra valor.
- **Valor completo**: + US3 (documentos persistentes y privados) → la razón de tener cuentas.
- **Cierre**: Polish (privacidad + tests + lint/CI verde).

## Paralelizables destacados

- T003, T004, T007 pueden ir en paralelo (archivos distintos).
- Frontend (T013, T016, T017) en paralelo con backend de su historia.
- Todos los tests del Polish (T024-T026) en paralelo.
