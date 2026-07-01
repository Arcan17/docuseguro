# Feature Specification: Respuestas Fieles al Documento + PII Legible + Ingesta Robusta

**Feature Branch**: `006-answer-fidelity`

**Created**: 2026-06-30

**Status**: Draft

**Input**: Que DocuSeguro responda SOLO con lo que está en los documentos subidos (nada de
conocimiento general/matemáticas/historia), que los datos personales del documento se vean
correctos y legibles en las respuestas (no como `[uuid]`), y que maneje bien todos los archivos que
una persona pueda subir (incluido lo que hoy no se puede leer).

---

## Resumen

Tres mejoras de **calidad y confianza** del producto, priorizadas como fases:

1. **Fidelidad al documento** — DocuSeguro solo responde con información contenida en los documentos
   del usuario. Si la respuesta no está ahí (una operación matemática, un dato histórico, cultura
   general, o simplemente algo no incluido en los PDFs), se niega con un mensaje claro en vez de
   contestar con conocimiento del mundo o inventar.
2. **PII legible** — los datos personales del documento (RUT, correo, teléfono) se ven correctos y
   completos en las respuestas, no como marcadores ilegibles, sin dejar de enmascararse antes de
   llegar a la IA.
3. **Ingesta robusta** — el sistema se comporta bien con todos los tipos de archivo, incluye leer
   imágenes y PDFs escaneados (OCR) y más formatos, y da mensajes claros cuando no puede leer algo.

Todo reutiliza el pipeline y el enmascarado existentes. Nada de esto relaja la privacidad: los datos
personales se siguen enmascarando ANTES de llegar al LLM.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Solo responde con lo que está en los documentos (Priority: P1)

Un usuario con documentos cargados pregunta algo que NO está en ellos: "¿cuánto es 2+2?", "¿en qué
año llegó el hombre a la Luna?", o un dato del negocio que no aparece en ningún PDF. DocuSeguro NO
lo responde: contesta con un mensaje claro como "Esa información no está en tus documentos".

**Why this priority**: Es la base de la confianza en un producto de consulta documental. Si el
sistema "inventa" o contesta con conocimiento general, el usuario no puede fiarse de ninguna
respuesta — especialmente en contextos legales/contables.

**Independent Test**: Con un documento cargado que no menciona matemáticas ni historia, preguntar
"¿cuánto es 15×3?" y "¿quién descubrió América?" y verificar que responde que no está en los
documentos, sin dar el resultado ni el dato.

**Acceptance Scenarios**:

1. **Given** un documento cargado que no contiene la respuesta, **When** el usuario hace una pregunta
   de conocimiento general (matemática, historia, cultura general), **Then** el sistema responde que
   esa información no está en sus documentos y NO entrega la respuesta de conocimiento del mundo.
2. **Given** un documento cargado, **When** el usuario pregunta algo del mismo tema pero que el
   documento no cubre, **Then** el sistema indica que el documento no contiene esa información en vez
   de inventar.
3. **Given** una pregunta cuya respuesta SÍ está en el documento, **When** el usuario la hace,
   **Then** el sistema responde correctamente citando/apoyándose en el documento.
4. **Given** que no se recupera contexto relevante para la pregunta, **When** se procesa,
   **Then** el sistema responde con un mensaje claro de "no encontré esa información en tus
   documentos" (nunca una respuesta inventada).

---

### User Story 2 — Los datos personales del documento se ven correctos y legibles (Priority: P1)

Un usuario sube un contrato con RUT y correo y pregunta "¿cuál es el RUT del arrendatario?". La
respuesta muestra el RUT real y correcto (ej. `12.345.678-9`), no un marcador ilegible ni un valor
cambiado por otro.

**Why this priority**: Hoy los datos personales del documento aparecen como marcadores opacos y a
veces cambiados de lugar, lo que hace inútiles las respuestas sobre datos clave. Es tan crítico como
la fidelidad.

