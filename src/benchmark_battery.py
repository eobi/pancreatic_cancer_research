"""
Can the molecules a generative model proposes actually be made?

A benchmark, not a case study. The question is usually asked of one model's output at a
time, with a bespoke filter, which makes results incomparable. This applies ONE battery of
UNMODIFIED published filters to the released outputs of many published models, plus two
reference arms that bound the scale:

  upper bound   purchasable compounds (a vendor ships them, so they can be made)
  ground truth  one campaign whose molecules went to synthetic chemists and were not made

The filters are BRENK and PAINS exactly as shipped in RDKit. No exemptions, no tuning. That
matters: a filter tuned by us would make the separation we report an artefact of our own
choices rather than a property of the molecules.

    python benchmark_battery.py -o results/benchmark_battery.json
"""
import argparse, glob, json, os
import multiprocessing as mp
from rdkit import Chem, RDLogger
from rdkit.Chem import FilterCatalog, Descriptors
RDLogger.DisableLog("rdApp.*")

_c = {}


def _init():
    p = FilterCatalog.FilterCatalogParams()
    p.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.BRENK)
    p.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS)
    _c["cat"] = FilterCatalog.FilterCatalog(p)


def check(smi):
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return None
    return (not _c["cat"].HasMatch(m),
            any(a.GetIsAromatic() for a in m.GetAtoms()),
            m.GetRingInfo().NumRings() > 0,
            Descriptors.MolWt(m))


def run(name, smis, workers=8):
    with mp.Pool(workers, initializer=_init) as pool:
        r = [x for x in pool.map(check, smis, chunksize=500) if x]
    n = len(r)
    if not n:
        return None
    return {"model": name, "n": n,
            "parse_fail": len(smis) - n,
            "pass_pct": round(100 * sum(x[0] for x in r) / n, 2),
            "aromatic_pct": round(100 * sum(x[1] for x in r) / n, 2),
            "ring_pct": round(100 * sum(x[2] for x in r) / n, 2),
            "median_mw": round(sorted(x[3] for x in r)[n // 2], 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="results/benchmark_battery.json")
    ap.add_argument("--limit", type=int, default=30000)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()

    out = []
    hdr = f"  {'set':<18} {'n':>7} {'pass%':>7} {'aromatic%':>10} {'ring%':>7} {'medMW':>7}"
    print(hdr); print("  " + "-" * (len(hdr) - 2), flush=True)

    for f in sorted(glob.glob("data/benchmark/*.csv")):
        name = os.path.basename(f)[:-4]
        smis = [l.split(",")[0].strip() for l in open(f).read().splitlines()[1:] if l.strip()]
        smis = [s for s in smis if s and not s[0].isdigit()][:a.limit]
        r = run(name, smis, a.workers)
        if r:
            out.append(r)
            print(f"  {r['model']:<18} {r['n']:>7} {r['pass_pct']:>7.1f} "
                  f"{r['aromatic_pct']:>10.1f} {r['ring_pct']:>7.1f} {r['median_mw']:>7.1f}", flush=True)

    import pandas as pd
    d = pd.read_excel("data/raw/source-cross_docked_kras.xlsx")
    names = d["Hit Molecule"].astype(str).tolist()
    gen = [str(s) for s, n in zip(d["SMILES"], names)
           if not any(k in n.lower() for k in ("sotorasib", "adagrasib"))]
    r = run("OUR-CAMPAIGN", gen, a.workers); out.append(r)
    print(f"  {r['model']:<18} {r['n']:>7} {r['pass_pct']:>7.1f} "
          f"{r['aromatic_pct']:>10.1f} {r['ring_pct']:>7.1f} {r['median_mw']:>7.1f}", flush=True)

    lig = json.load(open("data/gated/ligands.json"))
    if isinstance(lig, dict):
        lig = list(lig.values())
    smis = [(x if isinstance(x, str) else x.get("SMILES")) for x in lig[:a.limit]]
    r = run("PURCHASABLE", [s for s in smis if s], a.workers); out.append(r)
    print(f"  {r['model']:<18} {r['n']:>7} {r['pass_pct']:>7.1f} "
          f"{r['aromatic_pct']:>10.1f} {r['ring_pct']:>7.1f} {r['median_mw']:>7.1f}", flush=True)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=2)
    print(f"\n  wrote {a.out}")


if __name__ == "__main__":
    main()
