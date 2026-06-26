# Feature Specification: Cuentas de usuario y autenticación (Fase 1)

**Feature Branch**: `001-user-accounts`
**Created**: 2026-06-23
**Status**: Draft
**Input**: User description: "Fase 1 de PrivRAG — cuentas de usuario y autenticación con email + contraseña, para que los documentos subidos queden asociados a una cuenta persistente y aislados por usuario, manteniendo el modo demo anónimo."

## User Scenarios & Testing *(mandatory)*

PrivRAG hoy solo tiene un "modo demo anónimo": cualquiera sube documentos que se aíslan por una sesión temporal del navegador y se borran solos. Esta fase agrega **cuentas persistentes** para usuarios que quieran volver y conservar sus documentos, sin perder el modo demo que sirve de gancho.

### User Story 1 - Crear una cuenta (Priority: P1)

Una persona que probó la demo quiere conservar sus documentos para volver más tarde, así que crea una cuenta con su email y una contraseña.

**Why this priority**: sin registro no existen cuentas; es el cimiento de todo lo demás. Entrega valor por sí sola: el usuario obtiene una identidad persistente.

**Independent Test**: registrarse con un email y contraseña nuevos y confirmar que la cuenta queda creada y se inicia sesión.

**Acceptance Scenarios**:

1. **Given** un email no registrado, **When** el usuario se registra con email + contraseña válida, **Then** la cuenta se crea y queda con sesión iniciada.
2. **Given** un email ya registrado, **When** alguien intenta registrarse con ese mismo email, **Then** el sistema lo rechaza con un mensaje claro y no crea una cuenta duplicada.
3. **Given** una contraseña que no cumple el mínimo de seguridad, **When** el usuario intenta registrarse, **Then** el sistema lo rechaza e indica el requisito.

### User Story 2 - Iniciar y cerrar sesión (Priority: P1)

Un usuario que ya tiene cuenta vuelve a la app, inicia sesión con su email y contraseña, usa la app y luego cierra sesión.

**Why this priority**: una cuenta sin login no sirve. Es parte indivisible del cimiento.

**Independent Test**: con una cuenta existente, iniciar sesión con credenciales correctas (entra) e incorrectas (lo rechaza), y luego cerrar sesión (queda fuera).

**Acceptance Scenarios**:

1. **Given** una cuenta existente, **When** el usuario inicia sesión con credenciales correctas, **Then** accede a su espacio.
2. **Given** una cuenta existente, **When** ingresa una contraseña incorrecta, **Then** el sistema lo rechaza sin revelar si el email existe o no.
3. **Given** una sesión iniciada, **When** el usuario cierra sesión, **Then** deja de tener acceso a su espacio y debe volver a iniciar sesión.
4. **Given** muchos intentos fallidos de login seguidos, **When** se supera un umbral razonable, **Then** el sistema limita temporalmente nuevos intentos.

### User Story 3 - Documentos persistentes y privados por cuenta (Priority: P1)

Un usuario con sesión iniciada sube documentos y los consulta; al volver otro día e iniciar sesión, sus documentos siguen ahí; y ningún otro usuario puede consultarlos.

**Why this priority**: es la razón de tener cuentas. Convierte la demo efímera en una herramienta que se puede usar de verdad.

**Independent Test**: con el usuario A logueado, subir un documento y consultarlo; cerrar sesión, volver a entrar y confirmar que sigue disponible; con el usuario B, confirmar que no puede verlo.

**Acceptance Scenarios**:

1. **Given** un usuario con sesión iniciada, **When** sube un documento, **Then** queda asociado a su cuenta y NO se elimina automáticamente.
2. **Given** un usuario que vuelve e inicia sesión, **When** consulta, **Then** puede acceder a los documentos que subió antes.
3. **Given** dos usuarios distintos, **When** el usuario B consulta, **Then** solo ve sus propios documentos y los documentos de demostración compartidos — nunca los del usuario A.
4. **Given** un visitante sin cuenta (modo demo), **When** sube y consulta, **Then** mantiene el comportamiento actual: aislado por sesión y borrado automático.

### Edge Cases

