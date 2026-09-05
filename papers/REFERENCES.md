# Verified reference list

Every entry below was checked against the publisher record on **2026-09-05**. DOIs
resolve. Use this file as the single source for both manuscripts; do not cite from memory.

1. **Gao, W. & Coley, C. W.** The Synthesizability of Molecules Proposed by Generative
   Models. *J. Chem. Inf. Model.* **60**, 5714–5723 (2020).
   https://doi.org/10.1021/acs.jcim.0c00174
2. **Capuzzi, S. J., Muratov, E. N. & Tropsha, A.** Phantom PAINS: Problems with the
   Utility of Alerts for Pan-Assay INterference CompoundS. *J. Chem. Inf. Model.* **57**,
   417–427 (2017). https://doi.org/10.1021/acs.jcim.6b00465
   *Directly relevant: reports that **87 small-molecule FDA-approved drugs contain PAINS
   alerts**, and cautions against blind use of PAINS filters to triage compounds.*
3. **Baell, J. B. & Nissink, J. W. M.** Seven Year Itch: Pan-Assay Interference Compounds
   (PAINS) in 2017 — Utility and Limitations. *ACS Chem. Biol.* (2018).
   https://doi.org/10.1021/acschembio.7b00903
4. **Buttenschoen, M., Morris, G. M. & Deane, C. M.** PoseBusters: AI-based docking methods
   fail to generate physically valid poses or generalise to novel sequences.
   *Chem. Sci.* **15**, 3130–3139 (2024). https://doi.org/10.1039/D3SC04185A
5. **Brenk, R. et al.** Lessons Learnt from Assembling Screening Libraries for Drug
   Discovery for Neglected Diseases. *ChemMedChem* **3**, 435–444 (2008).
   https://doi.org/10.1002/cmdc.200700139
6. **Eberhardt, J., Santos-Martins, D., Tillack, A. F. & Forli, S.** AutoDock Vina 1.2.0:
   New Docking Methods, Expanded Force Field, and Python Bindings. *J. Chem. Inf. Model.*
   **61**, 3891–3898 (2021). https://doi.org/10.1021/acs.jcim.1c00203
7. **Wang, X. et al.** Identification of MRTX1133, a Noncovalent, Potent, and Selective
   KRAS^G12D Inhibitor. *J. Med. Chem.* **65**, 3123–3133 (2022).
   https://doi.org/10.1021/acs.jmedchem.1c01688
8. **Ardalan, B., Ciner, A., Baca, Y. et al.** Distinct Molecular and Clinical Features of
   Specific Variants of KRAS Codon 12 in Pancreatic Adenocarcinoma. *Clin. Cancer Res.*
   **31**, 1082–1090 (2025). https://doi.org/10.1158/1078-0432.CCR-24-3149
   *n = 3,755 PDAC with codon-12 mutations: **G12D 47% (1,766), G12V 34% (1,294),
   G12R 17% (621), G12C 2% (74)**. Denominator is codon-12-mutant tumours, not all PDAC.*
9. **Canon, J. et al.** The clinical KRAS(G12C) inhibitor AMG 510 drives anti-tumour
   immunity. *Nature* **575**, 217–223 (2019).
   https://doi.org/10.1038/s41586-019-1694-1
10. **Hallin, J. et al.** The KRAS^G12C Inhibitor MRTX849 Provides Insight toward
    Therapeutic Susceptibility of KRAS-Mutant Cancers in Mouse Models and Patients.
    *Cancer Discov.* **10**, 54–71 (2020).
    https://doi.org/10.1158/2159-8290.CD-19-1167
11. **Genheden, S. et al.** AiZynthFinder: a fast, robust and flexible open-source software
    for retrosynthetic planning. *J. Cheminform.* **12**, 70 (2020).
    https://doi.org/10.1186/s13321-020-00472-1
