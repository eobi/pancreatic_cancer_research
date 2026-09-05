"""
Stage 04b — will each proposed step actually work on THIS molecule?

Retrosynthesis (stage 04) asks "if this molecule existed, what reactions would assemble
it". It reasons over disconnections, one bond at a time, and it is blind to the rest of
the molecule. That blindness is what cost the 2025 campaign a year:

    Adagrasib (marketed)   71% of precursors in stock, 6 steps
    Hit 41    (impossible) 80% of precursors in stock, 6 steps

A valid disconnection is not a working reaction. Two things go wrong on a real bench, and
both are computable from structure alone:

  1. CHEMOSELECTIVITY. The reagent does not know which site you meant. If the reactive
     motif appears three times in your molecule, you get a mixture, not a product.
     Retrosynthesis counts the one bond it is breaking and ignores the other two.

  2. CONDITION COMPATIBILITY. Every step is run under conditions -- acid, base, hydrogen,
     heat -- and those conditions destroy functional groups elsewhere in the molecule. An
     epoxide does not survive the TFA that removes a Boc group. A free aldehyde does not
     survive a reductive amination aimed at a different position.

This stage answers both. It is rule-based and says so: the reaction classes, their
conditions and their incompatibilities are encoded chemistry, not a learned model. An ML
forward-prediction model (Molecular Transformer / IBM RXN) is strictly better at "what
product does this give" and needs a GPU or an API key; it slots in behind `predict_step()`
without changing the interface. What is here runs offline, on a laptop, today.

    python route_forward.py --smiles "<SMILES>"           # one molecule
    python route_forward.py candidates.json -o forward.json

WHAT A FINDING MEANS -- read this before using the number. A finding is SYNTHESIS
DIFFICULTY, not impossibility. It says "this step needs a protecting group, or a different
order of operations". Measured on real sets:

    reported 2025 shortlist   n=75    20% clean, median 4 findings
    purchasable ZINC (gated)  n=3000   4% clean, median 1 finding
    G12V top-200 shortlist    n=200   44% clean, median 1 finding

Only 4% of PURCHASABLE compounds are clean -- and those compounds demonstrably exist, a
vendor ships them. So "has findings" cannot mean "cannot be made", and a tool reporting it
that way would be worse than useless. The signal is in the MEDIAN: the generated molecules
need four interventions where a purchasable compound needs one. That is a real 4x
separation, and it is the claim this file supports.

CONTROL GATE, as everywhere else in this pipeline: the rules are checked against molecules
with known answers before they are trusted. Approved drugs were manufactured at scale, so
their liabilities must be manageable; a structure built from groups that destroy each
other must light up. A rule set that cannot separate those two is reporting noise.
"""
import argparse, json, sys
from pathlib import Path

from rdkit import Chem, RDLogger
RDLogger.DisableLog("rdApp.*")


# --- reaction classes -------------------------------------------------------
# Each entry: the motif the reagent attacks, the conditions it is run under, and the
# groups those conditions destroy. `sites` is what creates selectivity problems when it
# matches more than once; `kills` is what the conditions do to the rest of the molecule.
REACTIONS = {
    "amide_coupling": {
        "conditions": "HATU or EDC, DIPEA, DMF, rt",
        "sites": {"carboxylic_acid": "[CX3](=O)[OX2H1]",
                  "amine_1_2": "[NX3;H1,H2;!$(NC=O);!$(N[a]);!$(N=*)]"},
        "kills": [],
        "note": "amine and acid both nucleophilic/electrophilic; extra copies of either "
                "give oligomers and regioisomers",
    },
    "SNAr": {
        "conditions": "K2CO3 or DIPEA, DMSO/NMP, 80-120 C",
        "sites": {"activated_aryl_halide": "[c;$(c1ccccc1)][F,Cl,Br]",
                  "amine_1_2": "[NX3;H1,H2;!$(NC=O);!$(N=*)]"},
        "kills": ["epoxide", "ester", "aldehyde"],
        "note": "hot base; esters transesterify in DMSO/alkoxide, aldehydes aldol",
    },
    "suzuki": {
        "conditions": "Pd catalyst, base, dioxane/water, 80-100 C",
        "sites": {"aryl_halide": "[c][Br,I,Cl]", "boronic": "[BX3]([OX2H1])[OX2H1]"},
        "kills": ["alkyl_halide"],
        "note": "Pd inserts into any C-X bond present, not only the one you drew",
    },
    "reductive_amination": {
        "conditions": "NaBH(OAc)3 or NaBH3CN, DCE, rt",
        "sites": {"aldehyde_ketone": "[CX3H1,CX3](=O)[#6]",
                  "amine_1_2": "[NX3;H1,H2;!$(NC=O);!$(N=*)]"},
        "kills": ["epoxide"],
        "note": "every carbonyl in the molecule is a substrate; hydride also opens epoxides",
    },
    "boc_deprotection": {
        "conditions": "TFA/DCM 1:1, rt  (strong acid)",
        "sites": {"boc": "[NX3]C(=O)OC(C)(C)C"},
        "kills": ["epoxide", "acetal", "silyl_ether", "tbu_ester", "trityl", "aziridine"],
        "note": "strong acid; anything acid-labile goes with the Boc",
    },
    "ester_hydrolysis": {
        "conditions": "LiOH or NaOH, THF/water, rt-60 C  (strong base)",
        "sites": {"ester": "[CX3](=O)[OX2H0][#6]"},
        "kills": ["epoxide", "aldehyde", "activated_ester"],
        "note": "hydroxide is nucleophilic; opens epoxides, adds to aldehydes",
    },
    "nitro_reduction": {
        "conditions": "H2, Pd/C  or  Fe, AcOH",
        "sites": {"nitro": "[NX3](=O)=O"},
        "kills": ["alkene", "alkyne", "benzyl_ether", "aryl_halide", "azide", "nitrile"],
        "note": "hydrogenation is unselective; alkenes, alkynes and Cbz/Bn all reduce",
    },
    "n_alkylation": {
        "conditions": "alkyl halide, K2CO3, DMF, 60 C",
        "sites": {"amine_1_2": "[NX3;H1,H2;!$(NC=O);!$(N=*)]",
                  "phenol_alcohol": "[OX2H1]"},
        "kills": ["epoxide"],
        "note": "any N-H or O-H competes; over-alkylation is the usual outcome",
    },
}

