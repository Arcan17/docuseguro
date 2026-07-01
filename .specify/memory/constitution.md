<!--
SYNC IMPACT REPORT
==================
Version change: (none) → 1.0.0
Bump rationale: Initial ratification of the DocuSeguro constitution. No prior version existed.

Principles defined (1.0.0):
  I.   Privacidad Primero (NON-NEGOTIABLE)
  II.  IA con Costo Flexible por Cliente
  III. Configurable por Cliente (Multi-Tenant)
  IV.  Madurez de Datos por Fase
  V.   Entrega por Fases
  VI.  Spec-Driven (NON-NEGOTIABLE)

Added sections:
  - Core Principles (6 principios)
  - Restricciones de Seguridad y Cumplimiento (Section 2)
  - Flujo de Desarrollo (Section 3)
  - Governance

Removed sections: none (initial creation)

Templates requiring updates:
  ✅ .specify/templates/plan-template.md — la sección "Constitution Check" es genérica; los gates
     de estos principios se evalúan al planificar cada feature. Sin cambios estructurales necesarios.
  ✅ .specify/templates/spec-template.md — compatible; las specs deben declarar tier de datos
     (confidencial/no confidencial) y modo de IA cuando apliquen (cubierto por Principios II y IV).
  ✅ .specify/templates/tasks-template.md — compatible; tareas de privacidad, medición de tokens y
     cumplimiento se categorizan según Principios I, II y la Section 2.

Follow-up TODOs: ninguno. Fecha de ratificación = fecha de creación (proyecto sin constitución previa).
-->

# DocuSeguro Constitution

DocuSeguro es un SaaS chileno de preguntas y respuestas sobre documentos con privacidad por
diseño: enmascara datos personales (RUT, correo, teléfono) antes de enviarlos a un modelo de
lenguaje. Modelo de negocio: piloto gratis de 14 días → ajustes a medida (pago único) →
mantención mensual recurrente. Desarrollado por un equipo de una persona (Bastián Altamirano).

## Core Principles

### I. Privacidad Primero (NON-NEGOTIABLE)

Ningún dato personal puede salir hacia un servicio externo de IA sin estar previamente
enmascarado. El enmascaramiento de datos identificables (como mínimo RUT, correo y teléfono)
ocurre ANTES de cualquier llamada a un LLM externo, sin excepción. El producto MUST cumplir la
Ley 19.628 de Chile sobre protección de la vida privada.

Rationale: la privacidad no es una característica, es la razón de existir de DocuSeguro. Una sola
filtración destruye la propuesta de valor y expone legalmente al cliente y al proveedor. Cualquier
ruta de código que mande texto a un LLM debe ser auditable para demostrar que pasó por el
enmascarador.

### II. IA con Costo Flexible por Cliente

La arquitectura MUST soportar, configurable por cliente, tres modos de inferencia:
(a) IA gestionada por el proveedor, (b) la API key del propio cliente (BYO), y (c) un modelo
local/on-premise. El sistema MUST medir el consumo de tokens por cliente. El modelo de cobro de
la IA (incluido en la mensualidad, pass-through con margen, BYO, u on-premise) es una decisión
COMERCIAL y nunca una limitación del código.

Rationale: el costo de los tokens es la mayor incógnita del negocio. Si la arquitectura fija un
solo modo, el precio queda atrapado por una decisión técnica. Soportar los tres modos y medir el
consumo permite elegir y cambiar el modelo de cobro por cliente sin reprogramar, y refuerza el
argumento de privacidad para clientes sensibles (BYO/on-premise).

### III. Configurable por Cliente (Multi-Tenant)

Los tipos de documento, los prompts y el branding MUST ser ajustables por cliente mediante
configuración, sin modificar el núcleo del producto. El aislamiento de datos entre clientes
(tenants) MUST estar garantizado.

Rationale: la oferta es "ajustes a medida". Si cada cliente exige tocar el core, el negocio no
escala y cada cambio arriesga romper a los demás. La personalización vive en configuración por
tenant, no en forks del código.

### IV. Madurez de Datos por Fase

Hasta que existan almacenamiento persistente, registro de auditoría y opción on-premise, los
pilotos MUST usar únicamente datos NO confidenciales. No se onboardea ningún cliente con datos
sensibles reales (salud, expedientes legales con datos de terceros) en versiones que no cumplan
esos requisitos. El nivel de datos permitido MUST declararse explícitamente por feature y por
cliente.

