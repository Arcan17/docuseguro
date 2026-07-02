# Feature Specification: Visibilidad de Datos Personales por Rol

**Feature Branch**: `007-pii-visibility-by-role`

**Created**: 2026-07-01

**Status**: Draft (documentado para fase posterior — NO implementar aún)

**Input**: Que mostrar un dato personal (RUT, correo, teléfono) en la respuesta dependa del rol del
usuario: un rol autorizado lo ve; uno no autorizado recibe un aviso claro de "sin permiso",
distinto de "no encontrado".

---

## Resumen

Hoy DocuSeguro enmascara los datos personales antes de enviarlos a la IA y los **restaura para
cualquiera** que consulte. Esta feature hace que esa restauración dependa del **rol** del usuario
dentro de su organización:

- **Rol autorizado** (ej. admin) → ve el valor real (`12.345.678-9`).
- **Rol no autorizado** (ej. viewer) → NO ve el valor; recibe un aviso claro ("No tienes permiso
  para ver este dato" o una etiqueta "[dato protegido]").

Y separa **tres respuestas** que hoy se confunden en un solo mensaje, para no confundir al usuario:

1. El dato **no existe / no se encontró** → *"No encontré eso en tus documentos."*
2. El dato **existe pero tu rol no puede verlo** → *"No tienes permiso para ver este dato."*
3. El dato existe y tu rol puede verlo → **muestra el valor real**.

Refuerza la privacidad (Ley 21.719, minimización: solo quien corresponde ve datos personales) y es
un argumento de venta B2B fuerte. **Depende de los roles de la spec 002** (aún no implementada); por
eso queda documentada para una fase posterior.

---

## Usuarios y actores

Hereda los roles de organización de la **spec 002**:

| Actor | Acceso a datos personales (default sugerido) |
|-------|----------------------------------------------|
| **Admin de organización** | Ve todos los datos personales |
| **Editor** | Ve los datos personales (configurable) |
| **Viewer** | NO ve datos personales → recibe aviso "sin permiso" |
| **Usuario individual / anónimo** | Comportamiento definido por la organización o el modo demo |

Qué rol ve qué es **configurable por organización** (el default es solo una sugerencia).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Un rol autorizado ve el dato personal (Priority: P1)

Un admin pregunta por el RUT de un cliente que sí está en el documento. La respuesta muestra el RUT
real y legible.

**Why this priority**: Es el caso base autorizado; sin él no hay valor. Debe conservar el
comportamiento actual (mostrar el dato) para los roles permitidos.

**Independent Test**: Con un documento que contiene un RUT y un usuario con rol autorizado,
preguntar por el RUT y verificar que la respuesta muestra el valor real.

**Acceptance Scenarios**:

1. **Given** un usuario con rol autorizado y un documento con datos personales, **When** pregunta por
   un dato personal presente, **Then** la respuesta muestra el valor real.
2. **Given** que la IA procesa la consulta, **When** arma la respuesta, **Then** la IA nunca recibió
   el valor real (solo marcadores); el valor se restaura al final según el rol.

---

### User Story 2 — Un rol no autorizado NO ve el dato, con aviso claro (Priority: P1)

Un viewer pregunta por el RUT de un cliente que sí está en el documento. La respuesta NO muestra el
RUT; en su lugar aparece un aviso claro de que no tiene permiso para verlo.

**Why this priority**: Es el corazón de la feature — proteger datos personales según rol, con un
mensaje que no confunda.

**Independent Test**: Con el mismo documento y un usuario con rol no autorizado, preguntar por el
RUT y verificar que NO aparece el valor real y sí un aviso de "sin permiso".

**Acceptance Scenarios**:

1. **Given** un usuario con rol NO autorizado y un documento que contiene el dato, **When** pregunta
   por ese dato personal, **Then** la respuesta NO muestra el valor real y muestra un aviso claro de
   "no tienes permiso para ver este dato" (o una etiqueta "[dato protegido]").
2. **Given** una respuesta que mezcla información normal con un dato personal, **When** el rol no
   puede ver el dato, **Then** se responde la parte permitida y se protege solo el dato personal (no
   se bloquea toda la respuesta).

---

### User Story 3 — Tres mensajes distintos, sin confusión (Priority: P1)

El usuario debe poder distinguir claramente entre "no existe", "sin permiso" y "aquí está".

**Why this priority**: El problema original es que "no encontrado" y "protegido" se confundían en un
solo mensaje, lo que confunde al usuario.

**Independent Test**: Ejecutar las tres situaciones y verificar que cada una da un mensaje distinto y
claro.

**Acceptance Scenarios**:

1. **Given** un dato que NO está en los documentos, **When** se pregunta, **Then** el mensaje es de
   tipo "no encontrado".
2. **Given** un dato que SÍ está pero el rol no puede verlo, **When** se pregunta, **Then** el
   mensaje es de tipo "sin permiso" (distinto del anterior).
3. **Given** un dato que SÍ está y el rol puede verlo, **When** se pregunta, **Then** se muestra el
   valor real.

---

### User Story 4 — Configurar qué rol ve qué, por organización (Priority: P2)

El admin define qué roles pueden ver datos personales, e idealmente por tipo de dato (ej. un rol
puede ver el correo pero no el RUT).

**Why this priority**: Personalización por cliente (Principio III), pero funciona con un default
razonable si no se configura.

**Independent Test**: Cambiar la regla (ej. permitir al editor ver el correo pero no el RUT) y
verificar que las respuestas respetan esa configuración.

**Acceptance Scenarios**:

1. **Given** un admin, **When** configura qué roles ven datos personales (global o por tipo de dato),
   **Then** las respuestas de cada rol respetan esa configuración.
2. **Given** una organización sin configuración explícita, **When** un usuario consulta, **Then** se
   aplica el default (admin/editor ven; viewer no).

---

### User Story 5 — Registro de acceso a datos personales (Priority: P3)

Queda registro de quién vio (o intentó ver) qué dato personal, para auditoría y cumplimiento.

**Why this priority**: Necesario para cumplimiento B2B (Ley 21.719), pero es fase posterior (ligado
a la auditoría de Fase 4).

**Independent Test**: Tras varias consultas, verificar que existe un registro de accesos a datos
personales (quién, qué tipo de dato, cuándo, permitido o denegado) sin exponer el valor real en el
propio registro de forma insegura.

**Acceptance Scenarios**:

1. **Given** un usuario que consulta un dato personal, **When** se le muestra o se le deniega,
   **Then** queda registrado el evento (usuario, rol, tipo de dato, resultado permitido/denegado,
   fecha).

---

### Edge Cases

- ¿Qué pasa si el rol puede ver el correo pero no el RUT y la respuesta incluye ambos? → Muestra el
  correo, protege el RUT, en la misma respuesta.
- ¿Qué pasa con un usuario **anónimo / demo**? → Por defecto no ve datos personales reales (y en la
  demo pública solo hay datos no confidenciales, por Principio IV).
- ¿Qué pasa si la organización no tiene roles configurados aún (spec 002 no desplegada)? → Esta
  feature no aplica hasta que existan roles; el comportamiento previo (según spec 006) se mantiene.
- ¿Qué pasa si un dato personal aparece dentro de una frase larga? → Se protege solo el dato (se
  reemplaza por la etiqueta/aviso), no se descarta la frase completa.
- ¿El registro de auditoría podría filtrar el dato? → El registro NO debe guardar el valor real en
  claro; guarda el tipo de dato y el resultado, no el valor.
- ¿Un rol autorizado que pregunta por un dato que no existe? → Mensaje "no encontrado" (no "sin
  permiso").

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST decidir, al restaurar un dato personal en la respuesta, si el rol del
  usuario puede verlo; si puede, muestra el valor real; si no, lo protege.
- **FR-002**: Cuando el rol NO puede ver un dato personal presente, el sistema MUST reemplazarlo por
  un aviso claro ("No tienes permiso para ver este dato" o etiqueta "[dato protegido]"), sin exponer
  el valor real.
- **FR-003**: El sistema MUST distinguir tres respuestas con mensajes claramente diferentes:
  (a) dato no encontrado, (b) dato existe pero sin permiso, (c) dato mostrado.
- **FR-004**: El control de visibilidad MUST aplicarse en la restauración final; la IA MUST seguir
  recibiendo solo marcadores, nunca el valor real (Principio I intacto).
- **FR-005**: El sistema MUST permitir configurar por organización qué roles ven datos personales, e
  idealmente por tipo de dato (RUT, correo, teléfono), con un default razonable
  (admin/editor ven; viewer no).
- **FR-006**: Cuando una respuesta incluye varios datos y el rol solo puede ver algunos, el sistema
  MUST mostrar los permitidos y proteger los no permitidos en la misma respuesta.
- **FR-007**: El sistema MUST registrar los accesos a datos personales (usuario, rol, tipo de dato,
  resultado permitido/denegado, fecha) sin almacenar el valor real en claro en ese registro.
- **FR-008**: El comportamiento MUST heredar los roles y organizaciones de la spec 002; sin roles
  implementados, la feature no aplica y se mantiene el comportamiento previo.

### Key Entities *(include if feature involves data)*

- **Regla de visibilidad de PII**: por organización, define qué roles pueden ver qué tipos de dato
  personal (RUT, correo, teléfono). Tiene un default.
- **Rol y organización** (de la spec 002): determinan el permiso.
- **Dato personal en la respuesta**: cada valor a restaurar (con su tipo) sobre el que se evalúa el
  permiso.
- **Registro de acceso a PII**: evento de auditoría (usuario, rol, tipo de dato, resultado, fecha),
  sin el valor real.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un rol autorizado ve el 100% de los datos personales presentes que pregunta.
- **SC-002**: Un rol no autorizado ve el 0% de los datos personales protegidos; en su lugar recibe el
  aviso de "sin permiso" en el 100% de los casos.
- **SC-003**: En una inspección, el 0% de las respuestas a un rol no autorizado contiene el valor
  real de un dato protegido.
- **SC-004**: Las tres situaciones (no encontrado / sin permiso / mostrado) producen mensajes
  distintos y correctos en el 100% de las pruebas.
- **SC-005**: La IA nunca recibe el valor real de un dato personal (0% en el texto enviado al modelo),
  independiente del rol.
- **SC-006**: Cambiar la regla de visibilidad de una organización se refleja en las respuestas sin
  cambios de código.
- **SC-007**: El registro de auditoría de accesos a PII no contiene ningún valor personal en claro.

## Assumptions

- Depende de la **spec 002** (roles admin/editor/viewer + organizaciones) y del sistema de PII de la
  **spec 006** (marcadores + mapa por documento en `doc_pii`). Sin esas bases, esta feature no se
  puede construir.
- Default de visibilidad: admin y editor ven datos personales; viewer no. Configurable por
  organización; la granularidad por tipo de dato (ver correo pero no RUT) es deseable pero puede
  entregarse en una segunda iteración.
- El aviso exacto ("No tienes permiso para ver este dato" vs etiqueta "[dato protegido]") es una
  decisión de UX a afinar en el plan; ambos cumplen el objetivo.
- La auditoría de accesos (Historia 5) se alinea con la auditoría de Fase 4 de la constitución; puede
  entregarse después de las historias P1.
- No implementar aún: esta spec queda **documentada** para una fase posterior (después de los roles).
