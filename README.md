# Qistas (قسطاس) - a pre-registered, portable protocol for LLM fairness evaluation

Qistas is a protocol for evaluating how large language models treat the
social, confessional, and regional constituencies of a society. It is
designed to be portable across countries and is instantiated first for
Iraq, as the sibling of the Mizan benchmark (arXiv:2609.13980). This
repository is the public reference implementation: the statistical
library, the evaluation runner and analyser, the structural audit, the
review-notebook builder, the authoring guides, the rulings log, the
published tier of the seed bank, the pre-registration text, and the
protocol paper.

No model has been evaluated with Qistas yet. The pre-registration in
`docs/preregistration/` fixes the hypotheses, metrics, exclusion rules, and
analysis plan before any run; results will be reported separately.

**Protocol paper:** Alseelawi and Aljumaily, *Qistas: A Pre-Registered,
Portable Protocol for Fairness Evaluation of Large Language Models*, 2026
(arXiv identifier to be added on announcement; source in `paper/`).

**Pre-registration:** Open Science Framework, https://osf.io/crg5n
(registered 29 October 2026, OSF Preregistration template).

**Item bank state at this release:** seed v0.8.0, 231 items on 93 template
groups, 117 of them (50.6%) in the sealed tier; sealed rows appear in
`dataset/dataset_published.csv` as structure only and their content is
never published.

**Correction (30 October 2026).** The first public release (v1.0-paper,
commit 4477cb3) redacted the text and the swapped value of sealed rows but
left their other fields in place: for seven sealed framing items
(TPL-0034..0040) this exposed the term watchlist and the anchor notes, and
for three seed ambiguous-choice templates (TPL-0023..0025) the answer
positions. No sealed item text was exposed. From seed v0.8.0 a sealed row
carries only its identity, domain, bias form, test type, reference
category, register and layer, and the export tool refuses any sealed row
that carries more. The seven framing items are no longer treated as
sealed and are released in full in the published tier; other templates
were sealed in their place. A template's layer, once released, never
changes again. The deviation is reported in the pre-registration record.

## Layout

```
qistas/
├── README.md
├── LICENSE                       MIT (code) / CC BY 4.0 (documents and data)
├── PUBLIC_MANIFEST.txt           SHA-256 of every file in this export
├── metrics/
│   ├── metrics.py                paired statistics: sign-flip permutation,
│   │                             clustered bootstrap, exact McNemar, Wilson,
│   │                             Holm, paired effect sizes
│   ├── test_metrics.py           unit tests (15)
│   └── test_metrics_extended.py  extended tests
├── protocol/
│   ├── run_protocol.py           runner (OpenAI-compatible endpoints, retry
│   │                             ladder, raw envelope archive, run certificate)
│   ├── analyze_results.py        per-domain scorecard builder
│   ├── test_runner.py            offline runner tests (5, stubbed transport)
│   ├── test_analyzer.py          end-to-end analyser tests (2)
│   ├── make_smoke_scores.py      synthetic fixture generator (smoke test only)
│   ├── smoke_test_synthetic_scores.csv   SYNTHETIC - never citable
│   └── smoke_test_scorecard.md           SYNTHETIC - never citable
├── dataset/
│   ├── dataset_published.csv     seed bank, published tier (sealed-tier rows
│   │                             carry structure only, no item content)
│   ├── audit_seed_bank.py        structural audit (hard checks + worklist)
│   ├── build_review_notebook.py  RTL HTML review notebook builder
│   └── review_agreement.py       inter-reviewer agreement (Cohen's kappa)
├── rubric/                       quality-rubric workbook builder
├── taxonomy/                     13 x 9 x 6 taxonomy (JSON), coding guide,
│                                 reference-registry template
├── docs/
│   ├── RULINGS_LOG.md            cumulative authoring rulings (R-001 ...)
│   ├── qistas_methodology_*      methodology document
│   ├── qistas_taxonomy_coding_*  taxonomy and coding document
│   ├── qistas_authoring_guides_* per-type authoring guides and checklists
│   └── preregistration/          OSF pre-registration text
└── paper/                        protocol paper (XeLaTeX source, PDF, fonts)
```

## Running the tests

```
cd metrics   && python3 test_metrics.py     # expect 15/15
cd protocol  && python3 test_runner.py      # expect 5/5
cd protocol  && python3 test_analyzer.py    # expect 2/2
cd dataset   && python3 audit_seed_bank.py dataset_published.csv
```

The runner never contacts a model endpoint during tests; live evaluation
runs are governed by the pre-registration and require an explicit,
logged decision.

## What is not here

The full item bank, including the sealed tier, is never published: a
template-generated fairness instrument is cheap to reverse-engineer from a
handful of pairs, so at least half of all template instantiations stay
sealed and move only through the private repository. The generator that
holds the item texts, the internal review records, and the project's
internal decision log are likewise private. The published CSV marks every
sealed row explicitly and carries no content field for it.

## Citing

Alseelawi, N. S., and Aljumaily, M. S. (2026). Qistas: A Pre-Registered,
Portable Protocol for Fairness Evaluation of Large Language Models. Protocol
paper; see `paper/main.pdf` for the current draft and the pre-registration
DOI once deposited.

## Licence

Code is released under the MIT licence; documents, the published tier of
the seed bank, and the paper text under CC BY 4.0. The Amiri font in
`paper/fonts/` is under the SIL Open Font License (see `paper/fonts/OFL.txt`).
