"""
Stage 04b / 10 — turn the shortlist into something a person can order.

Joins every candidate back to its ZINC identifier, queries ZINC for vendor
availability, and emits one dossier per compound carrying the whole evidence chain:
docking score, ADMET profile, retrosynthetic route, and where to buy it.

    python make_dossier.py shortlist.json -o dossier.json --top 25

Why the join is needed: fetch_zinc.py kept only the SMILES column when merging tranches
and dropped zinc_id, so the screen results have no vendor handle. The cached tranche
files still carry both, so the mapping is recoverable — but the fetcher now keeps the id.

Nothing here is a purchase. It produces the list a human checks and then orders.
"""
import argparse, json, sys, time, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).parent
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def zinc_id_map(cache_dir, wanted):
    """SMILES -> ZINC id, by scanning the cached tranche files."""
    found, wanted = {}, set(wanted)
    for p in sorted(Path(cache_dir).glob("*.smi")):
        with p.open(errors="replace") as fh:
            for i, line in enumerate(fh):
                if i == 0:
                    continue
                parts = line.split()
                if len(parts) >= 2 and parts[0] in wanted:
                    found[parts[0]] = parts[1]
                    if len(found) == len(wanted):
                        return found
    return found


def zinc_lookup(zid, timeout=25):
    """Vendor and purchasability for one ZINC id. None if the lookup fails."""
    padded = "ZINC" + str(zid).zfill(12)
    url = f"https://zinc20.docking.org/substances/{padded}.json"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
        return {
            "zinc_id": padded,
            "url": f"https://zinc20.docking.org/substances/{padded}/",
            "purchasability": d.get("purchasability"),
            "features": d.get("features"),
            "tranche": d.get("tranche_name"),
        }
    except urllib.error.HTTPError as e:
        return {"zinc_id": padded, "url": f"https://zinc20.docking.org/substances/{padded}/",
                "lookup_error": f"HTTP {e.code}"}
    except Exception as e:
        return {"zinc_id": padded, "url": f"https://zinc20.docking.org/substances/{padded}/",
                "lookup_error": str(e)[:80]}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("shortlist")
    ap.add_argument("-o", "--out", default="dossier.json")
    ap.add_argument("--routes", default="routes.json")
    ap.add_argument("--cache", default="work/zinc_K")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--no-lookup", action="store_true", help="skip the ZINC web query")
    args = ap.parse_args()

    rows = json.loads(Path(args.shortlist).read_text())[:args.top]
    print(f"{len(rows)} candidates\n")

    print("recovering ZINC ids from the tranche cache ...", flush=True)
    ids = zinc_id_map(args.cache, [r["SMILES"] for r in rows])
    print(f"  matched {len(ids)}/{len(rows)}")

    routes = {}
    rp = Path(args.routes)
    if rp.exists():
        for k, v in json.loads(rp.read_text()).items():
            if "SMILES" in v:
                routes[v["SMILES"]] = v

    out = []
    for i, r in enumerate(rows, 1):
        smi = r["SMILES"]
        rec = {
            "rank": i,
            "SMILES": smi,
            "binding": {
                "vina_score": r.get("Vina Score"),
                "poses": r.get("Vina Poses"),
            },
            "properties": {
                "MW": r.get("Molecular Weight"),
                "formula": r.get("Molecular Formula"),
                "rotatable_bonds": r.get("Rotatable Bonds"),
            },
            "admet": {k: r[k] for k in
                      ("DILI", "hERG", "ClinTox", "AMES", "QED",
                       "Bioavailability_Ma", "Carcinogens_Lagunin", "logP", "TPSA")
                      if k in r},
        }
        if smi in routes:
            q = routes[smi]
            rec["route"] = {k: q[k] for k in
                            ("stock_fraction", "precursors", "precursors_in_stock",
                             "n_steps", "top_score", "not_in_stock") if k in q}
        if smi in ids:
            rec["source"] = {"zinc_id_raw": ids[smi]}
            if not args.no_lookup:
                rec["source"].update(zinc_lookup(ids[smi]))
                time.sleep(0.5)          # be polite
        out.append(rec)

    json.dump(out, open(args.out, "w"), indent=2)

    print(f"\n{'#':>3} {'vina':>7} {'MW':>6} {'QED':>5} {'ClinTx':>7} {'route':>7}  ZINC")
    print("-" * 74)
    for r in out:
        src = r.get("source", {})
        rt = r.get("route", {})
        print(f"{r['rank']:>3} {r['binding']['vina_score']:>7.2f} "
              f"{r['properties']['MW']:>6.1f} "
              f"{r['admet'].get('QED', float('nan')):>5.2f} "
              f"{r['admet'].get('ClinTox', float('nan')):>7.2f} "
              f"{(str(int(rt['stock_fraction']*100))+'%') if rt.get('stock_fraction') is not None else '-':>7}  "
              f"{src.get('zinc_id', '(unmatched)')}")
    print(f"\nwrote {args.out}")
    matched = sum(1 for r in out if r.get("source", {}).get("zinc_id"))
    print(f"{matched} of {len(out)} have a ZINC identifier and a vendor page to check.")


if __name__ == "__main__":
    main()
