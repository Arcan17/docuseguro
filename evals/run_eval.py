"""
PrivRAG Evaluation Suite
========================
Runs golden questions against the live API and measures:
  - Retrieval hit rate (chunk_count > 0 when expected)
  - PII detection accuracy (pii_found + pii_types)
  - No-context rejection rate (chunk_count == 0 when expected)
  - Cache hit rate (cache_hit when expected)
  - Keyword presence in answer

Usage:
    # Against local deployment
    python evals/run_eval.py

    # Against Railway demo
    python evals/run_eval.py --base-url https://privrag-production.up.railway.app

    # Save results
    python evals/run_eval.py --out evals/results.md
"""

import argparse
import json
import time
from pathlib import Path

import httpx

GOLDEN_FILE = Path(__file__).parent / "golden_questions.json"
SESSION_BASE = "00000000-0000-0000-0000-"
TIMEOUT = 30.0


def run_eval(base_url: str, out_path: str | None = None) -> None:
    questions = json.loads(GOLDEN_FILE.read_text())

    print(f"PrivRAG Eval — {base_url}")
    print(f"Questions: {len(questions)}\n")
    print("-" * 70)

    results = []
    passed = 0
    failed = 0

    for i, q in enumerate(questions):
        session_id = SESSION_BASE + str(i + 1).zfill(12)
        payload = {"query": q["question"], "session_id": session_id}

        t0 = time.monotonic()
        try:
            resp = httpx.post(f"{base_url}/query", json=payload, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[{q['id']}] ERROR: {e}")
            failed += 1
            continue

        latency = int((time.monotonic() - t0) * 1000)

        checks = []

        # 1. Context check
        if q.get("should_have_context"):
            ok = data.get("chunk_count", 0) > 0
            checks.append(("context_found", ok, f"chunk_count={data.get('chunk_count', 0)}"))
        else:
            ok = data.get("chunk_count", 0) == 0
            checks.append(("no_context_rejected", ok, f"chunk_count={data.get('chunk_count', 0)}"))

        # 2. PII check
        if q.get("pii_in_query"):
            pii_ok = data.get("pii_found", False)
            checks.append(("pii_detected", pii_ok, f"pii_types={data.get('pii_types', [])}"))
            if q.get("expected_pii_types"):
                for ptype in q["expected_pii_types"]:
                    type_ok = ptype in data.get("pii_types", [])
                    checks.append((f"pii_type_{ptype}", type_ok, ""))

        # 3. Cache hit check
        if q.get("expect_cache_hit"):
            cache_ok = data.get("cache_hit", False)
            checks.append(("cache_hit", cache_ok, f"latency={latency}ms"))

        # 4. Keyword check
        answer = data.get("answer", "").lower()
        for kw in q.get("expected_keywords", []):
            kw_ok = kw.lower() in answer
            checks.append((f"keyword_{kw}", kw_ok, ""))

        all_pass = all(c[1] for c in checks)
        status = "✅ PASS" if all_pass else "❌ FAIL"
        if all_pass:
            passed += 1
        else:
            failed += 1

        print(f"{status}  [{q['id']}]  {latency}ms")
        for name, ok, detail in checks:
            icon = "  ✓" if ok else "  ✗"
            print(f"       {icon} {name}" + (f"  ({detail})" if detail else ""))

        results.append({
            "id": q["id"],
            "question": q["question"],
            "passed": all_pass,
            "latency_ms": latency,
            "checks": [{"name": c[0], "passed": c[1], "detail": c[2]} for c in checks],
            "answer_preview": data.get("answer", "")[:120],
        })

    print("-" * 70)
    print(f"\nResults: {passed}/{len(questions)} passed  ({100*passed//len(questions)}%)")
    print(f"  Pass: {passed}  |  Fail: {failed}")

    if out_path:
        _write_markdown(results, passed, len(questions), out_path)
        print(f"\nSaved: {out_path}")


def _write_markdown(results: list, passed: int, total: int, path: str) -> None:
    lines = [
        "# PrivRAG Eval Results\n",
        f"**Score: {passed}/{total} ({100*passed//total}%)**\n\n",
        "| ID | Pass | Latency | Checks |\n",
        "|----|----|---------|--------|\n",
    ]
    for r in results:
        icon = "✅" if r["passed"] else "❌"
        check_str = " ".join("✓" if c["passed"] else "✗" for c in r["checks"])
        lines.append(f"| {r['id']} | {icon} | {r['latency_ms']}ms | `{check_str}` |\n")
    Path(path).write_text("".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    run_eval(args.base_url, args.out)
