"""Harness de evaluación del borrado de PII.

Corre offline (sin LLM ni red): usa solo el PIIScrubber con regex locales.
Mide precision / recall / F1 sobre un dataset etiquetado y muestra un reporte.

Uso:
    python -m evals.run_pii_eval

Sale con código != 0 si el F1 cae por debajo del umbral (apto para CI).
"""

import sys

from app.services.privacy.scrubber import PIIScrubber
from evals.pii_dataset import CASES, PiiCase

F1_THRESHOLD = 0.90


def _evaluate_case(scrubber: PIIScrubber, case: PiiCase) -> tuple[int, int, int, set[str]]:
    _clean, token_map, _types = scrubber.scrub(case.text)
    caught = set(token_map.values())
    expected = case.pii
    tp = len(caught & expected)
    fp = len(caught - expected)
    fn = len(expected - caught)
    leaks = expected - caught
    return tp, fp, fn, leaks


def main() -> int:
    scrubber = PIIScrubber()
    total_tp = total_fp = total_fn = 0
    rows: list[tuple[str, str, str]] = []

    for case in CASES:
        tp, fp, fn, leaks = _evaluate_case(scrubber, case)
        total_tp += tp
        total_fp += fp
        total_fn += fn
        status = "OK" if fp == 0 and fn == 0 else "FALLA"
        detail = ""
        if leaks:
            detail = "fuga: " + ", ".join(sorted(leaks))
        elif fp:
            detail = f"sobre-redacción x{fp}"
        rows.append((status, case.name, detail))

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 1.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    print("\n  EVALUACIÓN DE BORRADO DE PII")
    print("  " + "=" * 46)
    for status, name, detail in rows:
        mark = "✓" if status == "OK" else "✗"
        line = f"  {mark} {name:<28} {detail}"
        print(line.rstrip())
    print("  " + "-" * 46)
    print(f"  Casos:      {len(CASES)}")
    print(f"  TP {total_tp}  ·  FP {total_fp}  ·  FN {total_fn}")
    print(f"  Precision:  {precision:.3f}")
    print(f"  Recall:     {recall:.3f}")
    print(f"  F1:         {f1:.3f}   (umbral {F1_THRESHOLD})")
    print("  " + "=" * 46)

    if f1 < F1_THRESHOLD:
        print(f"  ✗ F1 {f1:.3f} bajo el umbral {F1_THRESHOLD}\n")
        return 1
    print("  ✓ Calidad de borrado sobre el umbral\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