- Email con formato inválido → rechazo claro al registrar.
- Sesión expirada o token inválido → se pide iniciar sesión de nuevo, sin exponer datos.
- Un usuario elimina su cuenta → sus documentos y derivados se eliminan también (ver FR-012).
- Olvido de contraseña → fuera de alcance en Fase 1; se informa al usuario que no hay recuperación todavía.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir registrar una cuenta con un email único y una contraseña.
- **FR-002**: El sistema MUST almacenar la contraseña de forma segura (con hashing), nunca en texto plano.
- **FR-003**: El sistema MUST rechazar el registro si el email ya está en uso.
- **FR-004**: El sistema MUST exigir una contraseña con un mínimo de seguridad (largo mínimo).
- **FR-005**: El sistema MUST permitir iniciar sesión con email + contraseña y obtener una sesión autenticada.
- **FR-006**: El sistema MUST permitir cerrar sesión, invalidando el acceso.
- **FR-007**: El sistema MUST responder a credenciales inválidas sin revelar si el email existe.
- **FR-008**: El sistema MUST limitar los intentos de login para mitigar ataques de fuerza bruta.
- **FR-009**: El sistema MUST asociar los documentos subidos por un usuario autenticado a su cuenta y NO eliminarlos automáticamente.
- **FR-010**: El sistema MUST aislar el acceso: un usuario solo puede consultar sus propios documentos más los documentos de demostración compartidos.
- **FR-011**: El sistema MUST conservar el modo demo anónimo actual (sin cuenta), con su aislamiento por sesión y borrado automático.
- **FR-012**: El sistema MUST permitir al usuario eliminar su cuenta, borrando sus documentos y derivados asociados.
- **FR-013**: El frontend MUST ofrecer pantallas de registro, inicio de sesión y un indicador de sesión iniciada (incluido cerrar sesión).
- **FR-014**: El sistema MUST mantener compatibilidad con lo ya construido (límite de uso, CORS, eliminación de datos personales antes de la IA, aviso de privacidad y términos).
- **FR-015**: El aviso de privacidad MUST reflejar que las cuentas guardan email y documentos de forma persistente hasta que el usuario los elimine.

### Key Entities *(include if feature involves data)*

- **Usuario (Cuenta)**: identifica a una persona registrada. Atributos clave: email (único), contraseña protegida, fecha de creación. Se relaciona con sus documentos.
- **Documento**: archivo subido. En Fase 1 puede pertenecer a una cuenta (persistente) o a una sesión anónima (efímero, como hoy).
- **Sesión autenticada**: representa que un usuario inició sesión; permite el acceso hasta cerrar sesión o expirar.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un usuario nuevo puede registrarse e iniciar sesión en menos de 1 minuto.
- **SC-002**: El 100% de las consultas de un usuario devuelven únicamente sus documentos y los de demostración — 0% de fugas entre cuentas (verificable con prueba de aislamiento entre dos cuentas).
- **SC-003**: Un usuario que cierra sesión y vuelve a entrar recupera el 100% de los documentos que había subido.
- **SC-004**: El modo demo anónimo sigue funcionando igual que antes (probar sin cuenta, sin registro).
- **SC-005**: Las contraseñas nunca quedan almacenadas ni visibles en texto plano (verificable inspeccionando el almacenamiento).
- **SC-006**: Tras N intentos fallidos de login seguidos, nuevos intentos quedan temporalmente bloqueados.

## Assumptions

- **Verificación de email**: en Fase 1 no se exige confirmar el email (no hay envío de correos todavía). Se asume registro inmediato; la verificación se evaluará en una fase futura.
- **Recuperación de contraseña**: fuera de alcance en Fase 1. Si un usuario olvida su contraseña, no hay flujo de recuperación aún; se le informa.
- **Multi-tenant / organizaciones**: fuera de alcance (Fase 2). En Fase 1 cada cuenta es individual.
- **OAuth / Login con Google**: fuera de alcance (fase futura). Solo email + contraseña.
- **Retención**: los documentos de una cuenta persisten hasta que el usuario los elimine o elimine su cuenta. El modo anónimo mantiene su borrado automático actual.
- **Mínimo de contraseña**: se asume un largo mínimo razonable (p. ej. 8 caracteres) como buena práctica.
