# Migración de base de datos — antes de desplegar la Fase 1

`create_tables()` usa `create_all`, que **crea tablas nuevas pero NO altera tablas
existentes**. En una base de datos vacía (tests, dev nuevo) todo se crea bien. Pero la
base de **producción** (Railway, PostgreSQL persistente) ya tiene la tabla `documents`,
así que requiere estos cambios manuales **antes** de desplegar:

```sql
-- 1. Tabla de cuentas (create_all la crea sola, pero por claridad):
--    se crea automáticamente al arrancar; no requiere acción manual.

-- 2. Agregar la columna user_id a documents (create_all NO la agrega):
ALTER TABLE documents ADD COLUMN IF NOT EXISTS user_id INTEGER
  REFERENCES users(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS ix_documents_user_id ON documents(user_id);

-- 3. Quitar el unique global de content_hash (ahora la dedup es por dueño).
--    El nombre del constraint puede variar; verifícalo con \d documents.
ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_content_hash_key;
```

**Recomendado:** generar una migración Alembic (ya está en `requirements.txt`) en lugar
de SQL manual, para dejar el cambio versionado:

```bash
alembic revision --autogenerate -m "fase1 cuentas: users + documents.user_id"
alembic upgrade head
```

> Nota: como ChromaDB es efímero en Railway, los vectores se re-siembran solos; solo
> la base relacional necesita esta migración.
