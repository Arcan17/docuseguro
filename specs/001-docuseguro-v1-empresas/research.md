# Research — DocuSeguro v1 para Empresas

## Decisión 1: Duración y almacenamiento del trial

**Decisión:** 14 días desde `created_at` del usuario. Se calcula al vuelo (`trial_expires_at = created_at + 14 días`), sin tabla separada.

**Rationale:** Evita migración adicional. La fecha de expiración es determinista y no necesita persistirse. Si en el futuro se necesitan trials extendidos manualmente, se agrega un campo `trial_override_expires_at` nullable.

**Campo a agregar en `users`:** ninguno nuevo — se calcula como `user.created_at + timedelta(days=14)`.

---

## Decisión 2: Comportamiento al vencer el trial

**Decisión:** El backend devuelve HTTP 402 en `/ingest` y `/query` cuando el trial venció. El frontend muestra un banner persistente con mensaje de contacto.

**Rationale:** Simple de implementar, no requiere roles ni estados adicionales. El historial sigue accesible (no se borra).

---

## Decisión 3: Endpoints de estadísticas para el panel

**Decisión:** Nuevo endpoint `GET /auth/stats` que devuelve counts desde PostgreSQL (documentos y consultas) y el estado del trial.

**Rationale:** Centraliza la lógica en el backend. El frontend hace una sola llamada al cargar el panel.

---

## Decisión 4: Landing page — enfoque de diseño

**Decisión:** Rediseño completo de `page.tsx`. Secciones: Hero → Cómo funciona (3 pasos) → Por rubro → Demo → CTA registro. Sin jerga técnica.

**Rationale:** La página actual está pensada como demo técnica, no como página de producto. El rediseño mantiene la demo funcional pero la rodea de contexto comercial.

---

## Decisión 5: Panel de usuario — ruta

**Decisión:** Nueva ruta `/dashboard` en Next.js. Accesible solo con sesión activa; redirige a `/` si no hay token.

**Rationale:** Separa la experiencia del usuario autenticado de la landing/demo pública.

---

## Decisión 6: QueryLog — tabla nueva vs. métricas en memoria

**Decisión:** Nueva tabla `query_logs` en PostgreSQL con campos mínimos: `id`, `user_id`, `pii_found`, `created_at`. El texto de la consulta NO se guarda (privacidad).

**Rationale:** Necesario para mostrar historial real en el panel. No guardar el texto protege la privacidad del usuario.

---

## Decisión 7: Orden de despliegue

**Decisión:**
1. Desplegar Fase 1 (cuentas) — rama `001-user-accounts` ya construida
2. Construir y desplegar Fase 2 (trial) sobre main actualizado
3. Construir y desplegar Fase 3 (landing) — puede ir junto con Fase 2
4. Construir y desplegar Fase 4 (panel) — requiere query_logs

**Rationale:** Cada fase es desplegable independientemente. El trial depende de que existan usuarios (Fase 1). El panel depende del logging (Fase 4 va última).
