# Feature Specification: Repositorio de Documentos Buscable por Identificador

**Feature Branch**: `005-document-repository`

**Created**: 2026-06-30

**Status**: Draft

**Input**: Sobre el almacenamiento persistente de la spec 002, agregar metadatos de cliente por
documento y búsqueda por identificador (nombre o RUT cifrado), para encontrar y consultar todos los
documentos de un cliente en un solo lugar sin re-subirlos.

---

## Resumen

Las oficinas que usarían DocuSeguro (estudios jurídicos, contables, corredoras) manejan muchos
documentos de muchos clientes. Hoy, para consultar un documento, hay que subirlo cada vez. Esta
funcionalidad agrega, encima del almacenamiento persistente de la **spec 002**, un **repositorio
buscable**: cada documento puede etiquetarse con datos del cliente al que pertenece (nombre,
identificador, tipo de documento, fecha) y luego encontrarse al instante buscando por ese
identificador. Encontrado el documento, el usuario lo consulta con el flujo de Q&A existente,
reutilizando el enmascarado de datos antes del LLM.

**Decisión de privacidad central:** el RUT (u otro identificador personal) **nunca se guarda ni se
muestra en claro**. Se almacena como una huella irreversible con clave (HMAC) que permite búsqueda
por coincidencia exacta sin que el RUT real exista en la base de datos. Como alternativa, el cliente
puede usar un identificador NO personal (folio, código interno, número de carpeta) como llave de
búsqueda principal. Esto mantiene intacta la promesa de DocuSeguro (Principio I) incluso para la
función que más se acerca a manejar datos personales.

**Alcance de despliegue:** está pensada para el **tier on-premise / a medida de pago**, donde los
documentos viven en el servidor del propio cliente. Su uso en la nube SaaS multi-cliente queda
**condicionado** a tener cifrado en reposo, registro de auditoría y contrato de tratamiento de datos
(DPA) — la Fase 4 de la constitución. En la demo pública solo se usa con datos NO confidenciales
(Principio IV).

---

## Usuarios y actores

Hereda los roles de organización de la **spec 002**:

| Actor | Qué puede hacer en el repositorio |
|-------|-----------------------------------|
| **Admin de organización** | Etiquetar, buscar, consultar, re-etiquetar y eliminar documentos de toda la org |
| **Editor** | Subir y etiquetar documentos, buscar, consultar; eliminar los propios |
| **Viewer** | Solo buscar y consultar; no puede etiquetar, subir ni eliminar |

El **identificador del cliente del documento** (ej. el RUT del cliente cuyo contrato es) NO es un
usuario del sistema: es un dato de metadatos del documento.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Etiquetar un documento con los datos de su cliente (Priority: P1)

Un editor de un estudio jurídico sube (o ya tiene en la biblioteca de la org) el contrato de un
cliente y lo etiqueta con el nombre del cliente, su RUT y el tipo de documento ("contrato"). El RUT
se guarda como huella con clave, no en texto plano.

**Why this priority**: Sin etiquetas no hay nada que buscar. Es la base del repositorio.

**Independent Test**: Etiquetar un documento con nombre, RUT y tipo; verificar en la base que el RUT
NO aparece en claro (solo su huella) y que el documento queda asociado a esos metadatos.

**Acceptance Scenarios**:

1. **Given** un editor autenticado en una org, **When** etiqueta un documento con nombre de cliente,
   RUT y tipo de documento, **Then** el documento queda registrado con esos metadatos y el RUT
   almacenado solo como huella irreversible con clave.
2. **Given** la configuración de la org usa un identificador NO personal (folio), **When** el editor
   etiqueta un documento, **Then** se le pide el folio en vez del RUT y no se solicita dato personal.
3. **Given** un intento de etiquetar sin ningún identificador buscable, **When** se guarda,
   **Then** el sistema exige al menos un identificador (nombre, RUT o folio) antes de aceptar.
4. **Given** un viewer, **When** intenta etiquetar un documento, **Then** la acción está bloqueada
   con mensaje explicativo.

---

### User Story 2 — Encontrar todos los documentos de un cliente por su identificador (Priority: P1)

Una asistente legal necesita "todos los documentos del cliente con RUT X" o "los documentos de Juan
Pérez". Escribe el RUT o el nombre y obtiene al instante la lista de documentos de ese cliente
dentro de su organización.

**Why this priority**: Es el valor central — tener la información en un solo lugar, sin re-subir.

**Independent Test**: Con varios documentos etiquetados, buscar por un RUT exacto y verificar que
devuelve exactamente los documentos de ese cliente; buscar por nombre parcial y verificar las
coincidencias; confirmar que nunca se muestra el RUT en claro en los resultados.

**Acceptance Scenarios**:

