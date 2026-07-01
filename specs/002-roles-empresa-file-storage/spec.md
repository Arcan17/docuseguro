# Feature Specification: Roles de Empresa + Almacenamiento Persistente de Documentos

**Feature:** `002-roles-empresa-file-storage`
**Fecha:** 2026-06-29
**Estado:** Borrador

---

## Resumen

DocuSeguro actualmente funciona con usuarios individuales y sesiones anónimas. Esta fase agrega dos capacidades clave para uso empresarial:

1. **Roles de empresa**: una organización puede tener múltiples usuarios con distintos permisos (admin, editor, viewer). Los documentos se comparten dentro de la organización y están aislados de otras organizaciones.
2. **Almacenamiento persistente de documentos**: los archivos subidos se guardan de forma duradera (no se pierden al reiniciar el servidor). Los usuarios pueden hacer consultas sobre documentos previamente subidos sin tener que subirlos de nuevo.

---

## Usuarios y actores

| Actor | Descripción |
|-------|-------------|
| **Admin de organización** | Crea la org, invita miembros, asigna roles, puede ver y eliminar documentos de todos |
| **Editor** | Puede subir documentos y hacer consultas sobre todos los docs de la org |
| **Viewer** | Solo puede hacer consultas; no puede subir ni eliminar documentos |
| **Usuario individual** | Flujo actual anónimo/personal, sin org (sigue existiendo) |

---

## User Scenarios & Testing

### User Story 1 — Admin crea organización e invita miembros (P1)

Un contador quiere que su equipo de 5 personas use DocuSeguro sobre los documentos legales de sus clientes. Crea una organización "Estudio Contable XYZ", invita a 4 colegas y les asigna rol Editor o Viewer.

**Por qué P1**: Sin esto no existe el concepto de organización. Es el punto de entrada para todo lo demás.

**Independent Test**: Se puede probar creando una org, invitando un usuario y verificando que ambos ven la misma biblioteca de documentos.

**Acceptance Scenarios**:

1. **Given** un usuario registrado sin org, **When** crea una organización con nombre, **Then** se convierte en Admin de esa org y ve el panel de la org.
2. **Given** un Admin, **When** ingresa el email de un colega y le asigna rol Editor, **Then** el colega recibe invitación y al aceptar accede a la org con permisos de Editor.
3. **Given** un Viewer invitado, **When** intenta subir un documento, **Then** la acción está bloqueada con mensaje explicativo.
4. **Given** dos organizaciones distintas, **When** un usuario de Org A accede a la app, **Then** solo ve los documentos de Org A, nunca los de Org B.

---

### User Story 2 — Editor sube documento que persiste para toda la org (P1)

Un abogado sube el contrato de un cliente. Al día siguiente, otro miembro del equipo puede hacer consultas sobre ese contrato sin que nadie lo vuelva a subir.

**Por qué P1**: La persistencia es el diferenciador principal respecto al flujo actual. Sin esto, el almacenamiento de documentos no tiene valor real.

**Independent Test**: Subir un documento, cerrar sesión, abrir nueva sesión y consultar el documento — debe responder sin re-subida.

**Acceptance Scenarios**:

1. **Given** un Editor autenticado en una org, **When** sube un PDF, **Then** el documento aparece en la biblioteca de la org con nombre, fecha y autor.
2. **Given** un documento en la biblioteca, **When** el servidor se reinicia o redespliega, **Then** el documento sigue disponible para consultas.
3. **Given** un Viewer de la misma org, **When** hace una consulta, **Then** el sistema responde basándose en todos los documentos de la org (incluyendo los subidos por otros miembros).
4. **Given** un Admin, **When** elimina un documento de la biblioteca, **Then** el documento deja de aparecer en consultas inmediatamente para todos los miembros.

---

### User Story 3 — Viewer consulta documentos de la org (P2)

Una asistente legal (rol Viewer) hace preguntas sobre contratos que el abogado principal subió, sin necesidad de acceder a los archivos originales.

**Por qué P2**: Depende de P1 (org) y P1 (persistencia). Es el flujo de uso diario una vez que la base está lista.

**Independent Test**: Probar con un Viewer que solo tiene acceso de lectura — puede consultar todos los docs de la org pero no subir ni eliminar.

**Acceptance Scenarios**:

1. **Given** un Viewer autenticado, **When** hace una pregunta sobre un documento de la org, **Then** recibe respuesta con fuentes citadas.
2. **Given** un Viewer, **When** intenta eliminar un documento, **Then** la opción no está disponible en la interfaz.
3. **Given** una consulta multiturno (conversación), **When** el Viewer hace preguntas de seguimiento, **Then** el sistema mantiene el contexto de la conversación.

---

### Edge Cases

