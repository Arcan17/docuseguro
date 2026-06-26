# Revisión de seguridad — Cuentas / Auth (Fase 1)

> Revisor de riesgos, NO asesoría legal. Confirma los puntos marcados con un abogado
> antes de producción. Vuelve a revisar contra el código tras cualquier corrección.

## Revisión 2026-06-24 (rama `001-user-accounts`)

### 🚦 ¿Puedo desplegar las cuentas?
🟡 **SÍ, pero con cuidado.** 0 bloqueantes, ningún agujero que filtre datos. 1 cosa
obligatoria antes de desplegar (fijar JWT_SECRET) y varias mejoras antes de datos reales.

### ✅ Lo que ya está bien
- Contraseñas con bcrypt (cifradas, con sal). `app/core/security.py`
- Tokens JWT firmados; secreto aleatorio si no se configura (sin default adivinable). `app/core/config.py`
- Login genérico — no revela si el correo existe. `app/api/routers/auth.py`
- Límite de intentos en registro/login.
- Aislamiento entre cuentas (probado con tests).
- Eliminar cuenta borra documentos y vectores.

### 🟡 Hallazgos (Media — ninguno bloquea)
1. **Fijar `JWT_SECRET` en producción** (si no, las sesiones se rompen en cada deploy). Lo más urgente. `app/core/config.py` — variable lista; falta ponerla en Railway al desplegar (acción operativa).
2. **Token en localStorage (XSS)** → migrar a cookie httpOnly antes de datos reales. `frontend/lib/auth.ts` — **⚠️ Sigue (pendiente).**
3. ~~Sin revocación de sesión~~ → ✅ **Mitigado:** token acortado de 7 días a 1 día. `app/core/config.py` (jwt_expire_minutes=1440). (Revocación total sigue siendo mejora futura.)
4. ~~Límite solo por IP~~ → ✅ **Resuelto:** bloqueo por cuenta tras 5 intentos fallidos (5 min). `app/core/login_guard.py` + test.

### 🟢 Menores
5. Sin verificación de correo (alguien puede registrar un email ajeno). Baja.
6. Contraseña solo exige largo 8 (sin complejidad). Baja.

### Resumen
- Seguro para demo / early users con datos NO confidenciales.
- Para datos legales reales: cerrar #2/#3/#4 + recordar que el texto anonimizado igual
  va a Groq → la versión para datos reales es **on-premise** (Fase 3).
