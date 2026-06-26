# Modelo de datos — DocuSeguro v1 para Empresas

## Entidades existentes (sin cambios)

### users *(ya existe en 001-user-accounts)*
| Campo | Tipo | Notas |
|-------|------|-------|
| id | INTEGER PK | auto-increment |
| email | VARCHAR(320) | unique, indexed |
| password_hash | VARCHAR(255) | bcrypt |
| created_at | TIMESTAMPTZ | server default NOW() |

**Trial calculado:** `trial_expires_at = created_at + 14 días` (no se persiste)

### documents *(ya existe, modificado en 001-user-accounts)*
| Campo | Tipo | Notas |
|-------|------|-------|
| id | INTEGER PK | |
| user_id | INTEGER FK | nullable → users.id ON DELETE CASCADE |
| filename | VARCHAR | |
| content_hash | VARCHAR | único por owner |
| chunk_count | INTEGER | |
| created_at | TIMESTAMPTZ | |

---

## Entidades nuevas (Fases 2 y 4)

### query_logs *(nueva — Fase 4)*
| Campo | Tipo | Notas |
|-------|------|-------|
| id | INTEGER PK | auto-increment |
| user_id | INTEGER FK | nullable → users.id ON DELETE CASCADE |
| session_id | VARCHAR | para usuarios anónimos |
| pii_found | BOOLEAN | ¿se detectó PII en la consulta? |
| pii_types | VARCHAR[] | ej: ["rut", "email"] |
| created_at | TIMESTAMPTZ | server default NOW() |

**Nota de privacidad:** El texto de la consulta NO se guarda.

---

## Migraciones necesarias

### Migración A — Fase 1 (ya documentada en specs/001-user-accounts/MIGRATION.md)
```sql
-- Crear tabla users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(320) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);

-- Modificar documents
ALTER TABLE documents ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS ix_documents_user_id ON documents(user_id);
ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_content_hash_key;
```

### Migración B — Fase 4 (query_logs)
```sql
CREATE TABLE IF NOT EXISTS query_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(64),
    pii_found BOOLEAN NOT NULL DEFAULT FALSE,
    pii_types TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_query_logs_user_id ON query_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_query_logs_created_at ON query_logs(created_at);
```

---

## Estado del trial — lógica

```
trial_active = NOW() < (user.created_at + 14 días)
days_remaining = max(0, (user.created_at + 14 días - NOW()).days)
```

Si `trial_active = False` → backend responde 402 en /ingest y /query para usuarios autenticados.
Usuarios anónimos no tienen trial (usan la demo sin límite de días pero sin persistencia).