12. **Swanson, K. et al.** ADMET-AI: a machine learning ADMET platform for evaluation of
    large-scale chemical libraries. *Bioinformatics* **40**, btae416 (2024).
    https://doi.org/10.1093/bioinformatics/btae416

## A correction these references force

Our working figures for KRAS variant frequency in PDAC were G12D 39%, G12V 29%, G12R 15%,
G12C 1.7%. Ref. 8 reports **47 / 34 / 17 / 2%**. The two are not in conflict — they use
different denominators:

- **Ref. 8 denominator:** PDAC tumours carrying a **codon-12** KRAS mutation (n = 3,755).
- **Our denominator:** all PDAC tumours.

KRAS is mutated in >90% of PDAC and codon 12 accounts for the large majority of those, so
47% of codon-12 mutants ≈ 40% of all PDAC, 34% ≈ 29%, 17% ≈ 14%, 2% ≈ 1.7% — matching our
figures. **Both manuscripts must state the denominator explicitly wherever these numbers
appear.** Reported coverage:

| variants screened | % of codon-12-mutant PDAC | % of all PDAC |
|---|---|---|
| G12D + G12V | 81% | 68% |
| G12D + G12V + G12R | **98%** | **83%** |

## Additions for the expanded manuscript (verified via CrossRef, 2026-09-05)

14. **Du, Y., Jamasb, A. R., Guo, J., Fu, T., Harris, C., Wang, Y., Duan, C., Lio, P.,
    Schwaller, P. & Blundell, T. L.** Machine learning-aided generative molecular design.
    *Nature Machine Intelligence* **6**, 589-604 (2024).
    https://doi.org/10.1038/s42256-024-00843-5
    *Source of the curated corpus of 73 generative campaigns with experimental validation
    used in section 3.6. Direct and recent prior art; must be cited in the introduction.*
15. **Polykovskiy, D. et al.** Molecular Sets (MOSES): A Benchmarking Platform for
    Molecular Generation Models. *Frontiers in Pharmacology* **11** (2020).
    https://doi.org/10.3389/fphar.2020.565644
    *Source of the eight baseline model outputs used in the filter battery.*
16. **Brown, N., Fiscato, M., Segler, M. H. S. & Vaucher, A. C.** GuacaMol: Benchmarking
    Models for de Novo Molecular Design. *J. Chem. Inf. Model.* **59**, 1096-1108 (2019).
    https://doi.org/10.1021/acs.jcim.8b00839
17. **Wang, et al.** ClickGen: Directed exploration of synthesizable chemical space via
    modular reactions and reinforcement learning. *Nature Communications* **15** (2024).
    https://doi.org/10.1038/s41467-024-54456-y
    *Surveyed campaign, gate coverage 0.53, the only one of four applying a reactive-group
    filter.*
18. **Atz, K. et al.** Prospective de novo drug design with deep interactome learning.
    *Nature Communications* **15** (2024). https://doi.org/10.1038/s41467-024-47613-w
    *Surveyed campaign, gate coverage 0.21.*
19. **Ballarotto, M. et al.** De Novo Design of Nurr1 Agonists via Fragment-Augmented
    Generative Deep Learning. *J. Med. Chem.* **66**, 8170-8177 (2023).
    https://doi.org/10.1021/acs.jmedchem.3c00485
    *Surveyed campaign, gate coverage 0.00, 6 synthesised, 2 hits.*
20. **Moret, M. et al.** Beam Search for Automated Design and Scoring of Novel ROR Ligands
    with Machine Intelligence. *Angew. Chem. Int. Ed.* **60**, 19477-19482 (2021).
    https://doi.org/10.1002/anie.202104405
    *Surveyed campaign, gate coverage 0.00, 3 synthesised, 3 hits. Records medicinal
    chemists rejecting the first design round as synthetically inaccessible, prompting a
    method revision. The key observation in section 3.6.*
21. **RDKit: Open-source cheminformatics.** https://www.rdkit.org
    *BRENK and PAINS catalogues used unmodified throughout.*
