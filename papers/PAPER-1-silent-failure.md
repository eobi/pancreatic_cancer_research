# Paper 1 — Silent, directional failure in the tools that vet generated molecules

**Status:** evidence complete, ready to draft.
**Merges:** Study 1 (generative validity) + Study 2 (filter calibration) + Study 5
(retrosynthesis), with Studies 3 and 4 as supporting material rather than separate papers.

**Author:** Obi Ebuka David
**Affiliation:** *decide before submission* — this work sits with Autogon Inc.; the
Dept. of Computer Science, University of Dayton affiliation applies to the Pentagon line
of work. Do not carry one over to the other by default.

---

## Title (working)

**A year of failed synthesis: silent, directional failure in the computational filters
that vet generated molecules**

Alternatives:
- *Confidently wrong in the same direction: five cheminformatics filters that reject the
  drugs they should rank first*
- *What it costs when a filter does not throw an error*

---

## Hypothesis

**H1 (primary).** The computational tools used to vet generated molecules — property
filters, structural-alert catalogues, ADMET predictors and retrosynthesis planners — fail
**silently** (returning a well-formed, confident answer rather than an error) and
**directionally** (systematically rejecting true positives rather than failing at random).

**H1a.** Because the failure is directional, it is invisible to the aggregate metrics the
field reports. A filter that rejects every approved drug still produces a tidy ranked list
and a plausible pass rate.

**H1b.** The failure is detectable by one cheap intervention: evaluating each tool against
a panel of molecules whose answer is already known, and refusing the tool until it
reproduces them. Panel **size** is the operative variable — small reference sets (n≈3)
miss failures that a 14-compound panel catches.

**H2 (consequence).** These failures are not academic. A campaign vetted by such tools
shipped three molecules to synthetic chemists; roughly a year of laboratory work followed
without producing the compounds. A retrospective audit reproduces that outcome from
structure alone.

### What would falsify this

- Filter failures are **random** rather than directional — i.e. approved drugs are
  rejected at the same rate as generated molecules. (Observed: they are rejected far more
  often, which is the opposite of the intended behaviour.)
- A small reference set (n≈3) detects the same failures as the 14-compound panel.
- The audit fails to distinguish the three molecules that failed synthesis from
  contemporaneous molecules that were successfully made.

---

## The novelty claim, stated narrowly

Each component result has partial prior art, and the paper must say so in the first
paragraph rather than be caught:

| component | prior art | what is new here |
|---|---|---|
| Generative models propose unsynthesizable molecules | Gao & Coley, JCIM 2020; GuacaMol; MOSES | Not new as a claim. Used only as the entry point. |
| Structural-alert catalogues over-reject | Capuzzi et al., *Phantom PAINS*, JCIM 2017; Baell & Nissink 2018 | Prior work critiques PAINS specifically; here **five independent filter families fail in the same direction**, quantified. |
| Deep-learning docking gives invalid poses | Buttenschoen et al., *PoseBusters*, 2024 | Not new. Supporting material only. |
| Retrosynthesis ignores stability | discussed informally | Quantified: an impossible molecule scores **above a marketed drug**. |

**The genuinely novel contributions are two, and neither is a chemistry result:**

1. **Ground truth linking a computational prediction to a real bench failure.** Almost all
   work in this area benchmarks in silico and stops. Here: model generates → molecules go
   to chemists → synthesis fails over ~a year → retrospective audit reproduces the failure
   from structure. That chain is rare and expensive to obtain.

2. **The silent-directional failure mode itself, quantified across independent tools.**
   A systems-level finding about the field's tooling. Not, to our knowledge, previously
   measured as a class.

*Every citation above is from recall and must be verified against the literature before
drafting. Treat the table as a checklist, not a bibliography.*

---

## Evidence in hand

**Generative output (n = 73).**
- **0** survive a standard pre-synthesis filter.
- **0 of 73** contain an aromatic ring. Reference drugs: 2 of 2 do.
- 63 of 73 in the reported shortlist carry a genotoxic or unstable group; mean 1.9 each.
- **15 are self-reactive** — functional groups that destroy one another in the same molecule.
- The three structures sent to chemists carry a **triazane**, an **epoxide**, and (in two)
  a **free aldehyde**.
