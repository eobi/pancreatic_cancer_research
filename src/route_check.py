"""
Stage 04 — can this molecule actually be made?

Retrosynthesis with AiZynthFinder: search backwards from the target to commercially
available building blocks. Returns a route tree, or nothing.

ORDER MATTERS. Retrosynthesis asks "if this molecule existed, what reactions would
assemble it" — it never asks whether the product is stable. Measured on the three 2025
structures that a year of lab work failed on, it proposes clean routes:

    Adagrasib (marketed)   71% of precursors in stock, 6 steps
    Hit 41    (impossible) 80% of precursors in stock, 6 steps

A triazane that decomposes on formation still has a valid formal disconnection. So this
stage CANNOT tell makeable from impossible, and running it alone reproduces the 2025
failure with more confidence attached.

    Stage 03 (prepare_ligands.py) asks: can this molecule exist?
    Stage 04 (this file)          asks: given that it exists, how do we make it?

This script therefore refuses to run on anything that has not passed the gate.

    python route_check.py work/route_validation.json -o routes.json

Like every other filter here, it is validated against molecules with known answers:
POSITIVE entries are approved drugs and MUST return routes; NEGATIVE entries are the
2025 structures a year of lab work failed on and SHOULD NOT return clean routes. A tool
that cannot tell those apart is not measuring reality.
"""
import argparse, json, time, sys
from pathlib import Path

HERE = Path(__file__).parent
CONFIG = HERE / "work" / "azf" / "config.yml"


def solve(finder, smiles):
    """Run the retrosynthesis search on one target.

    Returns graded evidence, not a boolean. `is_solved` requires EVERY precursor to be
    in the stock catalogue, which is too strict to be useful: Sotorasib — a marketed
    drug — comes back is_solved=False with 5 of 6 precursors in stock, because one
    intermediate is not in ZINC. What actually matters is how much of the route lands
    on purchasable material, and whether a route exists at all.
    """
    finder.target_smiles = smiles
    t0 = time.time()
    finder.tree_search()
    finder.build_routes()
    elapsed = time.time() - t0

    st = finder.extract_statistics()
    n_prec = int(st.get("number_of_precursors") or 0)
    in_stock = int(st.get("number_of_precursors_in_stock") or 0)
    return {
        "fully_solved": bool(st.get("is_solved", False)),
        "stock_fraction": round(in_stock / n_prec, 3) if n_prec else 0.0,
        "precursors": n_prec,
        "precursors_in_stock": in_stock,
        "not_in_stock": st.get("precursors_not_in_stock", ""),
        "top_score": round(float(st.get("top_score") or 0.0), 4),
        "n_steps": int(st.get("number_of_steps") or 0),
        "n_routes": int(st.get("number_of_routes") or 0),
        "search_seconds": round(elapsed, 1),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("molecules", help="JSON: {name: SMILES}, or a list of SMILES")
    ap.add_argument("-o", "--out", default="routes.json")
    ap.add_argument("--config", default=str(CONFIG))
    ap.add_argument("--time-limit", type=int, default=120, help="seconds per molecule")
    ap.add_argument("--skip-gate", action="store_true",
                    help="run route search without the stage-03 gate. Only for validation "
                         "runs that deliberately include impossible molecules.")
    ap.add_argument("--covalent", action="store_true", default=True,
                    help="exempt Michael acceptors (covalent programme)")
    args = ap.parse_args()

    if not Path(args.config).exists():
        sys.exit(f"no config at {args.config} — run download_public_data into work/azf first")

    data = json.loads(Path(args.molecules).read_text())
    if isinstance(data, list):
        data = {f"mol {i+1}": s for i, s in enumerate(data)}

    # --- stage 03 must pass first ------------------------------------------
    # Retrosynthesis is blind to whether the target can exist. Gate first, always.
    if not args.skip_gate:
        sys.path.insert(0, str(HERE))
        import prepare_ligands as gate_mod
        gate_mod._init(args.covalent)
        blocked = {}
        for name, smi in list(data.items()):
            if name.startswith("NEGATIVE"):
                continue                      # validation set: keep deliberately
            why = gate_mod.gate(smi)
            if why:
                blocked[name] = why
                data.pop(name)
        if blocked:
            print(f"{len(blocked)} molecule(s) rejected by the chemical reality gate "
                  f"before any route search:")
            for n, w in blocked.items():
                print(f"  {n[:44]:<46} {w}")
            print()

    from aizynthfinder.aizynthfinder import AiZynthFinder
    finder = AiZynthFinder(configfile=args.config)
    finder.stock.select("zinc")
    finder.expansion_policy.select("uspto")
    finder.filter_policy.select("uspto") if "uspto" in finder.filter_policy.items else None
    finder.config.search.time_limit = args.time_limit

    print(f"{len(data)} molecules | {args.time_limit}s search limit each\n")
    results = {}
    for name, smi in data.items():
        print(f"  {name[:44]:<46}", end="", flush=True)
        try:
            r = solve(finder, smi)
        except Exception as e:
            print(f"ERROR {str(e)[:40]}")
            results[name] = {"solved": False, "error": str(e)[:200], "SMILES": smi}
            continue
        r["SMILES"] = smi
        results[name] = r
        print(f"stock {r['precursors_in_stock']}/{r['precursors']} "
              f"({r['stock_fraction']:.0%})  score {r['top_score']:.2f}  "
              f"{r['n_steps']} steps  ({r['search_seconds']}s)")

    json.dump(results, open(args.out, "w"), indent=2)

    # --- validation summary: did it get the known answers right? ------------
    pos = {k: v for k, v in results.items() if k.startswith("POSITIVE")}
    neg = {k: v for k, v in results.items() if k.startswith("NEGATIVE")}
    if pos and neg:
        pf = [v["stock_fraction"] for v in pos.values() if "stock_fraction" in v]
        nf = [v["stock_fraction"] for v in neg.values() if "stock_fraction" in v]
        print("\nvalidation — stock fraction of the retrosynthetic route:")
        for k, v in list(pos.items()) + list(neg.items()):
            if "stock_fraction" not in v:
                print(f"  {k[:46]:<48} ERROR"); continue
            print(f"  {k[:46]:<48} {v['stock_fraction']:>6.0%}  "
                  f"({v['precursors_in_stock']}/{v['precursors']} precursors, "
                  f"{v['n_steps']} steps)")
        if pf and nf:
            print(f"\n  approved drugs   : {min(pf):.0%} - {max(pf):.0%}")
            print(f"  2025 'impossible': {min(nf):.0%} - {max(nf):.0%}")
            gap = min(pf) - max(nf)
            if gap > 0:
                print(f"\n  SEPARATED by {gap:.0%}. Gate at stock_fraction >= {max(nf) + gap/2:.0%}.")
            else:
                print("\n  NOT SEPARATED — this measure cannot tell the two groups apart.")
                print("  Do not gate on it. Report the route and let a chemist judge.")

    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
