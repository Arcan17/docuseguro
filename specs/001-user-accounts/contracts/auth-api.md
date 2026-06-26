# API Contracts — Autenticación (Fase 1)

Todos los endpoints de auth aplican el rate limiting existente. Tokens: JWT en
`Authorization: Bearer <token>`.

## POST /auth/register
Crea una cuenta e inicia sesión.
- Body: `{ "email": string, "password": string }`
- 201: `{ "access_token": string, "token_type": "bearer", "email": string }`
- 400: contraseña no cumple el mínimo
- 409: email ya registrado
- 422: email con formato inválido

## POST /auth/login
- Body: `{ "email": string, "password": string }`
- 200: `{ "access_token": string, "token_type": "bearer", "email": string }`
- 401: credenciales inválidas (mensaje genérico — no revela si el email existe)
- 429: demasiados intentos

## GET /auth/me
Devuelve el usuario actual (requiere Bearer).
- 200: `{ "id": int, "email": string }`
- 401: sin token o token inválido

## POST /auth/logout
Stateless: el cliente descarta el token. Responde 204. (Sin invalidación server-side en Fase 1.)

## DELETE /auth/account
Elimina la cuenta del usuario actual y todos sus documentos/derivados (requiere Bearer).
- 204: eliminado
- 401: sin token

## Cambios en endpoints existentes

### POST /ingest
- Ahora acepta opcionalmente el Bearer. Si hay usuario autenticado → el documento se
  asocia a su cuenta (`source=user`, `owner=user:{id}`, **no** expira).
- Si no hay sesión autenticada → comportamiento actual (anónimo, `source=upload`, efímero).
- El campo `session_id` (form) se mantiene para el modo anónimo.

### POST /query
- Si hay Bearer válido → busca en `demo` + documentos del usuario.
- Si no → busca en `demo` + documentos de la sesión anónima (`session_id`), como hoy.
