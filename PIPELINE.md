# End-to-end pipeline — the runbook

Every phase, in order, with the command that runs it and the check that must pass before
the next one starts. This is the record of what was actually executed, written so it can
be automated.

**The rule that governs the whole thing:** every phase is calibrated against molecules
whose answer is already known, before its output is believed. Three phases failed that
check on the first attempt. A phase with no validation gate is not finished.

---

## Phase map

| # | phase | script | gate that must pass | status |
|---|---|---|---|---|
| 0 | Target intake | manual + RCSB | receptor has a **cognate** ligand | done |
| 1 | Receptor prep | `mk_prepare_receptor` | PDBQT written, altlocs resolved | done |
| 2 | Method validation | `dock_site.py validate` | **cognate redock < 2.0 A** | done |
| 3 | Library acquisition | `fetch_zinc.py` | MW range matches the target's drugs | done |
| 4 | Chemical reality gate | `prepare_ligands.py` | known drugs survive it | done |
| 5 | Selection | `select_ligands.py` | similarity + diversity reported | done |
| 6 | Docking screen | `run_screen.py` | rate and dropout sane | done |
| 7 | ADMET | `admet_gate.py` | **known drugs pass the gate** | done |
| 8 | Route + buyability | `route_check.py` | runs only on phase-4 survivors | done |
| 9 | Order dossier | `make_dossier.py` | ZINC id recovered per compound | built |
| 10 | Lab capture | — | — | **not built** |

Phase 4 is also available as a service: `uvicorn gate_service:app --port 8090`, with
`/check`, `/validate`, `/rules`. Its `/validate` endpoint is what caught the MRTX-1133 bug.

Phases 0-9 run on an M1 Pro laptop. No GPU. A full target takes about 3 hours, almost
all of it phase 6.

---

## Phase 0 — Target intake

Pick the variant the **disease** has, then find a structure. Not the other way round.

    # what fraction of the disease does each variant represent?
    #   PDAC: G12D ~39%, G12V ~29%, G12R ~15%, G12C 1.7%
    # then search RCSB for that variant WITH a bound drug-like ligand

    curl -s -X POST -H "Content-Type: application/json" -d @query.json \
      "https://search.rcsb.org/rcsbsearch/v2/query"

**Gate:** the structure must contain a co-crystallised drug-like ligand. Without one,
phase 2 cannot run and nothing downstream can be trusted.

*Learned the hard way:* G12C was chosen first because 8AFB had a cognate ligand. It is
1.7% of pancreatic cancer. See DISCOVERIES section 7.

Used: **8AFB** (G12C + BI-0474, 1.12 A) then **7RPZ** (G12D + MRTX-1133, 1.3 A).

---

## Phase 1 — Receptor prep

Extract the crystal ligand, build the box from it, strip to protein, convert to PDBQT.

    # box = ligand extent + 5 A padding each side; keep the ligand as the RMSD reference
    python - <<'EOF'
    ... centre = mean(ligand coords); box = (max-min) + 10.0
    EOF

    mk_prepare_receptor.py --read_pdb receptor_protein.pdb -o rec -p \
      --default_altloc A --allow_bad_res \
      --box_center $cx $cy $cz --box_size $sx $sy $sz

**Gotchas:** high-resolution structures have altloc conflicts (`--default_altloc A`);
some need `--allow_bad_res`. GDP and MG are stripped with everything else — prody parses
protein only regardless, so this made no difference here, but check if your target's
cofactor is structural.

---

## Phase 2 — Method validation ← the gate that was missing in 2025

    python dock_site.py validate \
      --receptor work_g12d/rec.pdbqt --box work_g12d/box.txt \
      --crystal work_g12d/ref_6IC.pdb --controls work_g12d/controls.json \
      --cognate "MRTX-1133"

**Gate: cognate redock RMSD < 2.0 A.** Measured 0.67 A (G12C), 0.88 A (G12D).

Also record the **control spread** — how far apart the known binders score. 2.96 kcal/mol
on G12C, 4.84 on G12D. A spread near zero means the scoring function cannot rank, which is
exactly what blind docking did (0.4 kcal/mol, DISCOVERIES section 2).

**If this fails, stop.** Do not screen. Check the box, the protonation, or whether the
site needs an ensemble of receptor conformations.