- ¿Qué pasa si un Admin elimina la organización? → Todos los miembros pierden acceso y los documentos se marcan para eliminación.
- ¿Qué pasa si un Admin revoca el rol de un miembro activo? → La sesión activa expira en el próximo request.
- ¿Qué pasa si se sube un documento duplicado (mismo nombre, mismo contenido)? → Sistema alerta del duplicado y pregunta si reemplazar.
- ¿Qué pasa si el almacenamiento externo falla durante la subida? → La subida falla con error claro; no queda documento a medias indexado.
- ¿Un usuario puede pertenecer a más de una organización? → Sí, con roles independientes por org.

---

## Requirements

### Functional Requirements — Roles de Empresa

- **FR-001**: El sistema DEBE permitir crear una organización con nombre único.
- **FR-002**: El creador de la organización DEBE recibir automáticamente el rol Admin.
- **FR-003**: Un Admin DEBE poder invitar usuarios por email con rol predefinido (Admin / Editor / Viewer).
- **FR-004**: Un Admin DEBE poder cambiar el rol de cualquier miembro o eliminarlo de la org.
- **FR-005**: Los documentos subidos dentro de una org DEBEN ser visibles para todos los miembros de esa org.
- **FR-006**: Los documentos de una org NUNCA deben ser visibles para miembros de otra org.
- **FR-007**: Un Viewer NO DEBE poder subir ni eliminar documentos.
- **FR-008**: Un Editor DEBE poder subir documentos pero NO eliminar documentos de otros usuarios.
- **FR-009**: Un Admin DEBE poder subir y eliminar cualquier documento de la org.
- **FR-010**: Un usuario sin org DEBE poder seguir usando el flujo individual actual (sin cambios).

### Functional Requirements — Almacenamiento Persistente

- **FR-011**: Los archivos subidos DEBEN almacenarse de forma duradera, independiente del ciclo de vida del servidor.
- **FR-012**: Los documentos DEBEN seguir disponibles para consultas tras un redeploy o reinicio del servidor.
- **FR-013**: La biblioteca de documentos de la org DEBE mostrar: nombre del archivo, fecha de subida, usuario que lo subió y tamaño.
- **FR-014**: Un Admin DEBE poder eliminar documentos de la biblioteca; la eliminación DEBE remover el archivo y los vectores indexados.
- **FR-015**: El sistema DEBE soportar documentos de hasta 10 MB por archivo.
- **FR-016**: El sistema DEBE soportar al menos los formatos: PDF, DOCX, XLSX, TXT.
- **FR-017**: Al hacer una consulta, el sistema DEBE buscar sobre todos los documentos activos de la org, no solo el último subido.

---

## Success Criteria

1. Un equipo de 3 personas puede compartir una biblioteca de documentos y hacer consultas sin re-subir archivos — flujo completo en menos de 5 minutos desde el primer acceso.
2. Un documento subido sigue respondiendo consultas correctamente después de 24 horas y tras un reinicio del servidor.
3. Un Viewer no puede realizar ninguna acción de escritura (subida, eliminación) desde ningún punto de la interfaz.
4. Los documentos de una organización son completamente invisibles para usuarios de otra organización, verificable con dos cuentas en orgs distintas.
5. La biblioteca soporta al menos 50 documentos por organización sin degradación perceptible en el tiempo de respuesta de consultas.

---

## Key Entities

| Entidad | Atributos clave |
|---------|----------------|
| **Organization** | id, nombre, creado_por, fecha_creación |
| **OrgMember** | org_id, user_id, rol (admin/editor/viewer), fecha_invitación, estado (pendiente/activo) |
| **Document** | id, org_id, nombre_archivo, tamaño, formato, subido_por, fecha_subida, storage_url, estado (activo/eliminado) |
| **VectorChunk** | id, doc_id, org_id, texto, vector, índice |

---

## Assumptions

- El almacenamiento de archivos físicos usará un servicio de object storage (S3 o compatible). Los vectores siguen en ChromaDB pero con `org_id` como filtro de aislamiento.
- La invitación por email usará el sistema de email ya configurado en el proyecto (o un servicio transaccional básico).
- Los usuarios ya tienen cuentas individuales (la feature de user accounts del spec `001-user-accounts` es prerequisito).
- No incluye billing ni límites por plan en esta fase — todos los orgs tienen el mismo nivel de acceso.
- No incluye SSO/SAML corporativo en esta fase.

---

## Dependencias

- **Prerequisito**: Spec `001-user-accounts` — sistema de autenticación y cuentas individuales debe estar implementado.
- **Prerequisito**: Acceso a un servicio de object storage (AWS S3, Cloudflare R2, o similar).
- **Relacionado**: Spec `001-docuseguro-v1-empresas` — define el contexto comercial y los actores, pero no el modelo técnico de roles.
