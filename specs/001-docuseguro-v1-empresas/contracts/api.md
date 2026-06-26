# Contratos de API — DocuSeguro v1 para Empresas

## Endpoints existentes (sin cambios)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | /auth/register | No | Registro. Devuelve token + email |
| POST | /auth/login | No | Login. Devuelve token + email |
| GET | /auth/me | Bearer | Datos del usuario actual |
| POST | /auth/logout | Bearer | Logout (stateless, 204) |
| DELETE | /auth/account | Bearer | Elimina cuenta + documentos + chunks |
| POST | /ingest | Opcional | Sube documento |
| POST | /query | Opcional | Consulta sobre documentos |
| GET | /health | No | Estado del servicio |

---

## Endpoints nuevos

### GET /auth/stats
Devuelve estadísticas del usuario y estado del trial.

**Auth:** Bearer (requerido)

**Response 200:**
```json
{
  "email": "usuario@empresa.cl",
  "trial_active": true,
  "trial_days_remaining": 11,
  "trial_expires_at": "2026-07-09T14:32:00Z",
  "documents_count": 4,
  "queries_count": 17,
  "pii_events_count": 9
}
```

**Response 401:** Token inválido o ausente

---

## Cambios en endpoints existentes

### POST /ingest — nuevo comportamiento con trial vencido
Si el usuario está autenticado Y su trial venció:
```json
HTTP 402 Payment Required
{
  "detail": "Tu período de prueba ha vencido. Escribe a bast-1996@hotmail.com para continuar."
}
```

### POST /query — nuevo comportamiento con trial vencido
Igual que /ingest: HTTP 402 si trial vencido y usuario autenticado.

**Nota:** Usuarios anónimos (sin token) no están sujetos al trial — pueden seguir usando la demo.

---

## Páginas frontend nuevas/modificadas

| Ruta | Tipo | Descripción |
|------|------|-------------|
| `/` | Modificada | Landing page profesional (reemplaza demo actual) |
| `/app` | Nueva | Demo / app principal (se mueve desde `/`) |
| `/dashboard` | Nueva | Panel del usuario (requiere sesión) |
| `/privacidad` | Sin cambios | Aviso de privacidad |
| `/terminos` | Sin cambios | Términos y condiciones |
