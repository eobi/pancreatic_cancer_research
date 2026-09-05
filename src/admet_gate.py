"""
ADMET on the docking shortlist — as a gate, not an annotation.

The 2025 pipeline computed the same panel and wrote it into a report as columns to read.
Its shortlist carried a median predicted mutagenicity of 0.93 and nothing stopped. This
applies thresholds that reject, records which one fired, and reports what survives.

    python admet_gate.py top200.json -o shortlist.json

Thresholds are deliberately conservative for a first pass and every one is stated below
with its reason. Loosen them explicitly, in this file, rather than by ignoring output.
"""
import argparse, json, sys
from pathlib import Path

# --- gates -----------------------------------------------------------------
# CALIBRATED AGAINST THE CONTROLS, NOT AGAINST INVENTED NUMBERS.
#
# A first pass used textbook cutoffs (DILI<0.70, hERG<0.70) and rejected 199 of 200
# compounds. Checking the gate against the drugs it should obviously pass showed why:
#
#     BI-0474    DILI 0.96   hERG 0.89   ClinTox 0.43   AMES 0.49
#     Sotorasib  DILI 0.99   hERG 0.72   ClinTox 0.22   AMES 0.11
#     Adagrasib  DILI 0.83   hERG 0.96   ClinTox 0.75   AMES 0.30
#
# Sotorasib and Adagrasib are marketed drugs and both fail DILI and hERG outright.
# Oncology drugs *are* hepatotoxic and hERG-flagged; Sotorasib carries a hepatotoxicity
# warning on its label. In this chemical space those two heads do not discriminate, so
# using them as gates only throws away the right answer.
#
# Rule adopted: a gate must pass every approved control. Anything that does not is
# demoted to informational. Thresholds below are set with headroom over the worst
# control value, so a compound is only rejected for being worse than a marketed drug.
#
# (key, direction, threshold, why). "max" rejects above, "min" rejects below.
GATES = [
    ("AMES",                 "max", 0.60,
     "predicted mutagenic; worst control (BI-0474) is 0.49"),
    ("Carcinogens_Lagunin",  "max", 0.50,
     "predicted carcinogen; worst control is 0.16, so this stays strict"),
    ("ClinTox",              "max", 0.85,
     "clinical-trial toxicity; worst control (Adagrasib) is 0.75"),
    ("Bioavailability_Ma",   "min", 0.30,
     "oral bioavailability; worst control (BI-0474) is 0.66"),
    ("QED",                  "min", 0.30,
     "drug-likeness; Sotorasib and Adagrasib both sit at 0.36"),
]

# Reported, never used to reject. DILI and hERG are here because every approved control
# fails them — they carry no signal in oncology space and must not gate.
INFORMATIONAL = ["DILI", "hERG", "logP", "TPSA", "HIA_Hou", "BBB_Martins", "Lipinski",
                 "Solubility_AqSolDB", "hydrogen_bond_acceptors",
                 "hydrogen_bond_donors", "Caco2_Wang", "PPBR_AZ"]

# Controls the gate is required to pass. Verified on every run; if one fails, the
# thresholds are wrong, not the drug.
CONTROLS_PATH = "work/controls.json"


def find_key(preds, name):
    """ADMET-AI key names shift between releases; match case-insensitively."""
    if name in preds:
        return name
    low = {k.lower(): k for k in preds}
    return low.get(name.lower())


def judge(preds):
    """Return (list of failures, dict of the values that were tested)."""
    failures, tested = [], {}
    for name, direction, thresh, why in GATES:
        k = find_key(preds, name)
        if k is None:
            continue                      # head absent in this model version
        v = preds[k]
        if not isinstance(v, (int, float)):
            continue
        tested[name] = v
        if direction == "max" and v > thresh:
            failures.append(f"{name} {v:.2f} > {thresh} ({why})")
        elif direction == "min" and v < thresh:
            failures.append(f"{name} {v:.2f} < {thresh} ({why})")
    return failures, tested


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("shortlist", help="top200.json from the screen")
    ap.add_argument("-o", "--out", default="shortlist.json")
    ap.add_argument("--report", default="admet_report.csv")
    args = ap.parse_args()

    rows = json.loads(Path(args.shortlist).read_text())
    smiles = [r["SMILES"] for r in rows]
    print(f"{len(smiles)} compounds from {args.shortlist}")

    print("loading ADMET-AI (first run downloads model weights) ...", flush=True)
    from admet_ai import ADMETModel
    model = ADMETModel()

    # --- self-check: the gate must pass drugs known to be developable -------
    ctrl_path = Path(CONTROLS_PATH)
    if ctrl_path.exists():
        controls = json.loads(ctrl_path.read_text())
        cpred = model.predict(smiles=list(controls.values()))
        print("\ncontrol self-check (these MUST pass):")
        bad = []
        for name, smi in controls.items():
            fails, _ = judge(cpred.loc[smi].to_dict())
            print(f"  {name:<11} {'PASS' if not fails else 'FAIL — ' + '; '.join(fails)}")
            if fails:
                bad.append(name)
        if bad:
            sys.exit(f"\nGate rejects {', '.join(bad)}. Fix the thresholds in GATES — "
                     "a filter that rejects an approved drug is measuring the wrong thing.")
        print()

    print("predicting ...", flush=True)
    preds = model.predict(smiles=smiles)     # DataFrame indexed by SMILES

    passed, rejected = [], []
    for r in rows:
        smi = r["SMILES"]
        try:
            p = preds.loc[smi].to_dict()
        except Exception:
            rejected.append({**r, "ADMET failures": ["no prediction returned"]})
            continue
        failures, tested = judge(p)
        rec = {**r, **{k: p[k] for k in p if find_key({k: 1}, k)}, "ADMET tested": tested}
        if failures:
            rejected.append({**rec, "ADMET failures": failures})
        else:
            passed.append(rec)

    passed.sort(key=lambda r: r["Vina Score"])
    json.dump(passed, open(args.out, "w"), indent=2)

    # why things died
    import collections
    reasons = collections.Counter(f.split()[0] for r in rejected
                                  for f in r.get("ADMET failures", []))
    print(f"\n{len(passed)} pass, {len(rejected)} rejected\n")
    for name, n in reasons.most_common():
        why = next((w for k, _, _, w in GATES if k == name), "")
        print(f"  {n:>4}  {name:<22} {why}")

    if passed:
        print(f"\ntop survivors:")
        print(f"{'#':>3} {'score':>7} {'MW':>6}  SMILES")
        for i, r in enumerate(passed[:15], 1):
            print(f"{i:>3} {r['Vina Score']:>7.2f} {r['Molecular Weight']:>6.1f}  {r['SMILES'][:56]}")
    else:
        print("\nNothing survived. Loosen a threshold in GATES deliberately, or accept")
        print("that this shortlist is not developable and go back to the screen.")

    # full CSV for inspection
    import csv
    with open(args.report, "w", newline="") as fh:
        keys = ["SMILES", "Vina Score", "Molecular Weight", "verdict", "failures"]
        w = csv.writer(fh); w.writerow(keys)
        for r in passed:
            w.writerow([r["SMILES"], r["Vina Score"], r["Molecular Weight"], "PASS", ""])
        for r in rejected:
            w.writerow([r["SMILES"], r.get("Vina Score", ""), r.get("Molecular Weight", ""),
                        "REJECT", "; ".join(r.get("ADMET failures", []))])
    print(f"\nwrote {args.out} and {args.report}")


if __name__ == "__main__":
    main()
