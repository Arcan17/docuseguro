"""Dataset etiquetado para evaluar el borrado de PII.

Cada caso declara el texto y el conjunto EXACTO de cadenas que el scrubber
debería redactar (`pii`). Las cadenas que el scrubber detecta y que no están en
`pii` cuentan como falsos positivos (sobre-redacción); las de `pii` que no
detecta cuentan como falsos negativos (fugas).
"""

from dataclasses import dataclass, field


@dataclass
class PiiCase:
    name: str
    text: str
    pii: set[str] = field(default_factory=set)


CASES: list[PiiCase] = [
    # ---- RUT en varios formatos ----
    PiiCase(
        name="rut_con_puntos_guion",
        text="El arrendatario con RUT 12.345.678-9 firmó el contrato.",
        pii={"12.345.678-9"},
    ),
    PiiCase(
        name="rut_sin_puntos",
        text="Cliente RUT 9.876.543-2 al día con sus pagos.",
        pii={"9.876.543-2"},
    ),
    PiiCase(
        name="rut_con_k",
        text="El representante legal, RUT 7.654.321-K, autoriza la operación.",
        pii={"7.654.321-K"},
    ),
    PiiCase(
        name="rut_multiple",
        text="Comparecen don 11.111.111-1 y doña 22.222.222-2 ante notario.",
        pii={"11.111.111-1", "22.222.222-2"},
    ),
    # ---- Correos ----
    PiiCase(
        name="email_simple",
        text="Cualquier consulta escribir a ana.perez@estudiojuridico.cl.",
        pii={"ana.perez@estudiojuridico.cl"},
    ),
    PiiCase(
        name="email_con_subdominio",
        text="Notificaciones a soporte@mail.contadores.com quedan registradas.",
        pii={"soporte@mail.contadores.com"},
    ),
    # ---- Teléfonos chilenos ----
    PiiCase(
        name="telefono_movil_formato",
        text="Llamar al +56 9 8765 4321 para coordinar la reunión.",
        pii={"+56 9 8765 4321"},
    ),
    PiiCase(
        name="telefono_movil_junto",
        text="Su celular de contacto es +56987654321.",
        pii={"+56987654321"},
    ),
    # ---- Mixtos (caso realista) ----
    PiiCase(
        name="ficha_completa",
        text=(
            "Asegurado: Juan Soto, RUT 8.888.888-8, correo juan.soto@gmail.com, "
            "teléfono +56 9 1234 5678. Póliza vigente."
        ),
        pii={"8.888.888-8", "juan.soto@gmail.com", "+56 9 1234 5678"},
    ),
    # ---- Negativos: NO debe redactar ----
    PiiCase(
        name="negativo_montos_fechas",
        text="La renta es $650.000 con reajuste el 01/03/2026 según IPC.",
        pii=set(),
    ),
    PiiCase(
        name="negativo_numero_articulo",
        text="Conforme al artículo 1.545 del Código Civil, lo pactado obliga.",
        pii=set(),
    ),
    PiiCase(
        name="negativo_texto_simple",
        text="El contrato regula el término anticipado y las garantías.",
        pii=set(),
    ),
]