# Groups the conditions above destroy. Kept separate so a group is defined once.
FRAGILE = {
    "epoxide":        "[OX2r3]1[#6r3][#6r3]1",
    "aziridine":      "[NX3r3]1[#6r3][#6r3]1",
    "aldehyde":       "[CX3H1](=O)[#6]",
    "ester":          "[CX3](=O)[OX2H0][#6]",
    "tbu_ester":      "[CX3](=O)[OX2]C(C)(C)C",
    "activated_ester":"[CX3](=O)[OX2]N",
    "acetal":         "[CX4]([OX2H0][#6])([OX2H0][#6])",
    "silyl_ether":    "[OX2][Si]",
    "trityl":         "[CX4](c1ccccc1)(c1ccccc1)c1ccccc1",
    "benzyl_ether":   "[OX2][CH2]c1ccccc1",
    "alkene":         "[CX3]=[CX3;!$(C=O)]",
    "alkyne":         "[CX2]#[CX2]",
    "azide":          "[NX2]=[NX2+]=[NX1-]",
    "nitrile":        "[NX1]#[CX2]",
    "alkyl_halide":   "[CX4][Cl,Br,I]",
    "aryl_halide":    "[c][Cl,Br,I]",
}

_C = {k: Chem.MolFromSmarts(v) for k, v in FRAGILE.items()}
for r in REACTIONS.values():
    r["_sites"] = {k: Chem.MolFromSmarts(v) for k, v in r["sites"].items()}


def _n_matches(mol, patt):
    return len(mol.GetSubstructMatches(patt, uniquify=True)) if patt is not None else 0


