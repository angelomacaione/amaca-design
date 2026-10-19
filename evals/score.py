#!/usr/bin/env python3
"""score.py — Layer A of the model fidelity protocol (evals/PROTOCOL.md § 3).

Runs the skill bundle's own verifier, scripts/verify-output.py, against one
or more generated HTML files, and maps every finding to the law it breaks.
The verifier is read from downloads/amaca-frontend.zip, the bundle that
ships, so the grade is always against the spec the model was given. Nothing
here re-types a token, a class or a law: the closed lists stay in the bundle.

Usage:  python3 evals/score.py <output.html | run-dir> [...]
        A run dir is scored file by file (every *.html in it).
Prints one line per file and a JSON record per file to stdout with --json.
Exit 0 always: a failing output is a score, not an error.
"""
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "downloads" / "amaca-frontend.zip"

# finding text -> law id (DESIGN.md § Law). Order matters: first match wins.
LAW_OF = [
    (r"emoji", "L6"),
    (r"ease-spring", "L8"),
    (r"prefers-reduced-motion", "L7"),
    (r"one primary", "L3"),
    (r"focus-visible", "L2"),
    (r"component registry", "REG"),
    (r"invented token|raw hex|exact token|raw duration|z-index", "L4"),
]


def law(finding):
    for pat, lid in LAW_OF:
        if re.search(pat, finding):
            return lid
    return "OTHER"


def verifier_dir(tmp):
    with zipfile.ZipFile(BUNDLE) as z:
        z.extractall(tmp)
    hits = list(Path(tmp).rglob("scripts/verify-output.py"))
    if not hits:
        sys.exit(f"verify-output.py not found inside {BUNDLE.name}")
    return hits[0]


def score(verifier, html):
    r = subprocess.run([sys.executable, "-I", str(verifier), str(html)],
                       capture_output=True, text=True)
    findings = re.findall(r"\[FAIL\] (.+)", r.stdout)
    by_law = {}
    for f in findings:
        by_law[law(f)] = by_law.get(law(f), 0) + 1
    return {"file": str(html), "a_pass": r.returncode == 0,
            "a_findings": len(findings), "by_law": by_law, "findings": findings}


def main(argv):
    as_json = "--json" in argv
    targets = [Path(a) for a in argv if a != "--json"]
    if not targets:
        print(__doc__)
        return 2
    files = []
    for t in targets:
        files += sorted(t.glob("*.html")) if t.is_dir() else [t]
    with tempfile.TemporaryDirectory() as tmp:
        verifier = verifier_dir(tmp)
        rows = [score(verifier, f) for f in files]
    for row in rows:
        if as_json:
            print(json.dumps(row))
        else:
            laws = " ".join(f"{k}:{v}" for k, v in sorted(row["by_law"].items())) or "-"
            verdict = "PASS" if row["a_pass"] else "FAIL"
            print(f"{verdict}  {row['a_findings']:>3}  {laws:<24} {row['file']}")
    if not as_json and rows:
        passed = sum(r["a_pass"] for r in rows)
        print(f"\nA-pass {passed}/{len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