Rationale: ofrecer hoy el producto para datos confidenciales reales expone legalmente al
proveedor y al cliente. La confianza se gana por fases; prometer de más antes de tener los
controles es el mayor riesgo del proyecto.

### V. Entrega por Fases

El producto se construye en este orden de fases, y una fase no se promete como disponible hasta
estar implementada y verificada: hosting estable → autenticación → almacenamiento + roles →
IA flexible (Principio II) → cumplimiento B2B (backups, auditoría, contrato de tratamiento de
datos/DPA, SLA) → facturación (billing).

Rationale: un dev solo no puede construir todo a la vez. El orden refleja dependencias reales
(no hay storage útil sin auth; no hay cumplimiento B2B sin storage) y evita vender capacidades
que aún no existen. La "personalización a medida" es una propiedad habilitada en las fases de
storage e IA flexible, no una fase aparte.

### VI. Spec-Driven (NON-NEGOTIABLE)

Todo cambio que afecte la arquitectura, autenticación, almacenamiento, manejo de datos
personales o el modelo de IA MUST pasar por el flujo Spec Kit (specify → clarify → plan → tasks →
analyze → implement) ANTES de implementarse. Correcciones de bugs puntuales, cambios de texto y
scripts simples quedan exentos.

Rationale: el costo de un error de arquitectura en un producto de privacidad es alto y difícil de
revertir. Especificar antes de codificar fuerza a resolver ambigüedades y deja trazabilidad de
por qué el sistema es como es.

## Restricciones de Seguridad y Cumplimiento

- **Secretos fuera del repo**: las API keys (Groq u otras) viven SOLO en `.env` gitignored.
  Nunca se commitean. El placeholder vacío vive en `.env.example`.
- **Enmascaramiento verificable**: el componente que enmascara PII (RUT, correo, teléfono) es
  parte del camino crítico y MUST tener pruebas que demuestren que ningún dato sin enmascarar
  llega a un LLM externo.
- **Tokens en el navegador**: la mitigación del riesgo XSS del token en localStorage es un
  pendiente conocido y debe resolverse antes de manejar datos sensibles reales (ligado a
  Principio IV).
- **Cumplimiento legal**: Ley 19.628 (Chile) sobre datos personales aplica a los datos de los
  clientes y a la prospección comercial. Para clientes con datos confidenciales reales, se
  requiere un contrato de tratamiento de datos (DPA) antes del onboarding.
- **Prospección sin spam**: las herramientas de prospección NO envían correos automáticamente;
  el contacto es manual, sobre sitios públicos, respetando robots.txt.

## Flujo de Desarrollo

- El flujo Spec Kit es obligatorio para el trabajo descrito en el Principio VI. Cada feature
  empieza en `specs/NNN-nombre/`.
- Cada spec MUST declarar: el tier de datos que toca (confidencial / no confidencial) y, si invoca
  IA, el modo de inferencia soportado (gestionado / BYO / on-premise).
- Una fase del Principio V no se anuncia como disponible (a clientes o en marketing) hasta estar
  implementada y verificada.
- Antes de cerrar una feature que toque PII o IA, se verifica el cumplimiento de los Principios I
  y II contra el código real, no contra la intención.

## Governance

Esta constitución supersede cualquier otra práctica del proyecto. Las enmiendas requieren:
(1) documentar el cambio y su razón, (2) actualizar la versión según versionado semántico, y
(3) propagar el impacto a las plantillas y specs afectadas.

Versionado de esta constitución:
- **MAJOR**: eliminación o redefinición incompatible de un principio o de la gobernanza.
- **MINOR**: adición de un principio o sección, o expansión material de una guía existente.
- **PATCH**: aclaraciones, correcciones de redacción, refinamientos no semánticos.

Cumplimiento: todo plan de feature (`/speckit-plan`) MUST verificar alineación con estos
principios en su "Constitution Check". Las desviaciones MUST justificarse explícitamente o
corregirse antes de implementar. Ante duda sobre si un trabajo requiere Spec Kit, se aplica la
guía del `CLAUDE.md` del workspace.

**Version**: 1.0.0 | **Ratified**: 2026-06-30 | **Last Amended**: 2026-06-30
