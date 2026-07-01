# Phase 0 — Research: Respuestas Fieles + PII Legible (P1)

## Decisión 1 — Guardarraíl de fidelidad al documento

**Enfoque en tres capas complementarias (barato → seguro):**

1. **Corto-circuito por recuperación (principal).** Tras `search(...)`, mirar la **mejor similitud**
   de los chunks recuperados. Si está por debajo de un umbral de respuesta `answer_min_similarity`
   (más estricto que el `cosine_similarity_threshold=0.50` de recuperación), responder directamente
   "Esa información no está en tus documentos" **sin llamar al LLM**. Barato, determinístico y ahorra
   tokens.
2. **Prompt endurecido (refuerzo).** SYSTEM_PROMPT en español, con instrucción explícita: responder
   solo con el contexto; si el contexto no lo contiene, decir exactamente que no está en los
   documentos; NO usar conocimiento general (matemáticas, historia, cultura general); no inventar.
3. **Frase de negativa canónica.** El sistema define un texto fijo de negativa para el caso "no
   está", de modo que sea detectable y consistente (y testeable).

**Rationale:** la mayoría de las alucinaciones de conocimiento general ocurren cuando el modelo
"rellena" pese al contexto. El corto-circuito por similitud ataca el caso raíz (no hay nada
relevante) sin depender de que el modelo obedezca; el prompt cubre el caso en que sí hay algún
contexto tangencial.

**Umbral:** empezar `answer_min_similarity ≈ 0.62–0.65` (configurable), calibrable con la suite de
evals existente para no generar falsos negativos. Es un parámetro, no una decisión irreversible.

**Verificación de fundamentación (grounding-check) — descartada para P1.** Una segunda llamada al
LLM para verificar que la respuesta se apoya en el contexto duplicaría costo/latencia y podría
degradar utilidad. Se deja como posible mejora futura; el corto-circuito + prompt cubren el objetivo
medible (SC-001).

**Alternativas descartadas:** subir el umbral de recuperación 0.50 global → rompería el retrieval
normal; confiar solo en el prompt → los LLM igual alucinan conocimiento general.

---

## Decisión 2 — Marcadores de PII legibles y estables

**Decisión:** el scrubber deja de usar UUIDs y usa marcadores **por tipo e índice**:
`[RUT_1]`, `[RUT_2]`, `[CORREO_1]`, `[TELEFONO_1]`. Determinístico dentro de un `scrub()`: el mismo
valor recibe el mismo marcador; distintos valores del mismo tipo incrementan el índice.

**Rationale:** los UUID aleatorios son (a) imposibles de reproducir al pie de la letra por el LLM y
(b) indistinguibles entre sí, lo que hacía que el modelo los intercambiara → "datos desordenados".
Marcadores semánticos, cortos y numerados eliminan ambos problemas y el modelo los reproduce bien.

**Compatibilidad:** se mantiene la firma `scrub(text) -> (clean, token_map, detected)` y el
`token_map: dict[marcador -> original]`. `restorer.py` y `stream_restorer.py` no cambian de lógica
(siguen reemplazando `[marcador]`), solo sus tests que hoy asumen formato UUID.

**Fuga de tipo:** el marcador revela el *tipo* ("hay un RUT aquí"), no el valor. Es aceptable y
estándar; el dato sensible (el RUT real) sigue protegido.

**Alternativas descartadas:** UUID (el problema actual); marcadores genéricos `[PII_1]` sin tipo →
el modelo confundiría un RUT con un teléfono.

---

## Decisión 3 — Conservar y restaurar la PII del documento (sin colisiones entre documentos)

**Problema:** hoy la ingesta descarta el `token_map` del documento, así que la PII del documento
queda como marcador sin poder restaurarse. Además, si dos documentos usan cada uno `[RUT_1]` para
personas distintas, fusionar sus mapas colisiona.

**Decisión — mapa por documento + re-etiquetado en la consulta:**

1. **En la ingesta:** al scrubbear el documento, **guardar su `token_map`** en PostgreSQL asociado al
   `doc_id` (y al owner). Se guarda en la base relacional, **no** en el vector store, para no dejar
   valores reales en Chroma. Vigencia: TTL igual al del documento (efímero para anónimos; persistente
   cuando exista la spec 002).
2. **En la consulta:** por cada chunk recuperado (que trae su `doc_id`), cargar el mapa de su
   documento y resolver sus marcadores a los valores originales **en memoria**. Luego asignar
   **marcadores de presentación frescos y secuenciales por tipo** (`[RUT_1]`, `[RUT_2]`, …) únicos a
   través de todo el contexto ensamblado + la consulta. Reemplazar en el contexto los marcadores de
   almacenamiento por los de presentación. Enviar al LLM solo marcadores de presentación (nunca el
   valor real). Restaurar la respuesta con el mapa de presentación.

**Rationale:** el re-etiquetado en la consulta garantiza que el LLM siempre ve `[RUT_1..N]` limpios,
únicos y legibles, sin importar de cuántos documentos venga el contexto, y **sin colisiones**. La
misma persona (mismo original) en documento y consulta comparte marcador de presentación → coherencia.

**Principio I:** en todo momento el LLM ve solo marcadores; los valores reales viven en PostgreSQL y
se sustituyen únicamente en la respuesta final al usuario.

**Alternativas descartadas:** (a) guardar el mapa en metadata de Chroma → deja valores reales en el
vector store (mala postura de privacidad); (b) marcadores globalmente únicos tipo
`[RUT_<docid>_1]` enviados al LLM → funciona pero son más largos y feos para el modelo; el
re-etiquetado da lo mejor de ambos.

---

## Decisión 4 — Espacio de nombres consulta vs documento

**Decisión:** resuelto por la Decisión 3: al re-etiquetar en la consulta se construye **un único
espacio de marcadores de presentación** que cubre a la vez la PII de la consulta y la de los
documentos, deduplicando por valor original. No hay dos `[RUT_1]` con significados distintos en un
mismo prompt.

---

## Resumen de incógnitas resueltas

- ✅ Fidelidad: corto-circuito por similitud (umbral configurable) + prompt endurecido + frase
  canónica. Grounding-check con 2ª llamada: descartado para P1.
- ✅ Marcadores legibles por tipo e índice, manteniendo la API del scrubber.
- ✅ PII de documento: mapa por documento en PostgreSQL + re-etiquetado de presentación en la
  consulta; sin colisiones; la IA nunca ve valores reales.

Sin `NEEDS CLARIFICATION` pendientes.