1. **Given** documentos etiquetados con RUT, **When** el usuario busca por un RUT exacto,
   **Then** el sistema aplica la misma huella con clave a lo buscado y devuelve los documentos que
   coinciden, sin mostrar el RUT en claro.
2. **Given** documentos con nombres de cliente, **When** el usuario busca por parte del nombre,
   **Then** devuelve los documentos cuyo nombre de cliente coincide parcialmente.
3. **Given** un usuario de la Org A, **When** busca un identificador que existe en la Org B,
   **Then** no obtiene ningún resultado de la Org B (aislamiento por organización).
4. **Given** una búsqueda sin coincidencias, **When** se ejecuta, **Then** devuelve lista vacía con
   mensaje claro, sin error.
5. **Given** resultados de búsqueda, **When** el usuario filtra por tipo de documento y/o rango de
   fecha, **Then** la lista se acota según esos filtros.

---

### User Story 3 — Consultar (Q&A) los documentos encontrados (Priority: P2)

Encontrados los documentos de un cliente, el usuario hace preguntas en lenguaje natural sobre ellos
(uno o varios), y el sistema responde reutilizando el flujo de privacidad existente (enmascarado de
datos personales antes de llamar al LLM).

**Why this priority**: Cierra el ciclo (encontrar → usar), pero depende de que buscar (P1) funcione.

**Independent Test**: Tras encontrar los documentos de un cliente, hacer una pregunta y verificar
que la respuesta se basa en esos documentos y que los datos personales se enmascararon antes del LLM.

**Acceptance Scenarios**:

1. **Given** los documentos de un cliente encontrados, **When** el usuario hace una pregunta sobre
   ellos, **Then** recibe una respuesta basada en esos documentos, con datos personales enmascarados
   antes de llegar al LLM.
2. **Given** un viewer, **When** consulta documentos encontrados, **Then** puede preguntar pero no
   puede modificar ni eliminar.
3. **Given** una consulta sobre varios documentos del mismo cliente, **When** se ejecuta,
   **Then** la respuesta puede considerar el conjunto de esos documentos.

---

### User Story 4 — Configurar el identificador y los tipos de documento por organización (Priority: P3)

El admin de la org elige si la llave de búsqueda principal es el RUT (cifrado) o un identificador no
personal (folio/código interno), y define la lista de tipos de documento que su oficina maneja
(contrato, escritura, póliza, balance, etc.).

**Why this priority**: Personalización "a medida" (Principio III), pero el repositorio funciona con
defaults razonables aunque no se configure.

**Independent Test**: Cambiar el identificador principal de RUT a folio y verificar que el formulario
de etiquetado y la búsqueda usan folio; agregar un tipo de documento y verificar que aparece como
opción al etiquetar.

**Acceptance Scenarios**:

1. **Given** un admin, **When** configura el identificador principal como "folio interno",
   **Then** el etiquetado y la búsqueda de la org pasan a usar folio y no piden RUT.
2. **Given** un admin, **When** define los tipos de documento de su org, **Then** esos tipos
   aparecen como opciones al etiquetar y como filtros al buscar.

---

### Edge Cases

- ¿Qué pasa si el RUT se escribe con o sin puntos/guion (12.345.678-9 vs 123456789)? → Se normaliza
  a un formato canónico antes de aplicar la huella, para que la búsqueda coincida igual.
- ¿Qué pasa si dos documentos comparten el mismo cliente (mismo RUT)? → Ambos aparecen agrupados bajo
  ese cliente en los resultados.
- ¿Qué pasa si se pierde o rota la clave usada para la huella del RUT? → Las huellas viejas dejan de
  coincidir; el sistema debe documentar que rotar la clave invalida la búsqueda por identificador
  previo (decisión de operación, no se asume rotación silenciosa).
- ¿Qué pasa si un viewer intenta ver el RUT en claro? → Nunca se muestra en claro a ningún rol; el
  RUT no es recuperable desde la huella.
- ¿Qué pasa si se elimina un documento? → Desaparece de la búsqueda y de las consultas
  inmediatamente para toda la org (hereda comportamiento de la spec 002).
- ¿Qué pasa si se intenta usar esta función en la demo pública con datos reales? → No corresponde:
  en demo solo datos NO confidenciales (Principio IV); la función plena es para on-premise / nube con
  controles de Fase 4.
- ¿Qué pasa si el nombre del cliente trae tildes o mayúsculas distintas? → La búsqueda por nombre es
  insensible a mayúsculas y tildes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir asociar a cada documento metadatos del cliente al que
  pertenece: nombre del cliente, un identificador (RUT u otro código), tipo de documento y fecha.
- **FR-002**: El sistema MUST exigir al menos un identificador buscable (nombre, RUT o folio) para
  guardar el etiquetado; el resto de los campos son opcionales.