**Independent Test**: Subir un documento con dos RUT distintos (ej. arrendador y arrendatario) y un
correo; preguntar por cada uno y verificar que la respuesta muestra el valor correcto y legible, sin
confundir uno con otro y sin marcadores crudos.

**Acceptance Scenarios**:

1. **Given** un documento con datos personales, **When** el usuario pregunta por uno de ellos,
   **Then** la respuesta muestra el valor real y legible, no un marcador tipo `[uuid]`.
2. **Given** un documento con varios datos personales del mismo tipo (dos RUT), **When** el usuario
   pregunta por uno específico, **Then** la respuesta devuelve el correcto y no lo intercambia con el
   otro.
3. **Given** cualquier consulta, **When** el sistema procesa el documento, **Then** los datos
   personales se enmascaran ANTES de enviarse a la IA (la IA nunca ve el RUT real) y se restauran
   solo en la respuesta final al usuario.
4. **Given** una respuesta con datos personales restaurados, **When** se muestra al usuario,
   **Then** no queda ningún marcador sin restaurar ni valor corrupto.

---

### User Story 3 — Manejo claro de archivos que no se pueden leer (Priority: P2)

Una persona sube una foto de una factura, un PDF escaneado, un archivo dañado o un tipo no soportado.
El sistema no falla en silencio ni indexa basura: le dice con claridad qué pasó y qué puede hacer.

**Why this priority**: Evita la peor experiencia (subir algo y no recibir nada, sin saber por qué).
Parte ya está implementada (mensajes 422 en español); esta historia consolida la política.

**Independent Test**: Subir un archivo sin texto legible y verificar que la respuesta es un mensaje
claro (no un éxito con cero resultados ni un error genérico de servidor).

**Acceptance Scenarios**:

1. **Given** un archivo del que no se puede extraer texto (imagen/escaneo/corrupto), **When** se
   sube, **Then** el sistema responde con un mensaje claro que explica el motivo y no indexa un
   documento vacío.
2. **Given** un tipo de archivo no soportado, **When** se sube, **Then** el sistema lo rechaza
   indicando qué formatos sí acepta.
3. **Given** un archivo válido con texto, **When** se sube, **Then** se procesa normalmente.

---

### User Story 4 — Leer imágenes y PDFs escaneados (OCR) (Priority: P3)

Una persona sube una **foto de una factura** o un **PDF escaneado** (sin texto seleccionable).
DocuSeguro reconoce el texto de la imagen (OCR) y permite consultarlo como cualquier otro documento.

**Why this priority**: Es muy común (la gente fotografía facturas/documentos), pero es una capacidad
nueva que agrega dependencia y solo aplica con controles de privacidad (ver restricciones). Depende
de que el resto de la ingesta ya sea robusta.

**Independent Test**: Subir una imagen con texto conocido y verificar que, tras el OCR, una pregunta
sobre ese texto se responde correctamente.

**Acceptance Scenarios**:

1. **Given** una imagen o PDF escaneado con texto, **When** se sube en un despliegue habilitado para
   OCR, **Then** el texto se reconoce y queda disponible para consultas.
2. **Given** un despliegue de demo pública, **When** se intenta subir una imagen con datos
   personales reales, **Then** el OCR de datos sensibles no procede (solo on-premise / Fase 4) y se
   informa al usuario.
3. **Given** una imagen sin texto reconocible, **When** se procesa, **Then** el sistema informa que
   no encontró texto legible (misma política que la Historia 3).

---

### User Story 5 — Soportar más formatos frecuentes (Priority: P3)

El usuario sube un `.csv` (planilla exportada) o un `.pptx` (presentación) y puede consultarlo.

**Why this priority**: Amplía la cobertura a formatos que la gente sí usa, pero no es tan crítico
como los P1/P2. Reutiliza el mismo pipeline de extracción → chunking → consulta.

**Independent Test**: Subir un `.csv` con datos tabulares y verificar que una pregunta sobre una fila
se responde correctamente, preservando la estructura de la tabla.

