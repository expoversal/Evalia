"""Build the prototype interface: run the pipeline and embed its output in one self-contained HTML page.

With no arguments it runs on the fictional documents in tests/fixtures/synthetic and writes
build/evalia-prototype.html. For any other documents, the output must go inside the
folder named by EVALIA_DATA_DIR, so that a real engagement's results never land in the
repository.

    python scripts/make_synthetic_tender.py
    python scripts/build_demo.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from packs.construction.pipeline import run  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "synthetic"
UI = ROOT / "app" / "ui"


def build(data: dict) -> str:
    page = (UI / "index.html").read_text()
    app = (UI / "app.js").read_text()
    blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    return page.replace("/*DATA*/null", blob).replace("/*APP*/", app)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rfp", type=Path, default=next(FIX.glob("rfp_*.pdf"), None))
    ap.add_argument("--tender", type=Path, action="append")
    ap.add_argument("--receipts", type=Path, default=FIX / "receipts.yaml")
    ap.add_argument("--out", type=Path, default=ROOT / "build" / "evalia-prototype.html")
    a = ap.parse_args()
    tenders = a.tender or sorted(FIX.glob("tender_*.pdf"), key=lambda p: ["northfield", "cobalt", "harborpine"].index(p.stem[7:])
                                  if p.stem[7:] in ("northfield", "cobalt", "harborpine") else 99)
    inputs = [a.rfp, a.receipts, *tenders]
    if not all(p.resolve().is_relative_to(FIX) for p in inputs):
        data_dir = os.environ.get("EVALIA_DATA_DIR")
        if not data_dir or not a.out.resolve().is_relative_to(Path(data_dir).resolve()):
            sys.exit("Refused: these are not the fictional fixtures, so --out must be inside EVALIA_DATA_DIR.")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(build(run(a.rfp, tenders, a.receipts)))
    print(f"Wrote {a.out}")


if __name__ == "__main__":
    main()