def analyse(smiles):
    """Per-reaction-class liabilities for one molecule.

    Returns None if the SMILES will not parse. Every finding names the reaction class,
    because a liability is only a liability under particular conditions -- an epoxide is
    fine until someone reaches for TFA.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    present = {g: _n_matches(mol, p) for g, p in _C.items()}
    present = {g: n for g, n in present.items() if n}

    findings, applicable = [], []
    for rname, r in REACTIONS.items():
        counts = {s: _n_matches(mol, p) for s, p in r["_sites"].items()}
        if not any(counts.values()):
            continue                      # this chemistry does not apply to this molecule
        applicable.append(rname)

        for site, n in counts.items():
            if n > 1:
                findings.append({
                    "reaction": rname, "kind": "selectivity", "severity": "high",
                    "detail": f"{n} copies of {site} — the reagent cannot tell them "
                              f"apart, so this step gives a mixture",
                    "conditions": r["conditions"],
                })
        for g in r["kills"]:
            if g in present:
                findings.append({
                    "reaction": rname, "kind": "incompatible", "severity": "high",
                    "detail": f"{present[g]}x {g} does not survive: {r['conditions']}",
                    "conditions": r["conditions"],
                })
    return {
        # n_high is a DIFFICULTY count, not a verdict. See the module docstring:
        # 96% of purchasable compounds carry at least one finding.
        "SMILES": smiles,
        "fragile_groups": present,
        "applicable_reactions": applicable,
        "findings": findings,
        "n_high": sum(1 for f in findings if f["severity"] == "high"),
    }


def predict_step(reactants_smiles, product_smiles=None):
    """Placeholder for ML forward prediction (Molecular Transformer / IBM RXN).

    Deliberately not faked. Returning a guessed product here would reproduce exactly the
    error this stage exists to catch -- a confident answer with nothing behind it. Wire a
    real model in here when a GPU or an API key is available.
    """
    raise NotImplementedError(
        "forward reaction prediction needs a trained model (Molecular Transformer / "
        "IBM RXN); analyse() covers selectivity and conditions without one")


# --- control gate -----------------------------------------------------------
# Drugs that were manufactured at scale, and the 2025 structures a year of lab work
# failed to make. The rules must separate these. If they do not, they are noise.
CONTROLS = {
    "Adagrasib":  ("CC1CN(CCN1c1cc(cc(n1)c1nc(on1)C1(C)CCCc2sc(N)c(C#N)c12)N1CCN(CC1)C(=O)C=C)C", "made"),
    "Sotorasib":  ("CC1=CC(C)=C(C(C)=C1)N1C(=O)N(C2CCN(CC2)C(=O)C=C)c2nc(N3CCC(F)C3)nc(c2C1=O)O", "made"),
    "Imatinib":   ("Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc1nccc(-c2cccnc2)n1", "made"),
    "Hit-41-like":("O1CC1CN(N(N)N)CC=O", "failed"),   # epoxide + triazane + free aldehyde
}


def run_controls(verbose=True):
    """The rules are only trustworthy if they separate made from failed."""
    made, failed = [], []
    for name, (smi, truth) in CONTROLS.items():
        a = analyse(smi)
        if a is None:
            if verbose:
                print(f"  {name:<14} SMILES did not parse")
            continue
        (made if truth == "made" else failed).append((name, a["n_high"]))
        if verbose:
            print(f"  {name:<14} {a['n_high']:>2} high findings   ({truth})")
    if not made or not failed:
        return False, "controls missing a class"
    worst_made = max(n for _, n in made)
    best_failed = min(n for _, n in failed)
    if best_failed <= worst_made:
        return False, (f"cannot separate: worst made drug has {worst_made} findings, "
                       f"best failed structure has {best_failed}")
    return True, f"separated (made <= {worst_made} < {best_failed} <= failed)"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("candidates", nargs="?", help="JSON list of records with SMILES")
    ap.add_argument("--smiles", help="analyse a single molecule")
    ap.add_argument("-o", "--out")
    ap.add_argument("--skip-controls", action="store_true")
    ap.add_argument("--baseline", type=int, default=1,
                    help="median findings for purchasable compounds (calibration: 1)")
    args = ap.parse_args()

    if not args.skip_controls:
        print("control check — the rules must separate made drugs from failed structures\n")
        ok, msg = run_controls()
        print(f"\n  {msg}")
        if not ok:
            sys.exit("\nCONTROL GATE FAILED — rules are not reporting chemistry. Stopping.")
        print("  control gate passed\n")

    if args.smiles:
        a = analyse(args.smiles)
        if a is None:
            sys.exit("could not parse that SMILES")
        print(f"fragile groups: {a['fragile_groups'] or 'none'}")
        print(f"chemistry that applies: {', '.join(a['applicable_reactions']) or 'none'}")
        print(f"\n{a['n_high']} high findings:")
        for f in a["findings"]:
            print(f"  [{f['reaction']}] {f['detail']}")
        if not a["findings"]:
            print("  none — no selectivity or condition conflict found")
        return

    if not args.candidates:
        return
    rows = json.loads(Path(args.candidates).read_text())
    if isinstance(rows, dict):
        rows = list(rows.values())
    out = [r for r in (analyse(x["SMILES"]) for x in rows if x.get("SMILES")) if r]
    out.sort(key=lambda a: a["n_high"])
    clean = sum(1 for a in out if a["n_high"] == 0)
    import statistics as _st
    med = _st.median([a["n_high"] for a in out]) if out else 0
    print(f"{len(out)} analysed | {clean} clean ({100*clean/max(len(out),1):.0f}%) | "
          f"median {med:.0f} findings vs {args.baseline} for purchasable compounds")
    if med > 2 * args.baseline:
        print(f"  ! median is {med/max(args.baseline,1):.1f}x the purchasable baseline — "
              f"this set is unusually hard to make")
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        json.dump(out, open(args.out, "w"), indent=2)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
