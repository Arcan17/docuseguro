# Feature Specification: Portal de Autoconsulta para Clientes Finales

**Feature Branch**: `008-customer-self-service`

**Created**: 2026-07-01

**Status**: Draft (documentado para fase posterior — NO implementar aún)

**Input**: Que los clientes finales de una empresa puedan preguntar por SU propia información
identificándose con su RUT, y recibir respuestas con los datos protegidos y aislados de otros
clientes.

---

## Resumen

Convierte DocuSeguro en un **producto de cara al cliente final**: una empresa (clínica, corredora,
estudio, etc.) le da a sus clientes un **portal de autoconsulta** donde cada cliente pregunta por
**su propia información** (su contrato, su póliza, sus documentos) y recibe respuestas privadas.

El cliente se **identifica de forma segura** y el sistema usa su **RUT convertido en un identificador
cifrado/huella** (nunca guardado ni mostrado en claro) para **acotar la búsqueda solo a sus
documentos**. La IA nunca ve datos reales (enmascarado de siempre) y cada cliente ve únicamente lo
suyo.

**Distinción de seguridad central (del usuario):** el RUT hasheado sirve para **buscar y proteger**
los datos, pero **NO es autenticación** (los RUT son casi públicos en Chile). Por eso la identidad se
**verifica aparte** con un segundo factor; recién entonces se usa el RUT como llave de búsqueda.

Depende de las specs **002** (cuentas/organizaciones) y **005** (documentos con identificador
cifrado/HMAC), más un mecanismo de **autenticación del cliente final**. Queda documentado para fase
posterior.

---

## Usuarios y actores

| Actor | Descripción |
|-------|-------------|
| **Cliente final** | Cliente de la empresa (NO es miembro de la organización). Solo accede a SUS propios documentos. |
| **Admin de la empresa** | Configura el portal: qué pueden consultar los clientes, cómo se verifican, qué datos se muestran. |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — El cliente se identifica de forma segura (Priority: P1)

Un cliente entra al portal de la empresa, ingresa su RUT y confirma su identidad con un segundo
factor (un código de un solo uso enviado a su correo/teléfono que la empresa tiene registrado, o un
link de acceso). Recién verificado, entra a su espacio.

**Why this priority**: Sin identidad verificada, cualquiera podría escribir el RUT de otro y ver sus
datos. Es el requisito de seguridad que hace viable toda la feature.

**Independent Test**: Intentar acceder solo con un RUT (sin segundo factor) → NO se concede acceso;
completar el segundo factor válido → se concede acceso a los documentos de ese RUT únicamente.

**Acceptance Scenarios**:

1. **Given** una persona que ingresa un RUT sin verificar identidad, **When** intenta consultar,
   **Then** el sistema NO le da acceso a ningún dato.
2. **Given** un cliente que ingresa su RUT y completa el segundo factor válido, **When** accede,
   **Then** queda vinculado a su RUT y solo a sus documentos.
3. **Given** una persona que ingresa el RUT de OTRO y NO puede completar el segundo factor de esa
   persona, **When** intenta acceder, **Then** el sistema lo rechaza.

---

### User Story 2 — El cliente pregunta por su información y solo ve lo suyo (Priority: P1)

Ya verificado, el cliente pregunta en lenguaje natural por su información y recibe respuestas basadas
solo en sus documentos, con los datos personales protegidos frente a la IA.

**Why this priority**: Es el valor central del portal.

**Independent Test**: Con dos clientes distintos y sus documentos, verificar que cada uno solo obtiene
respuestas de SUS documentos y nunca de los del otro.

**Acceptance Scenarios**:

1. **Given** un cliente verificado, **When** pregunta por su información, **Then** la respuesta se basa
   únicamente en los documentos asociados a su RUT (identificador cifrado).
2. **Given** dos clientes distintos, **When** cada uno consulta, **Then** ninguno puede ver ni inferir
   datos del otro (aislamiento total).
3. **Given** cualquier consulta, **When** se procesa, **Then** la IA nunca recibe datos personales en
   claro (enmascarado antes del modelo).

---

### User Story 3 — El RUT nunca se guarda ni se muestra en claro (Priority: P1)

El RUT del cliente se usa como llave de búsqueda en forma de identificador cifrado/huella; el valor
real no se almacena ni se expone.

**Why this priority**: Es la protección de datos en reposo que pide el usuario y la constitución.

**Independent Test**: Inspeccionar el almacenamiento y confirmar que el RUT en claro no aparece; que
la búsqueda por RUT funciona vía la huella; y que las respuestas no filtran el RUT salvo cuando
corresponda mostrarlo al propio dueño.

**Acceptance Scenarios**:

1. **Given** un cliente que se identifica con su RUT, **When** el sistema busca sus documentos,
   **Then** usa la huella/cifrado del RUT (no el valor en claro) para acotar la búsqueda.
2. **Given** una inspección del almacenamiento, **When** se revisa, **Then** el RUT no aparece en
   claro.

---

### User Story 4 — La empresa configura el portal (Priority: P2)

El admin define qué pueden consultar los clientes, cómo se verifican (correo/teléfono/link) y qué
datos se muestran (puede combinarse con la visibilidad por rol de la spec 007).

**Why this priority**: Personalización por cliente (Principio III), pero funciona con defaults.

**Acceptance Scenarios**:

1. **Given** un admin, **When** configura el método de verificación y el alcance de consulta,
   **Then** el portal de sus clientes respeta esa configuración.

---

### User Story 5 — Registro de accesos (auditoría) (Priority: P3)

Queda registro de qué cliente accedió y qué consultó, para cumplimiento (Ley 21.719), sin guardar
datos personales en claro en el registro.

**Acceptance Scenarios**:

1. **Given** un cliente que accede y consulta, **When** ocurre, **Then** se registra el evento
   (identificador del cliente, momento, resultado) sin el RUT ni datos personales en claro.

---

### Edge Cases

- ¿Y si la empresa no tiene el correo/teléfono del cliente para el segundo factor? → No se puede
  habilitar el acceso de ese cliente hasta tener un canal de verificación; se informa al admin.
- ¿Y si alguien intenta muchos RUT distintos (fuerza bruta)? → Debe haber límite de intentos y
  bloqueo; el segundo factor impide el acceso aunque adivinen el RUT.
- ¿Y si un cliente no tiene documentos asociados a su RUT? → Se le informa que no hay información
  disponible (sin revelar datos de nadie más).
- ¿Y si el cliente pregunta algo que no está en sus documentos? → Aplica la fidelidad al documento
  (spec 006): "no encontré eso en tus documentos".
- ¿El propio cliente puede ver su propio RUT/datos? → Sí, es su información; la protección es frente a
  la IA, frente a OTROS clientes, y en el almacenamiento — no frente al dueño (salvo reglas de la
  spec 007 si la empresa las aplica).
- ¿Rotación de la clave de la huella? → Invalida las búsquedas por identificadores previos (decisión
  de operación; heredado de la spec 005).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST verificar la identidad del cliente final con un segundo factor (código a
  correo/teléfono registrado, o link de acceso) ANTES de darle acceso a datos; el RUT por sí solo NO
  concede acceso.
- **FR-002**: Tras verificar, el sistema MUST usar el RUT convertido en identificador cifrado/huella
  para acotar la búsqueda y las respuestas SOLO a los documentos de ese cliente.
- **FR-003**: El sistema MUST aislar totalmente a los clientes entre sí: ninguno puede ver ni inferir
  datos de otro.
- **FR-004**: El RUT del cliente NO debe almacenarse ni mostrarse en claro; MUST usarse como huella
  irreversible con clave para la búsqueda (hereda spec 005).
- **FR-005**: La IA MUST recibir siempre los datos personales enmascarados; nunca el valor real
  (Principio I).
- **FR-006**: El sistema MUST limitar los intentos de acceso (anti fuerza bruta) y bloquear tras
  varios intentos fallidos.
- **FR-007**: El sistema MUST permitir a la empresa configurar el método de verificación, el alcance
  de consulta y qué datos se muestran (combinable con la spec 007).
- **FR-008**: El sistema MUST registrar los accesos y consultas de clientes para auditoría, sin
  almacenar el RUT ni datos personales en claro en ese registro.
- **FR-009**: Cuando el cliente pregunta algo que no está en sus documentos, el sistema MUST
  responder según la fidelidad al documento (spec 006), sin inventar.

### Key Entities *(include if feature involves data)*

- **Cliente final**: persona que consulta su propia información; representada por su identificador
  cifrado (huella del RUT) y un canal de verificación (correo/teléfono). No es miembro de la
  organización.
- **Identificador del cliente (huella del RUT)**: llave de búsqueda irreversible con clave; nunca el
  RUT en claro.
- **Verificación de identidad**: segundo factor (código de un solo uso, link) asociado a un canal de
  contacto que la empresa tiene registrado.
- **Documentos del cliente** (de la spec 005): documentos etiquetados con el identificador del
  cliente, sobre los que se acota la búsqueda.
- **Registro de acceso**: evento de auditoría sin datos personales en claro.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 0% de los accesos se concede solo con el RUT (sin segundo factor válido).
- **SC-002**: Un cliente verificado obtiene respuestas basadas únicamente en sus documentos en el
  100% de los casos; 0% de fuga de datos de otros clientes.
- **SC-003**: En una inspección del almacenamiento, el RUT en claro aparece en el 0% de los registros.
- **SC-004**: La IA recibe datos personales reales en el 0% de las consultas.
- **SC-005**: Tras N intentos fallidos, el acceso se bloquea (anti fuerza bruta).
- **SC-006**: El registro de auditoría no contiene RUT ni datos personales en claro (100%).

## Assumptions

- Depende de la **spec 002** (cuentas/organizaciones), la **spec 005** (documentos con identificador
  cifrado/HMAC) y de un mecanismo de **autenticación del cliente final** (segundo factor). Sin esas
  bases no se construye.
- La empresa debe tener un **canal de contacto verificado** del cliente (correo o teléfono) para
  enviar el segundo factor; sin él, ese cliente no puede habilitarse.
- El método de verificación por defecto sugerido es **código de un solo uso al correo/teléfono**; un
  link de acceso es alternativa. La elección final es del plan/empresa.
- Se combina naturalmente con la **spec 007** (visibilidad de datos por rol) si la empresa quiere
  limitar qué campos ve incluso el propio cliente.
- No implementar aún: queda **documentada** para una fase posterior (después de cuentas + repositorio
  por RUT). Encaja como evolución "producto de cara al cliente" del roadmap.