*Trap:* RMSD against a PDB ligand needs `AssignBondOrdersFromTemplate` first, or
`CalcRMS` maps atoms arbitrarily and reports ~8 A for a pose sitting 0.34 A away.

---

## Phase 3 — Library acquisition

    python fetch_zinc.py --tranches KE KF KG --max-files 6 \
      -o library_K.smi --cache work/zinc_K --profile

**Gate:** the profile's MW range must bracket the target's known drugs. ZINC tranche
letters are mass bins — **I = 425-450, J = 450-500, K = 500-953**. MRTX-1133 is 600 Da,
so K. The first attempt pulled tranches centred on 437 Da and had to be discarded.

*Traps:* `files.docking.org` returns 503 for parallel requests and writes the HTML error
page into your `.smi`; it 403s urllib's default User-Agent but allows curl's. Both corrupt
a library silently. The fetcher handles both, and preserves `zinc_id` (an early version
dropped it, which broke phase 9).

Result: 902,833 unique compounds, MW median 437 (I/J) then 500-953 (K).

---

## Phase 4 — Chemical reality gate ← the phase that would have saved the year

    python prepare_ligands.py library_K.smi -o ligands.json \
      --covalent -j 10 --min-mw 500 --max-mw 700

**Gate: a PANEL of known drugs must survive it** — not two or three references. A 14-drug
panel caught five broken catalogue rules that a 3-drug check missed, including one that
rejected MRTX-1133. Run `curl localhost:8090/validate` or see section 7b.

With `--covalent`, the gate recovers exactly Adagrasib and Sotorasib from 2,999 KRAS
molecules and rejects all 2,997 generated ones.

**The covalent exemption is mandatory for covalent programmes.** BRENK flags acrylamide as
`Michael_acceptor_1` and rejects both approved G12C drugs — the warhead *is* the mechanism.

Rejects: unstable groups (triazane, peroxide, epoxide, aziridine, azo, N-oxide, boron),
**self-reactive pairs** (hydrazine+aldehyde, hydrazine+epoxide, amine+aldehyde), PAINS,
BRENK, and anything with no aromatic ring.

Result: 902,833 → **685,000 (75.90%)** after the exemption fix; the original run gave
518,662 (57.45%) because rules rejecting approved drugs were still gating. The same gate passes 0.07% of the 2025 generated
molecules. That contrast is the single most useful number in this project.

Streams rather than loading the library into memory — a 22M-compound list will exhaust
16 GB.

---

## Phase 5 — Selection

Docking is the expensive tier, so 500k survivors cannot all be scored.

    python select_ligands.py ligands.json -n 2000 -o selected_g12d.json \
      --controls work_g12d/controls.json

Ranks by max Tanimoto (Morgan r2, 2048 bit) to the reference binders, then diversifies
(pairwise cap 0.85) so the shortlist is not one scaffold repeated.

**Record the similarity ceiling.** 0.58 for the G12C references, 0.454 for G12D — the
library simply contains less chemistry resembling MRTX-1133, and that partly explains the
result in phase 6.

---

## Phase 6 — Docking screen

    python run_screen.py selected_g12d.json -o screen_g12d.json -j 10 \
      --receptor work_g12d/rec.pdbqt --box work_g12d/box.txt

One Vina process per ligand, **one core each** — that beats one process on ten cores by
about 4x (3.5-5 s/ligand vs 14-32 s). Exhaustiveness 4 scores essentially identically to
8. Checkpoints every 25, skips what is done, so it survives an interrupt.

**Watch:** dropout rate (0.7-1.0% is normal, from conformer embedding), and rate drift
(heavy flexible ligands slow batches; the run is not stalled).

Results: G12C 1,987 scored in 1 h 56 m; G12D 1,986 in 2 h 40 m; G12D deep 9,913 in ~20 h
(two arms sharing the machine, so ~10 s/ligand rather than ~5).

**Run a random control arm.** The similarity selection had never been validated. Screening
10,000 random draws from the same gated pool alongside the ranked 10,000 showed the
heuristic is worth its cost: median -8.68 vs -8.24, and the only hit past a clinical
reference came from the ranked arm.

---