**Acceptance Scenarios**:

1. **Given** un archivo `.csv` con filas y columnas, **When** se sube, **Then** su contenido queda
   disponible para consultas preservando la relación fila/columna.
2. **Given** un archivo `.pptx` con texto en diapositivas, **When** se sube, **Then** el texto de las
   diapositivas queda disponible para consultas.

---

### Edge Cases

- ¿Qué pasa si el documento SÍ trata el tema pero no tiene el dato exacto preguntado? → Responde que
  el documento no contiene ese dato específico, sin completarlo con conocimiento externo.
- ¿Qué pasa si la pregunta mezcla algo del documento con algo externo ("suma los montos y conviértelo
  a dólares de hoy")? → Responde la parte que está en el documento (los montos) y aclara que la parte
  externa (tipo de cambio de hoy) no está en los documentos.
- ¿Qué pasa si el LLM igual intenta responder de conocimiento general pese al guardarraíl? → Debe
  existir una verificación que evite entregar respuestas no apoyadas en el contexto recuperado.
- ¿Qué pasa si un dato personal aparece muchas veces en el documento? → Se enmascara de forma
  consistente (el mismo valor → el mismo marcador) y se restaura correctamente.
- ¿Qué pasa si el LLM altera o no reproduce bien un marcador de PII? → El diseño de marcadores debe
  minimizar esa confusión (marcadores legibles y estables) y la restauración no debe dejar marcadores
  a medias en la respuesta.
- ¿Qué pasa si un documento está en otro idioma? → La fidelidad al documento aplica igual (responde
  solo con su contenido).
- ¿Qué pasa con un OCR de baja calidad que produce texto parcial/errado? → Se trata como texto del
  documento; si es ilegible, aplica la política de "sin texto legible".

## Requirements *(mandatory)*

### Functional Requirements

**Fidelidad al documento (P1)**

- **FR-001**: El sistema MUST responder únicamente con información contenida en los documentos del
  usuario y MUST negarse a responder preguntas cuya respuesta no esté en ellos (conocimiento general,
  matemáticas, datos históricos, etc.).
- **FR-002**: Cuando la respuesta no esté en los documentos, el sistema MUST entregar un mensaje
  claro indicándolo, y NO debe entregar una respuesta basada en conocimiento del mundo ni inventada.
- **FR-003**: El sistema MUST evitar entregar respuestas que no estén apoyadas en el contexto
  recuperado de los documentos (verificación de fundamentación), incluso cuando existan documentos
  cargados que no cubran la pregunta.
- **FR-004**: Cuando no se recupere contexto relevante, el sistema MUST responder con un mensaje de
  "no encontré esa información en tus documentos", nunca con una respuesta inventada.

**PII legible (P1)**

- **FR-005**: Los datos personales del documento (RUT, correo, teléfono) MUST verse correctos y
  legibles en la respuesta final al usuario, sin marcadores crudos ni valores corruptos.
- **FR-006**: El sistema MUST conservar la correspondencia entre cada dato personal y su marcador a
  través de todo el pipeline (ingesta y consulta) para poder restaurarlos correctamente (hoy esa
  correspondencia se descarta en la ingesta).
- **FR-007**: Los marcadores de datos personales MUST ser legibles y estables (que identifiquen el
  tipo y distingan múltiples valores, p.ej. "RUT 1", "correo 1") para que la IA no los confunda ni
  los intercambie.
- **FR-008**: El sistema MUST seguir enmascarando los datos personales ANTES de enviarlos a la IA; la
  IA nunca recibe el valor real (Principio I). El cambio solo afecta cómo se muestran después.
- **FR-009**: Cuando el mismo dato personal aparece varias veces, el sistema MUST usar el mismo
  marcador de forma consistente y restaurarlo igual en toda la respuesta.

**Ingesta robusta y formatos (P2/P3)**

- **FR-010**: El sistema MUST manejar los archivos ilegibles/corruptos/no soportados con un mensaje
  claro para el usuario, sin indexar documentos vacíos ni devolver errores genéricos de servidor.
- **FR-011**: El sistema MUST poder reconocer texto de imágenes y PDFs escaneados (OCR) en los
  despliegues habilitados para ello.
- **FR-012**: El sistema MUST soportar formatos tabulares/comunes adicionales (al menos `.csv` y
  `.pptx`) preservando su estructura relevante (filas/columnas, texto de diapositivas).
- **FR-013**: El OCR y el manejo de imágenes con datos personales reales MUST limitarse a despliegue
  on-premise o nube con controles de Fase 4; en la demo pública se opera solo con datos no
  confidenciales (Principio IV).

### Key Entities *(include if feature involves data)*

- **Documento y sus chunks** (existente): el texto extraído del archivo, dividido para búsqueda. Se
  le asocia el mapa de datos personales para poder restaurarlos.
- **Mapa de datos personales (token map)**: correspondencia entre cada dato personal detectado y su
  marcador legible. Debe persistir/asociarse al documento y a la sesión para restaurar en las
  respuestas (hoy se descarta en la ingesta).
- **Marcador de PII**: etiqueta legible y estable que reemplaza al dato personal antes de la IA
  (identifica tipo e índice; nunca contiene el valor real).
- **Respuesta**: el texto entregado al usuario, apoyado solo en el contexto del documento y con los
  datos personales restaurados correctamente.
- **Resultado de extracción/OCR**: el texto obtenido de un archivo (incluye el caso "sin texto
  legible").

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En un conjunto de preguntas de conocimiento general (matemáticas, historia, cultura
  general) sobre documentos que no las contienen, el 100% se responde con "no está en tus documentos"
  y 0% entrega la respuesta de conocimiento del mundo.
- **SC-002**: En preguntas cuya respuesta SÍ está en el documento, la tasa de respuesta correcta se
  mantiene o mejora respecto del comportamiento actual (sin sacrificar utilidad por el guardarraíl).
- **SC-003**: En documentos con datos personales, el 100% de las respuestas que citan un dato
  personal lo muestran legible y correcto (sin marcadores crudos ni valores intercambiados).
- **SC-004**: En una inspección del texto enviado a la IA, el 0% contiene datos personales sin
  enmascarar.
- **SC-005**: El 100% de los archivos ilegibles/no soportados produce un mensaje claro al usuario y 0
  documentos vacíos indexados.
- **SC-006**: En despliegues con OCR habilitado, una imagen/PDF escaneado con texto conocido permite
  responder correctamente una pregunta sobre ese texto.
- **SC-007**: Un `.csv` y un `.pptx` con contenido conocido permiten responder correctamente una
  pregunta sobre ese contenido.

## Assumptions

- El pipeline de recuperación (búsqueda por similitud) y el enmascarado de PII existen y se
  reutilizan; esta feature los endurece, no los reemplaza.
- "Fidelidad al documento" se apoya en el contexto recuperado; ajustar el umbral de similitud y/o
  agregar una verificación de fundamentación son medios válidos, a decidir en el plan.
- La corrección de la compresión de contexto (que preservaba mal las tablas) ya está aplicada y es
  base para las respuestas correctas sobre documentos tabulares.
- El mecanismo de restauración de PII en respuestas (incluida la versión en streaming) ya existe; el
  cambio es conservar el mapa en la ingesta y usar marcadores legibles.
- El OCR agrega una dependencia nueva; la elección local vs nube se decide en el plan, respetando que
  OCR de datos sensibles reales es solo on-premise/Fase 4.
- Los mensajes claros para archivos ilegibles/no soportados (422 en español) ya están implementados y
  esta spec los consolida como política.
- El alcance de despliegue de las capacidades que tocan datos reales (OCR, PII de documentos) sigue
  la constitución: demo pública solo con datos no confidenciales.
