# Research — Decisiones técnicas (Fase 1)

## 1. Hashing de contraseñas
- **Decisión:** bcrypt (vía passlib).
- **Rationale:** estándar de la industria, lento a propósito (resiste fuerza bruta), salt incorporado.
- **Alternativas:** argon2 (más moderno, pero passlib+bcrypt es suficiente y simple); SHA plano (descartado: inseguro).

## 2. Mecanismo de sesión
- **Decisión:** JWT firmado (HS256) en header Bearer.
- **Rationale:** stateless → no requiere tabla de sesiones ni cambios de infra; encaja con API + frontend separados (Vercel↔Railway). Logout = descartar token en el cliente.
- **Alternativas:** sesión en DB con token opaco (permite invalidación real, pero más complejo; se evalúa si se necesita revocación en una fase futura). Cookie httpOnly (más segura contra XSS, pero requiere SameSite=None/Secure + CORS con credenciales entre dominios; anotado como hardening futuro).

## 3. Convivencia anónimo + autenticado
- **Decisión:** generalizar el aislamiento por `owner` (user o session) en la metadata del vector store. Dependencia `get_optional_user` que no obliga login.
- **Rationale:** mantiene el gancho "probar sin registro" intacto y reusa el aislamiento ya construido y verificado.

## 4. Persistencia vs borrado
- **Decisión:** el cleanup automático sigue tocando solo `source=upload` (anónimo). Lo de cuentas (`source=user`) no expira.
- **Rationale:** cumple "documentos de cuenta persisten" sin tocar la lógica de borrado anónimo ya probada.
