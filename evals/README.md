# Evals — evaluación de calidad

Suite de evaluación del componente que más diferencia a DocuSeguro: el **borrado
de datos personales (PII)** antes de enviar texto al modelo de lenguaje.

## Por qué

Medir la calidad de un sistema de IA —no solo que "funcione"— es lo que separa un
prototipo de un producto serio. Acá la métrica crítica es de privacidad: una sola
fuga de un RUT o correo al LLM rompe la promesa del producto.

## Qué mide

`run_pii_eval.py` corre **offline** (solo regex locales, sin LLM ni red) sobre un
dataset etiquetado (`pii_dataset.py`) y reporta:

- **Recall** — de todos los datos personales reales, ¿cuántos detectó? (una fuga = recall < 1)
- **Precision** — de todo lo que redactó, ¿cuánto era realmente PII? (sobre-redacción baja la precision)
- **F1** — media armónica de ambas

El dataset incluye RUT en varios formatos (con/sin puntos, dígito K, múltiples),
correos, teléfonos chilenos, fichas mixtas y **casos negativos** (montos, fechas,
números de artículo) que NO deben redactarse.

## Cómo correr

```bash
python -m evals.run_pii_eval
```

Sale con código ≠ 0 si el F1 cae bajo `F1_THRESHOLD` (0.90) — apto para CI.

## Alcance y limitaciones

- Cubre PII estructurada (RUT, correo, teléfono) vía regex determinista.
- Nombres y direcciones requieren NER (spaCy, opcional vía `SPACY_ENABLED=true`)
  y no están en este set base.