## Phase 7 — ADMET

    # SEPARATE VENV — admet-ai needs chemprop 1.x, aizynthfinder (phase 8) pulls 2.x
    # and silently breaks it. Also allowlist argparse.Namespace for torch >= 2.6.
    ../scratchpad/admetenv/bin/python admet_gate.py top200_g12d.json -o shortlist_g12d.json

**Gate: the approved controls must pass.** The script runs this self-check on every
invocation and exits if one fails.

First attempt used textbook cutoffs (DILI < 0.70, hERG < 0.70) and rejected **199 of 200**
— and also Sotorasib and Adagrasib. Oncology drugs are hepatotoxic and hERG-flagged;
Sotorasib carries a hepatotoxicity warning on its label. **DILI and hERG are informational
here, never gates.**

Recalibrated: 197 pass, 3 rejected. But note that a gate calibrated to "no worse than a
marketed drug" barely filters. **Use ADMET comparatively** — how many hits beat the *best*
control on each axis — rather than as pass/fail.

---

## Phase 8 — Route and buyability

    python route_check.py work/route_validation.json -o routes.json --time-limit 180

**Order is mandatory: phase 4 before phase 8.** The script enforces it and refuses
anything that fails the gate.

Retrosynthesis asks *"if this molecule existed, what would assemble it"* — it never asks
whether the product is stable. Measured: Hit 41 (a triazane + epoxide + aldehyde that a
year of lab work failed on) returns a clean 6-step route at 80% stock, **better than
Adagrasib**. Approved drugs 71-83%, impossible molecules 67-80%. **Not separated.**

*Also:* AiZynthFinder's `is_solved` boolean requires every precursor in stock and returns
False for Sotorasib. Use stock fraction and step count as graded evidence.

*Trap:* Zenodo drops connections mid-transfer and leaves truncated model files with no
error — the corruption surfaces as `InvalidProtobuf` at load. Fetch with `curl -C -` and
verify every file loads.

---

## Phase 9 — Order dossier

    python make_dossier.py shortlist_g12d.json -o dossier.json --top 25

Joins each candidate back to its ZINC id from the tranche cache, queries vendor
availability, and emits the full evidence chain per compound: binding, properties, ADMET,
route, and where to buy.

---

## Phase 10 — Lab capture — NOT BUILT

The missing layer. Orders placed from inside the system, compound and batch tracking, and
ingestion of what comes back (NMR, LC-MS, HPLC purity, assay readouts) attached to the
molecule record that predicted them.

**Why it matters more than anything above:** every phase improves only if measured
outcomes return. Without it the pipeline never learns, and phases that need real assay
data — potency prediction, cell response, exposure — cannot be built at all.

---

## Running a new target end to end

    # 0-1  pick the variant by disease prevalence, fetch a LIGANDED structure, prep
    # 2    validate — STOP if cognate redock > 2.0 A
    python dock_site.py validate --receptor <rec> --box <box> \
        --crystal <ref> --controls <controls> --cognate "<name>"

    # 3-4  library, once per mass range; the gate output is target-independent and reusable
    python fetch_zinc.py --tranches K? --profile -o library.smi --cache work/zinc
    python prepare_ligands.py library.smi -o ligands.json --covalent --min-mw 500 --max-mw 700

    # 5-6  select and screen
    python select_ligands.py ligands.json -n 2000 -o selected.json --controls <controls>
    python run_screen.py selected.json -o screen.json -j 10 --receptor <rec> --box <box>

    # 7-9  triage
    python admet_gate.py top200.json -o shortlist.json
    python route_check.py shortlist.json -o routes.json
    python make_dossier.py shortlist.json -o dossier.json --top 25

Phases 3-4 are the expensive part and are reusable across targets. Re-running a new
variant costs phases 0-2 (minutes) and 5-6 (~3 hours).

---

## What automating this needs

1. **Every phase already returns a verdict**, not just data. Wire those into a runner that
   halts on a failed gate rather than proceeding.
2. **Phase state is on disk** (`ligands.json`, `selected.json`, `screen_*.json`), so a
   runner can resume mid-pipeline.
3. **Phase 10 is the gap.** Until results come back and attach to predictions, this is an
   open loop that produces hypotheses and never learns from them.
4. **Service boundaries do not exist yet.** These are scripts. "Usable individually and as
   a system" needs each phase behind an API — phase 4 is the obvious first one to expose,
   since a chemist anywhere can use it standalone with nothing else adopted.
