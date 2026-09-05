# Gate coverage survey: scoring rubric

**Fixed 2026-09-05, before any paper was scored.** Changes go in the amendment log at the
foot of this file, with reasons.

## Question

For each published generative or virtual-screening campaign that proposes specific molecules
for a target: **which computed properties could stop a molecule, and which were only
reported?**

## Inclusion criteria

A paper is eligible if all four hold.

1. It proposes specific small molecules for a named biological target.
2. It computes at least one molecular property beyond the primary scoring function
   (docking score, binding affinity, or generative likelihood).
3. It names a shortlist, hit set, or lead candidates.
4. Methods are sufficiently described to determine what the selection rule was.

Excluded: pure benchmark or distribution-learning papers with no shortlist; method papers
proposing no molecules; reviews.

## Per-paper fields

| field | definition |
|---|---|
| `properties_computed` | count of distinct property TYPES computed and reported, excluding identifiers. Per-target duplicates of the same property count once. |
| `properties_gating` | count of those with an explicit threshold, cutoff, or filter that removed molecules |
| `coverage` | `properties_gating / properties_computed` |
| `primary_gate` | what actually selected the shortlist |
| `inert_safety` | list of computed safety or stability signals with no threshold: PAINS, toxicity, mutagenicity, reactive-group flags, synthetic accessibility |
| `stability_gate` | boolean: any explicit criterion on chemical stability or reactivity |
| `wetlab` | boolean: any molecule synthesised or assayed |

## Decision rules, to keep scoring reproducible

- **Gating requires a stated threshold that removed molecules.** "We computed QED" is not a
  gate. "Compounds with QED < 0.5 were discarded" is.
- **Ambiguity counts against gating.** If the methods do not state that a property removed
  molecules, it is scored as reported, not gating. This biases coverage downward, and the
  bias is stated in the results.
- **Ranking is not gating** unless a cutoff is applied.
- **A property mentioned only in a results table, never in methods, is reported.**
- Where a paper is scored from abstract plus methods only, it is flagged `partial` and
  reported separately.

## Pre-registered prediction

Before scoring: we expect median coverage below 0.35, and expect synthetic accessibility and
toxicity predictions to be the most frequently inert signals. Recording this so the survey
cannot be read as having found whatever we went looking for.

## Known limitations, stated in advance

- Coverage is crude and ignores gate quality. A pipeline gating on one well-calibrated
  property may outperform one gating on five badly.
- Methods sections vary in detail; the downward bias above is real and unquantified.
- Sample is drawn from searchable literature and is not exhaustive.
- The authors' own campaign is in the sample and scored by the same rubric (coverage 0.16).

## Amendment log

*(none)*
