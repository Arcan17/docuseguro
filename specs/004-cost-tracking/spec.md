# Feature Specification: Medidor de Costo de IA por Cliente

**Feature Branch**: `004-cost-tracking`

**Created**: 2026-06-30

**Status**: Draft

**Input**: Convertir el consumo de tokens ya registrado (tabla QueryLog) en costo monetario por
cliente y período, para que el operador (Bastián) decida cuánto cobrar de mantención mensual.

---

## Resumen

DocuSeguro ya registra el consumo de tokens por consulta (tokens originales, tokens comprimidos
tras el enmascarado, latencia, si hubo PII, si fue cache hit) y expone un reporte agregado de
métricas. Lo que falta es **traducir esos tokens a dinero** y **separarlos por cliente**.

Esta funcionalidad agrega una capa de **costeo**: toma el consumo registrado, lo multiplica por el
precio del proveedor de IA usado, lo convierte a pesos chilenos y lo presenta agrupado por cliente
y por rango de fechas. Es una herramienta **interna del operador**, de solo lectura, que no toca el
flujo del usuario final. Su propósito de negocio es habilitar la decisión de precio de la
mantención mensual con datos reales (Principio II de la constitución).

---

## Usuarios y actores

| Actor | Descripción |
|-------|-------------|
| **Operador** (Bastián) | Único usuario de esta función. Consulta cuánto le cuesta la IA por cliente para fijar precios. Accede con credencial de operador (la misma que protege `/metrics` hoy). |

El **usuario final** (quien sube documentos y consulta) NO ve esta función ni se ve afectado por ella.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — El operador ve el costo de IA por cliente en un período (Priority: P1)

Bastián quiere saber, antes de proponerle un precio de mantención a un cliente, cuánto le costó la
IA de ese cliente en el último mes. Abre el reporte de costos, elige el cliente y el rango de
fechas, y ve: tokens consumidos, costo estimado en USD y en CLP, y número de consultas.

**Why this priority**: Es el núcleo de la funcionalidad. Sin esto no hay forma de poner precio con
datos reales — que es la razón de existir de la feature.

**Independent Test**: Con consultas ya registradas para un cliente, pedir el reporte de ese cliente
en un rango de fechas y verificar que el costo en USD y CLP corresponde a (tokens × precio del
proveedor × tipo de cambio).

**Acceptance Scenarios**:

1. **Given** consultas registradas de un cliente en un período, **When** el operador pide el reporte
   de costo de ese cliente para ese período, **Then** ve total de tokens, costo en USD, costo en CLP
   y número de consultas.
2. **Given** un cliente sin actividad en el período, **When** se pide su reporte, **Then** el sistema
   responde con costo cero y cero consultas, sin error.
3. **Given** un período que abarca consultas con distintos proveedores de IA, **When** se pide el
   reporte, **Then** el costo total suma correctamente el aporte de cada proveedor según su precio.

---

### User Story 2 — Precios de proveedor configurables sin tocar código (Priority: P1)

Los precios de los proveedores de IA (Groq, OpenAI, Anthropic) cambian seguido. Bastián necesita
actualizar el precio por millón de tokens (entrada y salida) de cada proveedor/modelo sin
reprogramar ni redeployar el sistema.

**Why this priority**: Si los precios están escritos en el código, el reporte queda desactualizado y
las decisiones de precio se toman con datos falsos. La configurabilidad es lo que mantiene el costeo
confiable.

**Independent Test**: Cambiar el precio de un proveedor en la configuración, volver a pedir el mismo
reporte y verificar que el costo cambió en proporción, sin cambios de código.

**Acceptance Scenarios**:

1. **Given** un precio configurado para un proveedor/modelo, **When** se calcula el costo de una
   consulta de ese proveedor, **Then** se usa el precio configurado (entrada y salida por separado
   si el dato existe).
2. **Given** que el operador actualiza el precio de un proveedor, **When** vuelve a pedir el reporte,
   **Then** el costo refleja el precio nuevo sin necesidad de redeploy.
3. **Given** una consulta de un proveedor/modelo sin precio configurado, **When** se calcula el
   costo, **Then** el sistema marca esa consulta como "precio no configurado" en vez de asumir cero
   silenciosamente.

---

### User Story 3 — El operador ve el ahorro que genera el enmascarado (Priority: P2)

El scrubber de DocuSeguro reduce los tokens (de `original_tokens` a `compressed_tokens`). Bastián
quiere mostrar —a sí mismo y como argumento de venta— cuánto dinero ahorra ese enmascarado.

**Why this priority**: Refuerza la propuesta de valor (privacidad que además abarata), pero depende
de que el costeo base (P1) ya funcione.

**Independent Test**: Para un período con consultas donde `compressed_tokens < original_tokens`,
verificar que el reporte muestra el costo "sin enmascarar" vs el costo "real" y la diferencia
(ahorro) en CLP.

**Acceptance Scenarios**:

1. **Given** consultas con tokens originales mayores a los comprimidos, **When** se pide el reporte,
   **Then** muestra costo estimado con tokens originales, costo real con tokens comprimidos y el
   ahorro en USD y CLP.
2. **Given** un período sin reducción de tokens, **When** se pide el reporte, **Then** el ahorro se
   muestra como cero, sin error.

---

### Edge Cases

- ¿Qué pasa si una consulta no tiene desglose entrada/salida, solo total? → Se estima el costo con
  el total y un supuesto de proporción configurable; el reporte marca esos costos como "estimados".
- ¿Qué pasa si el tipo de cambio USD→CLP no está configurado o está vencido? → El reporte muestra el
  costo en USD igual y advierte que el CLP usa un tipo de cambio por defecto o desactualizado.