- Same filter on **902,833** purchasable compounds: **57–76% pass**. Generated: **0.0%**.

**Directional filter failure (five independent cases).**
- BRENK flags acrylamide as `Michael_acceptor_1`, rejecting **Sotorasib and Adagrasib** —
  the warhead *is* the mechanism.
- A nitroso SMARTS also matched nitro groups, rejecting **Venetoclax**.
- The stability gate rejected **MRTX-1133** on its alkyne.
- ADMET with textbook cutoffs (DILI < 0.70, hERG < 0.70) rejected **199 of 200**
  compounds, including Sotorasib and Adagrasib. *Every approved control failed.*
- A 3-compound reference set missed all of the above; a **14-drug panel** caught them.

**Retrosynthesis cannot gate feasibility.**
- Impossible molecule ("Hit 41"): **80%** of precursors in stock, 6 steps.
- Adagrasib (marketed): **71%** of precursors in stock, 6 steps.
- Extension (`route_forward.py`), chemoselectivity and condition compatibility across 8
  reaction classes: generated molecules need a median of **4** interventions; purchasable
  compounds need **1** (n = 3,000). Only **4%** of purchasable compounds are entirely
  clean — so "has findings" cannot mean "cannot be made", and the signal is the median.

**Supporting material (formerly Studies 3 and 4).**
- Blind docking + CNN rescoring: **4.0 kcal/mol run-to-run variance** on the same molecule
  (Sotorasib scored −3.80 and −7.78 on repeat runs). Site-directed docking on the same
  target: cognate redock **0.67 Å** (G12C), **0.88 Å** (G12D).
- Screens covering **68%** of pancreatic KRAS by variant frequency: G12D 19,639 compounds,
  G12V 9,913. No purchasable compound competes with the clinical inhibitors.

---

## Figures

1. **The consequence.** Timeline: generation → shortlist → three molecules to chemists →
   ~a year → no compound. Structures annotated with the offending groups.
2. **The categorical gap.** Pass rate, generated (0.0%) vs purchasable (57–76%),
   with the aromatic-ring distribution beneath it.
3. **Directional failure.** Five filters × the approved drugs each rejects. The visual
   argument: the errors all point the same way.
4. **Panel size.** Failures detected vs reference-set size, 3 → 14.
5. **Retrosynthesis inversion.** In-stock precursor fraction: impossible molecule above
   marketed drug. Beside it, the median-4-vs-1 chemoselectivity separation.

---

## What this paper does **not** support

- That generative chemistry cannot work. Only that **this** model, with **this**
  objective, did not. The objective weighted docking 0.65 and synthetic accessibility
  0.20, with **no stability term at all**.
- That the filters criticised are bad tools. They are being used outside the domain they
  were fitted for. BRENK was never intended to vet covalent inhibitors.
- Any claim about the compounds' biological activity. Nothing here was measured in a lab.
- That the 14-drug panel is sufficient. It is sufficient *to catch these five*. The
  general question of panel construction is left open, and should be stated as open.

---

## Target venues

| venue | fit | realism |
|---|---|---|
| Nature Machine Intelligence | Perspective framing suits the systems-level claim | reach |
| Nature Communications | ground-truth anchor carries it | plausible |
| JACS Au | chemistry-facing, open access | plausible |
| Journal of Cheminformatics / JCIM | natural home for the technical version | safe |

The honest ceiling: this is a **retrospective, negative** result. Well-argued negative
results with a real-world anchor reach Nature Communications; they rarely go higher. The
prospective companion (Paper 2) is what changes the tier.

---

## Reproduce

    python src/audit_molecules.py data/raw/source-cross_docked_kras.xlsx   # → results/audit-output.txt
    python src/route_forward.py data/shortlists/top200_g12v.json           # → chemoselectivity
    curl localhost:8090/validate                                          # → filter panel check
