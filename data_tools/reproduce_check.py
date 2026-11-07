#!/usr/bin/env python3
"""Generate twice with identical settings and compare file hashes/row counts."""

import argparse, hashlib, json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def hashes(folder):
    result = {}
    for p in sorted(Path(folder).glob("*")):
        if p.is_file():
            result[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", choices=["starter", "full"], default="starter")
    ap.add_argument("--seed", type=int, default=20261022)
    ap.add_argument("--out", default="reproducibility")
    a = ap.parse_args()
    dest = Path(a.out).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as t:
        one = Path(t) / "one"
        two = Path(t) / "two"
        for folder in [one, two]:
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "generate_dataset.py"),
                    "--scale",
                    a.scale,
                    "--seed",
                    str(a.seed),
                    "--out",
                    str(folder),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
            )
        h1, h2 = hashes(one), hashes(two)
        ok = h1 == h2
        report = {
            "status": "PASS" if ok else "FAIL",
            "scale": a.scale,
            "seed": a.seed,
            "identical_file_hashes": ok,
            "first_hashes": h1,
            "second_hashes": h2,
        }
        (dest / "reproducibility_report.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "scale": a.scale,
                    "seed": a.seed,
                    "files_compared": len(h1),
                    "identical_file_hashes": ok,
                },
                indent=2,
            )
        )
        raise SystemExit(0 if ok else 1)