- **FR-003**: El sistema NO debe almacenar ni mostrar el RUT (ni otro identificador personal) en
  texto plano; MUST guardarlo como huella irreversible con clave (HMAC) que permita búsqueda exacta.
- **FR-004**: El sistema MUST permitir buscar documentos por identificador exacto (RUT o folio)
  aplicando a lo buscado la misma transformación con clave usada al guardar.
- **FR-005**: El sistema MUST permitir buscar documentos por nombre de cliente (coincidencia
  parcial, insensible a mayúsculas y tildes) y filtrar por tipo de documento y por rango de fecha.
- **FR-006**: El sistema MUST normalizar el RUT a un formato canónico (sin puntos/guion, etc.) antes
  de aplicar la huella, para que variantes de escritura del mismo RUT coincidan.
- **FR-007**: El sistema MUST aislar el repositorio por organización: una organización solo ve y
  busca sus propios documentos (hereda de la spec 002).
- **FR-008**: El sistema MUST respetar los roles de la spec 002: admin y editor pueden etiquetar y
  eliminar; viewer solo busca y consulta.
- **FR-009**: El sistema MUST permitir, sobre los documentos encontrados, hacer consultas de Q&A
  reutilizando el flujo de privacidad existente (enmascarado de datos personales antes del LLM).
- **FR-010**: El sistema MUST permitir configurar por organización (a) el identificador principal de
  búsqueda (RUT cifrado vs identificador no personal) y (b) la lista de tipos de documento.
- **FR-011**: El sistema MUST funcionar con datos reales de clientes solo en despliegue on-premise o
  en nube con cifrado en reposo, auditoría y DPA; en la demo pública MUST operar solo con datos no
  confidenciales.
- **FR-012**: El sistema MUST tratar el nombre del cliente como dato personal: visible para los
  miembros autorizados de la org, nunca expuesto fuera de ella ni enviado sin enmascarar a servicios
  externos de IA.

### Key Entities *(include if feature involves data)*

- **Documento** (extiende el de la spec 002): un archivo persistido de una organización. Se le
  agregan metadatos de cliente: nombre del cliente, huella del identificador, identificador no
  personal opcional (folio), tipo de documento y fecha.
- **Identificador de cliente**: la llave de búsqueda. Si es personal (RUT), se guarda solo como
  huella irreversible con clave; si es no personal (folio/código), puede guardarse legible. Nunca se
  almacena el RUT en claro.
- **Cliente del documento**: la persona o empresa a la que pertenece el documento (no es un usuario
  del sistema). Se representa por su nombre y su identificador; varios documentos pueden compartirlo.
- **Configuración de repositorio por organización**: define el identificador principal (RUT cifrado
  vs folio) y los tipos de documento de esa organización.
- **Organización y roles** (de la spec 002): determinan aislamiento y permisos sobre el repositorio.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un usuario encuentra todos los documentos de un cliente buscando su identificador en
  menos de 5 segundos, sin volver a subir ningún archivo.
- **SC-002**: En una inspección de la base de datos, el 0% de los RUT (u otros identificadores
  personales) aparece en texto plano; solo existen sus huellas.
- **SC-003**: Una búsqueda por RUT exacto devuelve exactamente los documentos de ese cliente dentro
  de la organización, y cero documentos de otras organizaciones.
- **SC-004**: Variantes de escritura del mismo RUT (con o sin puntos/guion) devuelven el mismo
  resultado de búsqueda.
- **SC-005**: Un viewer puede buscar y consultar pero no puede etiquetar ni eliminar en el 100% de
  los intentos.
- **SC-006**: Sobre un documento encontrado, una consulta de Q&A responde con datos personales
  enmascarados antes de llegar al LLM en el 100% de los casos.

## Assumptions

- Depende de la **spec 002** (organizaciones, roles, almacenamiento persistente). Si 002 no está
  implementada, esta feature no puede entregarse completa; comparten la base de datos de documentos.
- La búsqueda por identificador personal es por **coincidencia exacta** (no parcial), porque una
  huella irreversible no permite búsqueda parcial. La búsqueda parcial aplica solo al nombre.
- La clave usada para la huella del identificador la administra el operador/despliegue; rotarla
  invalida las búsquedas por identificadores previos (no se asume rotación automática).
- El enmascarado de datos antes del LLM ya existe en DocuSeguro y se reutiliza tal cual.
- El identificador no personal por defecto sugerido es un "folio/código interno" libre definido por
  la organización.
- v1 cubre búsqueda por un identificador y por nombre; relaciones más ricas (carpetas por cliente,
  jerarquías de expediente) quedan fuera de alcance de esta versión.
- El despliegue por defecto de esta feature es on-premise; habilitarla en la nube SaaS requiere los
  controles de Fase 4 (cifrado en reposo, auditoría, DPA) y es una decisión explícita, no el default.
