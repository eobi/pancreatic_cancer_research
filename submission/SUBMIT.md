# Preprint submission kit

Everything needed to post this manuscript. Each field below is copy-paste ready.
**You must submit it yourself:** every preprint server requires an authenticated account,
and an ORCID iD in the case of ChemRxiv.

## Where to submit

**ChemRxiv is the right server.** https://chemrxiv.org

Cheminformatics and computational drug discovery sit squarely in its scope, it is run by the
ACS with partner societies, and it is where the audience for this work reads preprints.

bioRxiv is a weaker fit: the work is chemistry-facing, not biology. arXiv q-bio.BM is
possible but has a smaller readership for this subject and may require endorsement.

## Before you start

1. **ORCID iD is mandatory.** Register free at https://orcid.org if you do not have one.
   Two minutes, and it should carry your academic name, Obi Ebuka David.
2. Screening is administrative and ethical only, not peer review. Posting typically takes a
   day or two.

## Fields

**Content type:** Working paper (full-length research manuscript)

**Category:** *Theoretical and computational chemistry*
Second choice if that feels wrong: *Biological and medicinal chemistry*

**Title**
```
Computed but not consulted: a self-audit of a generative drug-discovery campaign against KRAS in pancreatic cancer
```

**Authors:** Obi Ebuka David, Autogon Inc.
*Decide before submitting whether any co-authors from the 2024 Medgnosis paper (Yentumi,
Mbatuegwu, Ayobami, Obi T.) belong on this one. They built the system being audited.*

**Abstract:** `submission/abstract.txt` (299 words, plain text, no markup)

**Keywords**
```
pancreatic cancer; pancreatic ductal adenocarcinoma; KRAS; virtual screening;
molecular docking; generative molecular design; cheminformatics; ADMET;
synthetic accessibility; reproducibility; negative results
```

**Main file:** `submission/computed-but-not-consulted.pdf` (16 pages)

**Supplementary:** optional. The repository covers it, and the manuscript already links
there. If you want a supplementary upload, use `results/` as a zip.

**Data and code availability statement**
```
All code, data, figures and negative results, including failed validations, are available
at https://github.com/eobi/pancreatic_cancer_research (MIT licence). Citation metadata is
in CITATION.cff.
```

**Conflict of interest**
```
The author is affiliated with Autogon Inc., which developed the generative system audited
in this work. This is a self-audit and is described as such throughout.
```
*Declare this. A reviewer or reader who discovers it independently will weight it far more
heavily than one who is told plainly.*

**Funding:** as applicable.

## After it posts

1. ChemRxiv issues a DOI. Add it to `CITATION.cff` and to the repository README.
2. Update the open pull request at yboulaamane/awesome-drug-discovery#24 with the DOI.
3. The preprint makes zaixizhang/Awesome-SBDD a legitimate submission target, since that
   list indexes papers rather than repositories.

## Two things to settle first

**The synthesis record.** The manuscript states the laboratory outcome is attested rather
than documented. That is honest and survives, but any dated record of the synthesis attempts
would strengthen the paper's central anchor materially.

**Co-authorship.** See above. This decision is easier to make now than after posting.
