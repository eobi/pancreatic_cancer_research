"""
Gate coverage: what fraction of the properties a pipeline computes can actually stop it?

A pipeline that computes ten properties and gates on one has gate coverage 0.10. It sees
almost everything and can act on almost nothing. That is the failure this project
documents: the campaign audited here computed an `Epoxide Ring Present` column, set it True
on all three molecules it sent to synthetic chemists, and shipped them, because the column
fed a report and not a decision.

    coverage = (properties wired to a halt decision) / (properties computed)

The metric is deliberately crude. Its value is that it is computable from a methods section
or an output file, so it can be applied at scale across published work rather than argued
about one pipeline at a time.

    python gate_coverage.py --file data/raw/source-cross_docked_kras.xlsx --gated "docking"
    python gate_coverage.py --computed 9 --gated 1 --label "Campaign X"
"""
import argparse, json, sys
from pathlib import Path

# Column-name fragments that denote a computed molecular property, not an identifier.
PROPERTY_HINTS = [
    "pains", "ames", "qed", "lipinski", "logp", "tpsa", "bbb", "clintox",
    "carcinogen", "bioavail", "hydrogen bond", "accessibility", "epoxide",
    "toxic", "herg", "dili", "solub", "weight", "affinity", "confidence",
    "docking", "score", "mutagen",
]
ID_HINTS = ["molecule", "name", "id", "smiles", "formula", "index"]


def properties_in(path):
    import pandas as pd
    df = pd.read_excel(path) if str(path).endswith((".xlsx", ".xls")) else pd.read_csv(path)
    props = []
    for c in df.columns:
        lc = str(c).lower()
        if any(h in lc for h in ID_HINTS) and not any(h in lc for h in PROPERTY_HINTS):
            continue
        if any(h in lc for h in PROPERTY_HINTS):
            props.append(str(c))
    return props, list(df.columns)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", help="pipeline output file (xlsx/csv)")
    ap.add_argument("--gated", default="",
                    help="comma-separated fragments naming the properties that COULD halt "
                         "the pipeline (from the methods section, not the file)")
    ap.add_argument("--computed", type=int, help="manual count of computed properties")
    ap.add_argument("--gated-count", type=int, help="manual count of gating properties")
    ap.add_argument("--label", default="pipeline")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()

    if a.computed is not None and a.gated_count is not None:
        props, gated = [f"p{i}" for i in range(a.computed)], [f"g{i}" for i in range(a.gated_count)]
        allcols = props
    elif a.file:
        props, allcols = properties_in(a.file)
        frags = [f.strip().lower() for f in a.gated.split(",") if f.strip()]
        gated = [p for p in props if any(f in p.lower() for f in frags)]
    else:
        sys.exit("give --file, or --computed with --gated-count")

    n_c, n_g = len(props), len(gated)
    cov = n_g / n_c if n_c else 0.0
    print(f"  {a.label}")
    print(f"    columns in file            {len(allcols)}")
    print(f"    properties computed        {n_c}")
    print(f"    properties able to halt    {n_g}   {gated}")
    print(f"    GATE COVERAGE              {cov:.2f}")
    print()
    print(f"    computed but inert ({n_c - n_g}):")
    for p in props:
        if p not in gated:
            print(f"      - {p}")

    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        json.dump({"label": a.label, "computed": n_c, "gating": n_g,
                   "coverage": round(cov, 3), "gated": gated,
                   "inert": [p for p in props if p not in gated]},
                  open(a.out, "w"), indent=2)
        print(f"\n  wrote {a.out}")


if __name__ == "__main__":
    main()
