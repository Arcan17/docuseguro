"""Integra el harness de evals a la suite: la calidad de PII no debe regresar."""
from app.services.privacy.scrubber import PIIScrubber
from evals.pii_dataset import CASES
from evals.run_pii_eval import F1_THRESHOLD, _evaluate_case


def test_pii_eval_meets_threshold() -> None:
    scrubber = PIIScrubber()
    tp = fp = fn = 0
    for case in CASES:
        c_tp, c_fp, c_fn, _ = _evaluate_case(scrubber, case)
        tp += c_tp
        fp += c_fp
        fn += c_fn
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    assert f1 >= F1_THRESHOLD, f"F1 {f1:.3f} bajo el umbral {F1_THRESHOLD}"


def test_pii_eval_no_leaks_on_labeled_pii() -> None:
    """Ningún dato personal etiquetado debe filtrarse (recall por caso = 1)."""
    scrubber = PIIScrubber()
    for case in CASES:
        _tp, _fp, _fn, leaks = _evaluate_case(scrubber, case)
        assert not leaks, f"Fuga en {case.name}: {leaks}"
