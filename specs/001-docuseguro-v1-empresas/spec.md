# DocuSeguro v1 para Empresas — Especificación

**Feature:** `001-docuseguro-v1-empresas`
**Fecha:** junio 2026
**Estado:** Borrador

---

## Resumen

DocuSeguro permite a empresas —estudios de abogados, oficinas contables y corredoras de seguros— consultar documentos internos en lenguaje natural sin que los datos personales (RUT, correos, teléfonos) salgan al exterior. Esta especificación cubre la versión lista para ofrecer a empresas: landing page profesional, sistema de cuentas, trial gratuito de 14 días y panel básico del usuario.

---

## Objetivos

- Que una empresa que recibe el link de DocuSeguro pueda entender qué es, registrarse y empezar a usar sin necesidad de explicación adicional.
- Que el período de prueba gratuito motive a probar sin compromiso y genere interés en contratar.
- Que el panel del usuario muestre claramente el valor recibido (documentos consultados, datos protegidos) y el tiempo de prueba restante.

---

## Usuarios y actores

| Actor | Descripción |
|-------|-------------|
| **Visitante** | Llega al sitio por primera vez, sin cuenta |
| **Usuario en trial** | Registrado, dentro del período de 14 días gratuitos |
| **Usuario activo** | Con suscripción vigente (futuro; fuera de scope de esta versión) |
| **Admin (Bastián)** | Puede ver usuarios registrados y su estado de trial |

---

## Fases

### Fase 1 — Cuentas de usuario *(ya construida, falta desplegar)*
Registro con email y contraseña, login, logout, eliminación de cuenta. Cada usuario tiene sus documentos aislados. Los documentos subidos como usuario autenticado son persistentes (no se eliminan en 10 min).

### Fase 2 — Trial gratuito
Al registrarse, el usuario recibe 14 días de acceso completo. Cuando el trial vence, puede seguir viendo su historial pero no puede subir nuevos documentos ni hacer consultas hasta contratar.

### Fase 3 — Landing page profesional
Página de inicio rediseñada: propuesta de valor clara, secciones por rubro (abogados, contadores, seguros), demostración visual de la protección de datos, llamada a la acción para registrarse y empezar el trial.

### Fase 4 — Panel del usuario
Dashboard accesible desde la app tras iniciar sesión: documentos subidos, historial de consultas, estadísticas de datos protegidos y días de trial restantes (o estado de suscripción).

---

## Requisitos funcionales

### RF-01 · Registro y login (Fase 1)
- El visitante puede registrarse con email y contraseña.
- El sistema valida que el email no esté en uso y que la contraseña cumpla mínimos de seguridad.
- Al registrarse exitosamente, inicia sesión automáticamente y comienza el trial de 14 días.
- El usuario puede cerrar sesión y volver a iniciar en cualquier momento.

### RF-02 · Trial gratuito de 14 días (Fase 2)
- Desde el momento del registro, el usuario tiene 14 días con acceso completo a todas las funciones.
- El sistema muestra cuántos días de trial restan en la interfaz (panel y barra de sesión).
- Al vencer el trial, el usuario puede ver su historial pero no puede subir documentos ni hacer consultas.
- El mensaje de trial vencido debe indicar claramente cómo continuar (contacto con Bastián).

### RF-03 · Landing page profesional (Fase 3)
- La página de inicio presenta DocuSeguro como producto, no como demo técnica.
- Incluye secciones diferenciadas para los tres rubros objetivo: abogados, contadores, seguros.
- Muestra cómo funciona la protección de datos con un ejemplo visual simple.
- Tiene una llamada a la acción principal: "Empieza tu prueba gratuita de 14 días".
- No usa lenguaje técnico (no menciona RAG, embeddings, ChromaDB, etc.).
- Incluye link a aviso de privacidad y términos.

### RF-04 · Panel del usuario (Fase 4)
- Accesible desde la app tras iniciar sesión.
- Muestra: email del usuario, días de trial restantes (o estado), total de documentos subidos, total de consultas realizadas, tipos de datos protegidos detectados.
- Permite eliminar la cuenta (con confirmación).
- El diseño es coherente con el resto de la app.

---

## Escenarios de usuario

### Escenario 1 — Primer contacto (abogado)
1. Rodrigo, abogado, recibe el link de DocuSeguro por correo.
2. Lee la landing page y entiende para qué sirve sin ayuda.
3. Hace clic en "Empieza gratis", se registra con su email.
4. Sube un contrato de arrendamiento y hace una pregunta.
5. Ve que el RUT del arrendatario fue protegido antes de enviarse a la IA.
6. Revisa su panel: 1 documento subido, 1 consulta, 14 días de trial.

### Escenario 2 — Trial vencido
1. María, contadora, usó DocuSeguro durante 14 días.
2. Al día 15 intenta subir un balance y ve un mensaje de trial vencido.
3. El mensaje le indica que escriba a Bastián para continuar.
4. Puede seguir viendo el historial de consultas anteriores.

### Escenario 3 — Visitante que no se registra
1. León, corredor de seguros, entra a la landing.
2. Ve la sección de seguros, entiende el caso de uso.
3. Puede usar la demo anónima (comportamiento actual) sin registrarse.
4. Al final de la demo, se le invita a registrarse para guardar su historial.

---

## Criterios de éxito

| Criterio | Medición |
|----------|----------|
| Un visitante nuevo entiende qué hace DocuSeguro en menos de 30 segundos | Test con 3 personas del rubro objetivo |
| El flujo registro → primera consulta se completa en menos de 3 minutos | Medición cronometrada |
| El trial vencido bloquea el uso sin romper el acceso al historial | Verificación funcional |
| El panel muestra datos reales del usuario sin errores | Verificación funcional |
| La landing no usa lenguaje técnico ni jerga de IA | Revisión de texto |

---

## Entidades de datos

| Entidad | Campos relevantes |
|---------|------------------|
| **User** | id, email, password_hash, created_at |
| **Trial** | user_id, started_at, expires_at, is_active |
| **Document** | id, user_id, filename, chunk_count, created_at |
| **QueryLog** | id, user_id, query_text, pii_found, created_at |

---

## Supuestos y decisiones tomadas

- **Duración del trial:** 14 días desde el registro. Sin tarjeta de crédito requerida.
- **Plan después del trial:** contacto directo con Bastián (no hay pago online en esta versión).
- **Demo anónima:** se mantiene — los visitantes pueden usar la demo sin registrarse.
- **Admin panel:** fuera de scope. Bastián puede ver usuarios directamente en la base de datos.
- **Envío de correos:** fuera de scope en esta versión (no hay email de bienvenida ni recordatorio de trial).
- **Landing page:** reemplaza la página de inicio actual; la demo queda accesible desde un botón en la landing.

---

## Fuera de scope

- Pago online o suscripción automática.
- Panel de administración con interfaz visual.
- Envío de emails automáticos (bienvenida, recordatorio de trial, vencimiento).
- Versión on-premise / instalable.
- Soporte multi-idioma.
- App móvil.
