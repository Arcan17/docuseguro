# Data Model — Cuentas de usuario (Fase 1)

## Entidad: User (nueva tabla `users`)

| Campo          | Tipo                | Reglas |
|----------------|---------------------|--------|
| id             | int (PK)            | autoincremental |
| email          | str (único)         | formato email válido; case-insensitive (guardar en minúsculas) |
| password_hash  | str                 | bcrypt; nunca texto plano |
| created_at     | datetime (tz)       | default ahora |

Relaciones: un `User` tiene 0..N `Document`.

## Entidad: Document (tabla existente — cambio)

Se agrega:

| Campo    | Tipo            | Reglas |
|----------|-----------------|--------|
| user_id  | int (FK→users)  | **nullable** — null = documento anónimo (modo demo) |

No se rompe nada existente: los documentos actuales quedan con `user_id = null`.

## Vector store (ChromaDB) — metadata por chunk

Generaliza el aislamiento actual. Cada chunk lleva:

| Metadata    | Valores | Significado |
|-------------|---------|-------------|
| source      | `demo` \| `user` \| `upload` | demo = compartido; user = de una cuenta; upload = anónimo efímero |
| owner       | `user:{id}` \| `session:{sid}` \| (ausente en demo) | dueño del chunk |
| uploaded_at | epoch   | solo para `upload` (anónimo) — usado por el borrado automático |

**Regla de búsqueda:** devolver chunks donde `source == demo` OR `owner == caller`,
donde `caller` = `user:{id}` si hay sesión autenticada, o `session:{sid}` si es anónimo.

**Regla de borrado automático:** solo elimina `source == upload` antiguos. Los
`source == user` (de cuentas) **no** expiran.

## Estados / transiciones

- Documento anónimo (`upload`) → se borra solo tras TTL (como hoy).
- Documento de cuenta (`user`) → persiste hasta que el usuario lo borre o elimine su cuenta.
- Eliminar cuenta → se borran sus `Document` y sus chunks (`owner == user:{id}`).
