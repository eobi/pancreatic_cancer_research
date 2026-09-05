# Automating the pipeline end to end — what that can and cannot mean

Written in answer to: *"can we automate this pipeline end to end, so whatever drug we
generate we can properly validate it, and even run in vivo / in vitro on the selected
compound and measure it digitally?"*

Short answer: **the discovery half can be fully automated today. The in vitro and in vivo
half cannot be measured digitally — not because we have not built it, but because the
models that would do it need your own wet-lab data to exist at all.**

That distinction is the whole thing. Getting it wrong is what cost 2025.

---

## What is automatable now, unattended

Each stage already returns a **verdict**, not just data, and each has a gate calibrated
against molecules with known answers. A runner can chain them and halt on failure.

| # | stage | returns | gate | state |
|---|---|---|---|---|
| 1 | Target intake | receptor + cognate ligand | structure has a bound drug-like ligand | works |
| 2 | Generation | candidate structures | — | works, model needs retraining |
| 3 | **Chemical reality** | pass / fail + reason | 14-drug panel must pass | **validated** |
| 4 | Selection | ranked subset | similarity beats random (measured) | **validated** |
| 5 | Binding | score + pose | cognate redock < 2.0 A | **validated per target** |
| 6 | ADMET | liability profile | approved controls must pass | works, weak discrimination |
| 7 | Route + buyability | route tree, stock fraction | runs only on stage-3 survivors | works, cannot judge stability |
| 8 | Dossier | evidence chain per compound | ZINC id resolved | works |

**A target goes from PDB code to ranked, ADMET-profiled, route-checked, orderable
shortlist with no human in the loop.** ~3 hours on a laptop for 2,000 compounds.

That is real, and it is more than most groups have. It is also *entirely a hypothesis
generator*.

---

## What "validate" means here — and what it does not

Everything above predicts **binding propensity**. Nothing above measures **activity**.

A Vina score of -12.83 is not an IC50. It is not an affinity. It is a geometric and
empirical estimate that a molecule could occupy a pocket. The evidence for that gap in our
own data:

- Sotorasib, a marketed drug, scored **-5.00** on its own target under blind docking —
  worse than 68 of 73 generated molecules.
- The same compound moved **4.0 kcal/mol** between two identical runs.
- Our G12D lead beats AM-2383 by **0.12 kcal/mol**, which is inside the method's error.
- ADMET-AI barely separates our shortlist from marketed drugs at any threshold.

So "properly validate" is achievable in the sense of **"no compound reaches a chemist that
cannot exist, has no route, or carries a liability an approved drug does not."** That is a
real and valuable form of validation, and it is exactly what was missing.

It is **not** validation in the sense of "we know this binds."

---

## In vitro and in vivo — the honest position

### They cannot be measured digitally

- **In vitro prediction** (cell-line sensitivity, assay outcome, morphological profile) can
  be built from public pharmacogenomic and imaging corpora. Such a model would prioritise
  which assays to run. It would not tell you whether *your* compound is active, because it
  has never seen your chemistry or your assay.
- **In vivo** is further out. PBPK simulation (PK-Sim, GastroPlus) predicts absorption,
  exposure and organ burden well enough to **design a smaller, shorter animal study**. It
  does not replace one, and no regulator currently accepts that it does. FDA Modernization
  Act 2.0 opened a door in principle; in practice you still need the data.

### And they are downstream of wet data, not a substitute for it

This is the part that inverts the intuition. To build a model that predicts your in vitro
result, you need in vitro results to train it on. You have none. So the sequence is:

    order compound  ->  run assay  ->  results attach to the prediction that chose it
                                   ->  retrain  ->  model becomes worth trusting
                                   ->  next cycle needs fewer compounds

**Digitising in vitro/in vivo is the reward for closing the loop, not the way to avoid
closing it.** A model trained only on literature will confidently mis-rank your chemistry,
which is the same failure mode as 2025 in a new costume.

### What this means for a clinical partner

They asked for laboratory validation. Nothing above answers that. The honest statement is:

> "We can now guarantee that every molecule we bring you can exist, has a synthetic route
> or is purchasable, and carries no liability an approved drug does not. We cannot tell you
> it binds. That still needs your assay — and we have cut the number of compounds you need
> to test to get there."

That is a much stronger position than 2025, and it is defensible.

---

## The missing stage, and why it is the important one

**Stage 9 — lab execution and capture. Not built.**

Orders placed from inside the system; compound and batch tracking; ingestion of what comes
back (NMR, LC-MS, HPLC purity, assay readouts) **attached to the molecule record that
predicted it.**

Without it, every stage above is an open loop that generates hypotheses and never learns
whether it was right. With it:

- stage 5 gets a measured hit rate, so its scores acquire meaning
- stage 6 can be recalibrated on your chemistry instead of on marketed drugs
- in vitro prediction becomes buildable for the first time
- the whole pipeline improves per cycle rather than per rewrite

**It is the only stage whose absence caps the value of all the others.** It is also the
cheapest to build, because it is plumbing rather than science.

---

## So: is the answer yes?

| claim | verdict |
|---|---|
| automate discovery end to end, unattended | **yes, today** |
| guarantee every candidate can exist and is obtainable | **yes, validated** |
| rank candidates against clinical references on a validated setup | **yes, per target** |
| screen a purchasable library in hours on a laptop | **yes** |
| predict binding affinity | **no** — scores are hypotheses, error ~1 kcal/mol |
| run in vitro digitally and trust it on your chemistry | **no** — needs your assay data first |
| run in vivo digitally | **no** — simulation shapes a study, does not replace it |
| shrink the wet lab to a handful of compounds | **yes, and that is the actual prize** |

The goal was never zero experiments. It is that every experiment you run tests a molecule
that could exist, has a route, and has cleared everything a computer can decide alone.
**That is now true, and it was not true in 2025.**

---

## Concrete next build

`src/run_pipeline.py` — an orchestrator that chains stages 1-8, halts on any failed gate,
and writes a per-target dossier. Everything it needs already exists: each stage returns a
verdict, and state lives on disk so it can resume mid-pipeline.

Then stage 9, which turns the open loop into a closed one.