- ¿Qué pasa mientras no exista el concepto de organización (spec 002)? → El agrupamiento cae a un
  identificador disponible (usuario o credencial/API key) en vez de organización.
- ¿Qué pasa con las consultas de sesiones anónimas? → Se agrupan bajo un cubo "anónimo/demo"
  separado de los clientes reales.
- ¿Qué pasa si dos consultas usan el mismo proveedor pero distinto modelo con distinto precio? → El
  costo se calcula por modelo, no por proveedor a secas.
- ¿Qué pasa con un cliente en modo BYO (paga su propia IA)? → Su costo de tokens es informativo para
  el cliente, pero se marca como "no facturable al operador" (el operador no lo paga).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST calcular el costo monetario de cada consulta a partir de los tokens
  registrados y el precio configurado del proveedor/modelo que la atendió.
- **FR-002**: El sistema MUST distinguir tokens de entrada y de salida cuando el dato esté
  disponible, aplicando precios distintos a cada uno; si solo hay total, MUST estimar usando una
  proporción configurable y marcar el resultado como estimado.
- **FR-003**: El sistema MUST permitir configurar los precios por proveedor y por modelo (precio por
  millón de tokens de entrada y de salida) sin modificar código ni redeployar.
- **FR-004**: El sistema MUST agrupar el costo por cliente (organización cuando exista; en su
  ausencia, por usuario o credencial) y por rango de fechas.
- **FR-005**: El sistema MUST convertir el costo a pesos chilenos (CLP) usando un tipo de cambio
  USD→CLP configurable, mostrando también el costo en USD.
- **FR-006**: El sistema MUST mostrar, por cliente y período, al menos: total de tokens, número de
  consultas, costo en USD y costo en CLP.
- **FR-007**: El sistema MUST exponer el ahorro de tokens del enmascarado: costo con tokens
  originales vs costo con tokens comprimidos y la diferencia.
- **FR-008**: El acceso al reporte de costos MUST estar restringido al operador (misma protección que
  el reporte de métricas actual); ningún usuario final puede verlo.
- **FR-009**: Los reportes MUST contener solo datos agregados de uso y costo; NO deben exponer ningún
  dato personal (contenido de documentos, RUT, correos, teléfonos).
- **FR-010**: El sistema MUST funcionar para los tres modos de inferencia de la constitución
  (IA gestionada por el operador, API key del cliente / BYO, y modelo on-premise), marcando en cada
  caso si el costo lo paga el operador o el cliente.
- **FR-011**: El sistema MUST manejar consultas de proveedor/modelo sin precio configurado
  marcándolas explícitamente como "precio no configurado" en vez de contarlas como costo cero.
- **FR-012**: Las sesiones anónimas / de demo MUST contabilizarse en un grupo separado de los
  clientes reales.

### Key Entities *(include if feature involves data)*

- **Registro de consulta** (existente, `QueryLog`): una consulta atendida, con tokens originales,
  tokens comprimidos, proveedor/modelo usado, marca de tiempo y, cuando exista, el cliente al que
  pertenece. Es la fuente de datos del costeo.
- **Tarifa de proveedor**: precio por millón de tokens de entrada y de salida, asociado a un
  proveedor y un modelo, editable por el operador. Incluye fecha de vigencia para no recalcular el
  pasado con precios nuevos si así se decide.
- **Tipo de cambio**: valor USD→CLP configurable usado para convertir el costo, con fecha.
- **Reporte de costo**: resultado agregado por cliente y período: tokens, consultas, costo en USD,
  costo en CLP, ahorro por enmascarado, y marca de quién paga (operador / cliente BYO).
- **Cliente / agrupador**: la entidad por la que se agrupa el costo. Es la organización cuando exista
  (spec 002); mientras tanto, el usuario o la credencial; y un cubo aparte para anónimos/demo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El operador puede obtener el costo de IA de un cliente para un mes dado en menos de 1
  minuto, sin editar código.
- **SC-002**: El costo reportado coincide con el cálculo manual (tokens × precio × tipo de cambio)
  con un margen de error menor al 1% para consultas con desglose entrada/salida.
- **SC-003**: Actualizar el precio de un proveedor y ver el reporte recalculado no requiere ningún
  cambio de código ni redeploy.
- **SC-004**: El 100% de los reportes generados no contiene ningún dato personal (verificable por
  inspección: solo cifras agregadas).
- **SC-005**: Para cualquier período, la suma de los costos por cliente más el grupo anónimo/demo
  iguala el costo total del sistema en ese período (cuadra el total).
- **SC-006**: El reporte muestra el ahorro del enmascarado en pesos para cualquier período con
  reducción de tokens.

## Assumptions

- El consumo de tokens por consulta ya se registra de forma confiable (tabla `QueryLog`); esta
  feature lee ese dato, no lo genera. Si falta el desglose entrada/salida, se estima.
- El proveedor/modelo usado en cada consulta está disponible o es derivable del registro; si hoy no
  se guarda, registrarlo es parte del alcance mínimo de esta feature.
- El concepto de "cliente/organización" puede no existir aún (depende de la spec 002). Mientras
  tanto se agrupa por usuario o credencial, y la migración a organización es directa cuando 002 esté.
- El tipo de cambio USD→CLP lo fija el operador manualmente; integrarse a una fuente automática de
  tipo de cambio queda fuera del alcance de esta versión.
- Es una herramienta interna de un solo operador; no requiere multiusuario, ni roles, ni una UI
  elaborada. Un reporte simple (datos legibles + exportable) es suficiente para v1.
- Reutiliza la protección de acceso del reporte de métricas existente.
