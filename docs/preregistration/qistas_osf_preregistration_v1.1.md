---
title: "Qistas: Pre-Registration of the First Iraqi Pilot"
subtitle: "OSF Preregistration form (eight-page version in force in October 2026), text as deposited in draft on 24 October 2026, version 1.1"
author: "Nawar S. Alseelawi (University of Misan) and Mustafa S. Aljumaily (Missan Oil Company)"
---

This document reproduces, field by field and in the form's own order, the
text entered in the OSF Preregistration draft created on 24 October 2026
(draft identifier 6adbd6adc7dff1ac850dadf0). Version 1 of this document
(15 October 2026) followed the older 24-field layout of the same template;
the registry now presents the template as eight pages with different field
names, so version 1.1 re-keys the same commitments to the fields as they
stand. Where the two versions differ in wording, the deposited text
governs. The registration is submitted on the day the protocol paper is
sent to arXiv, so that the registration link and date appear in the paper;
until then the paper cites "OSF registration, DOI to appear". No model has
been run at the time of registration.

# Page 1: Metadata

## Title

Qistas pilot: differential refusal, register effects, and stereotype
reliance of large language models across Iraqi social constituencies

## Description

Qistas is a protocol for evaluating how large language models (LLMs) treat
the social, confessional, and regional constituencies of a society. It
measures procedural properties only: whether a model's treatment of two
prompts that differ in one group variable is symmetric, whether it refuses
one arm of such a pair more than the other, and whether it relies on a
stereotype when a question has no supportable answer. It never adjudicates
contested truth and never ranks constituencies. The pilot registered here
is the first instantiation, for Iraq, in Arabic, with Modern Standard
Arabic and Iraqi Arabic as a register factor. The pilot evaluates ten to
twelve systems on the automatically scored axes of the protocol
(differential refusal, register twins, and stereotype reliance). The
quality-gap axis (pairwise comparison of generated text by human raters) is
run and archived but not scored under this registration; see "Other".

## Contributors

Nawar S. Alseelawi, University of Misan, Amarah, Iraq
(nawar.alseelawi@uomisan.edu.iq), administrator and bibliographic
contributor. Mustafa S. Aljumaily, Missan Oil Company, Amarah, Iraq
(mustafasadiq0@gmail.com), read-and-write and bibliographic contributor.

## Affiliated institutions

None (the University of Misan is not an OSF institutional member).

## License

CC-By Attribution 4.0 International.

## Subjects

Social and Behavioral Sciences: Linguistics. Physical Sciences and
Mathematics: Computer Sciences: Artificial Intelligence and Robotics.

## Tags

large language models; fairness evaluation; bias; Arabic; Iraqi Arabic;
preregistration; differential refusal; stereotype reliance; counterfactual
evaluation.

# Page 2: Overview

## Research questions or hypotheses

All hypotheses are tested per system; the pilot makes no claim about
"models in general". Each system is run twice, independently. Run 1 carries
the registered test and run 2 is a pre-registered direct replication. A
hypothesis is "supported for a system" only if the Holm-corrected test
rejects the null in both runs; a rejection in one run only is reported as
"not replicated".

H1 (directional). On factorial templates (templates authored as
semantically identical twins in Modern Standard Arabic and Iraqi Arabic),
pooled across domains, the Iraqi-register twin is refused more often than
its MSA twin. Null: the two discordant counts are equal in expectation.
Statistic: exact McNemar test on template twins, one-sided in the direction
"Iraqi refused more". Family: one test per system.

H2 (two-sided). Differential refusal exists between the two arms of
counterfactual pairs on at least one social axis. For each axis (regional
origin, rural/urban origin, class, gender, tribal affiliation, marital
status, ethno-regional origin, sect, religious community), pairs are pooled
across domains. Null: discordant counts equal in expectation. Statistic:
exact McNemar, two-sided. The "first arm" of every pair is the first-listed
value in the authored value list, which is disclosed with the frozen bank;
the direction of any detected asymmetry is reported. Family: systems x
axes.

H3 (directional). Register interacts with axis: on factorial templates,
the between-arm refusal difference is larger in the Iraqi register than in
MSA. For each factorial template the statistic is the difference of two
differences, (refusal of arm B minus arm A in Iraqi) minus (the same in
MSA), with refusal coded 0/1 per item after aggregation over repetitions.
Null: the mean of this difference is zero. Statistic: sign-flip permutation
test clustered by template, one-sided in the direction "larger in Iraqi".
Family: one test per system.

H4 (directional). On ambiguous stereotype-reliance items, the
stereotype-consistent share among committed answers exceeds 0.5. A
"committed answer" is a choice of one of the two named persons rather than
the "cannot be determined" option. Null: the share equals 0.5. Statistic:
exact one-sided binomial test on committed answers. Validity gate, applied
before testing: the system's accuracy on the disambiguated twins must be at
least 0.80; otherwise its H4 result is reported as "uninterpretable: fails
disambiguated accuracy gate" and no test is run. Family: one test per
system.

Not tested confirmatorily: any single-domain comparison; any comparison
between two named systems; any statement about the quality gap on the
counterfactual-pair axis; any comparison across systems of the size of an
effect. These are reported descriptively with intervals.

## Foreknowledge of data or evidence

Data does not yet exist. No part of the data that will be used for this
analysis plan exists, and no part will be generated until after this plan
is registered.

## Explanation of foreknowledge and managing unintended influences

No model output exists at the time of registration. Before the registered
runs, the pipeline will be exercised on two systems with a handful of
throw-away prompts solely to verify connectivity, logging, and the
verification certificate; those outputs are not part of the item bank, are
not scored, and are discarded. The analysis script is published before the
runs and executed as published.

# Page 3: Research Design

## Study type

Non-randomized study. There is no random assignment of systems to
conditions: every system receives every item, and the manipulation of the
group variable is fixed within each pair by authoring.

## Intention for causal interpretation

Indirect inference on causal relationship(s). The counterfactual pair
isolates the effect of the swapped variable on the model's behaviour, but
the pilot makes no claim about the mechanism (the emergence stage of a
detected asymmetry is a hypothesis for later work, not a registered test).

## Blinding of experimental treatments

Subjects will not be aware of the assigned treatment during data collection
(the systems are not informed of the measurement and the prompts contain no
reference to it). Researchers or observers who code or interpret data for
analysis will not be aware of the assigned treatments during coding (human
raters and coders are blind to the identity of the system).

## Additional blinding during research or analysis

Prompts contain no reference to the measurement (authoring rule R-005: no
prompt may name the criterion being measured). Human raters and coders are
blind to the identity of the system whose output they adjudicate; outputs
are presented under random identifiers. The authors are not blind to system
identity during analysis; the analysis is fully scripted and the script is
published before the runs and executed as published.

## Study design

Within-system paired design. Every item belongs to a template group; a
counterfactual pair consists of two items identical except for one group
variable. Factorial templates additionally carry an MSA/Iraqi register
twin, giving a 2 (group arm) x 2 (register) within-template factorial.
Stereotype-reliance items follow the BBQ ambiguous/disambiguated-twin
design. Every system receives every item under identical conditions
(identical prompts, identical decoding parameters declared in the run
certificate, identical retry ladder). All comparisons are within-system and
paired at the item or template level; there are no between-subject arms.

## Randomization

Order of items within a run is randomised with a seeded generator so that
repetitions of the same item are not adjacent. Answer-option positions in
stereotype-reliance items are balanced by design at authoring and audited
against uniformity with a chi-squared test before analysis; options are not
shuffled at run time. The random seed is recorded in each run certificate.

# Page 4: Sampling

## Data collection procedures

The item bank is authored natively in Arabic under the published authoring
guides, passes the automated structural audit (zero hard violations) and a
checklist-driven human semantic review, and is then frozen; the frozen
file's SHA-256 digest and the final system list are posted as a dated
addendum to this registration (as an uploaded file or a registration
update) before any run begins. Each system is queried through its provider
API or through an OpenAI-compatible self-hosted endpoint, three times per
item, in two complete independent runs, with the raw response envelope
archived for every attempt. Refusal is detected automatically from the
response text and, where available, from the provider's structured refusal
fields, with human verification on a 25% sample of refusal-axis responses.
Stereotype-reliance items are scored by exact answer-letter match.

## Sample size

Units: systems (ten to twelve; the final list is fixed in the addendum)
and, within each system, items. Item bank at freeze: 100 counterfactual
pairs (200 items); 60 ambiguous stereotype-reliance items with their 60
disambiguated twins; 50 differential-refusal pairs (100 items); 40 to 50
terminological-framing items; between 40% and 50% of templates carry a
register twin. Every system receives the same items, so sample sizes are
identical across systems. Three repetitions per item and two runs per
system.

## Sample size rationale

Computed minimum detectable effects at alpha = 0.05 and power 0.80, with a
design effect of 1.3 applied to pair-level statistics to account for two
pairs per factorial template at an assumed intra-template correlation of
0.3: counterfactual pairs, paired d_z of about 0.32 at the axis level
(about 0.52 for a 40-pair single-domain slice, which is why single-domain
slices are descriptive); differential refusal, with exact McNemar power a
function of discordant pairs, a split of about 84:16 among 15 discordant
pairs (30% discordance at 50 pairs), with the full dependence tabulated in
the protocol paper; stereotype reliance, a committed share of 0.72 at a 50%
commitment rate (30 trials), 0.66 at full commitment. The refusal axis was
enlarged from 30 to 50 pairs because at 30 pairs it could detect only
near-total one-sidedness. Any "no evidence" result is reported together
with these bounds.

## Starting and stopping rules

Start: data collection begins only after the item bank is frozen and its
SHA-256 digest and the system list are posted as the dated addendum; a
pipeline check on two systems with throw-away prompts precedes it and
produces no analysed data. Stop: data collection stops when both runs of
every listed system are complete, or when a system has exhausted the retry
ladder on more than 5% of its items, in which case that system is reported
as "incomplete" with its completed items analysed and the incompleteness
disclosed. No interim analysis is performed and no system is added or
removed after the addendum.

# Page 5: Variables

## Manipulated variables

Four within-system manipulations, all assigned by design (no randomization
of assignment):

1. Group arm of the counterfactual pair: the swapped value on the declared
   axis (regional origin, rural/urban origin, class, gender, tribal
   affiliation, marital status, parenthood, ethno-regional origin, sect,
   religious community). Two levels per pair; the "first arm" is the
   first-listed value in the authored value list, disclosed with the frozen
   bank.
2. Register, on factorial templates only: Modern Standard Arabic versus
   Iraqi Arabic, as semantically identical twins.
3. Context, on stereotype-reliance items: ambiguous (no supportable answer)
   versus disambiguated (a single decisive sentence replaces the
   no-information sentence).
4. Disambiguation direction, on stereotype-reliance templates: the decisive
   fact resolves with or against the prevalent stereotype, balanced across
   the bank.

## Measured variables

Per item and repetition: refusal (explicit or veiled, under the
coding-guide definitions; coded 0/1); for stereotype-reliance items, the
option chosen and whether it is the stereotype-consistent person, the other
person, or "cannot be determined"; for disambiguated twins, correctness of
the chosen option; technical outcome of the attempt (completed, empty,
truncated, failed after the retry ladder). Variables used for subsetting:
system identity, run number (1 or 2), test type, domain, axis, register,
sensitivity band of refusal pairs, template identifier.

## Indices

Per item: refusal is the majority outcome over the three repetitions
(refused in at least two of three); the stereotype-reliance choice is the
modal choice over repetitions, with ties recorded as "cannot be
determined". Per system and axis: refusal rate per arm with a 95% Wilson
interval and a template-clustered bootstrap interval; discordant-pair
counts for the McNemar tests (pairs where exactly one arm is refused); for
factorial templates, the difference of differences (refusal of arm B minus
arm A in Iraqi) minus (the same in MSA); commitment rate on ambiguous items
(share of answers naming one of the two persons); stereotype-consistent
share among committed answers; disambiguated accuracy (share of
disambiguated twins answered with the keyed option). Between runs: per-axis
agreement of item-level outcomes.

# Page 6: Analysis Plan

## Statistical models

H1 and H2: exact McNemar test on discordant pairs, that is an exact
binomial test of the discordant split against 0.5; one-sided for H1
(direction: Iraqi twin refused more), two-sided for H2. H3: sign-flip
permutation test on the per-template difference of differences, 10,000
resamples, template as the unit of resampling, one-sided (direction: larger
between-arm difference in Iraqi). H4: exact binomial test of the committed
stereotype-consistent count against 0.5, one-sided, run only after the
validity gate (disambiguated accuracy at least 0.80); a system failing the
gate is reported as "uninterpretable" and no H4 test is run for it. Every
proportion is reported with a 95% Wilson interval; every proportion
computed over template-generated items is additionally reported with a
template-clustered bootstrap interval (2,000 resamples). Effect sizes: the
discordant-pair odds for McNemar tests, paired d_z for the permutation
test, and the share itself with its interval for H4. No omnibus tests, no
regression models, no covariates. The analysis code is the published
metrics library and protocol analyser at the repository commit named in the
addendum, and is executed as published.

## Transformations

Refusal is coded 0/1 per attempt under the coding-guide definitions
(explicit and veiled refusal both coded 1). Stereotype-reliance answers are
coded as one of three categories (stereotype-consistent person, other
person, cannot be determined) by exact answer-letter match against the
keyed option order. Aggregation over the three repetitions follows the
rules stated under Indices (majority for refusal, mode for choice, ties to
"cannot be determined"). No other transformation, centering or recoding is
performed.

## Inference criteria

alpha = 0.05 after Holm correction within each family. Families: H1, one
test per system (family size = number of systems); H2, systems x axes; H3,
one test per system; H4, one test per system. Sidedness: H1, H3 and H4
one-sided in the stated direction; H2 two-sided. Sidedness will not be
changed after data are seen. A hypothesis is "supported for a system" only
if the Holm-corrected test rejects the null in both independent runs;
rejection in one run only is reported as "not replicated". No claim is made
about models in general, no system is compared with another
confirmatorily, and no composite score across domains or axes is computed.

## Data inclusion and exclusion

All items of the frozen bank and all listed systems are included. Attempts
that end empty or truncated by the provider's envelope after the retry
ladder are flagged and excluded from stereotype-reliance scoring; in
refusal metrics they count as non-refusals only if the response contains
substantive content before truncation, otherwise as technical failures
excluded from both. Deterministic provider-side refusals are counted as
refusals, not technical failures, and are not re-run. Items withdrawn after
the freeze (for example on discovery of an authoring defect) are withdrawn
publicly with their identifier, and their effect on every affected
statistic is reported. There is no outlier handling: the outcomes are
binary or categorical.

## Missing data

An item with no completed attempt in a run is missing for that run, and
its pair or template is dropped from the paired statistics of that run;
the count of dropped units is reported per axis and per system. A system
that exhausts the retry ladder on more than 5% of its items is reported as
"incomplete" with its completed items analysed and the incompleteness
disclosed. No imputation.

## Other planned analysis

Exploratory, reported with intervals and not corrected: single-domain
slices; descriptive comparison of refusal rates across the three
sensitivity bands of refusal pairs; distributions of watchlist terms on
terminological-framing items coded by two human coders, with Krippendorff's
alpha; explicit versus veiled refusal; between-run disagreement patterns;
descriptive quality-gap comparisons on the counterfactual-pair axis if
independent raters become available. All are labelled exploratory in the
report.

# Page 7: Other

## Context and additional information

Protocol and documents. This registration covers the first instantiation
of Qistas, a portable protocol for fairness evaluation of large language
models, for Iraq. The protocol paper (Qistas: A Pre-Registered, Portable
Protocol for Fairness Evaluation of Large Language Models, Alseelawi and
Aljumaily, 2026, to appear on arXiv) describes the taxonomy, the four test
types, the authoring guides, the rulings log, the structural audit and the
power analysis; the methodology, taxonomy and authoring-guide documents and
the reference implementation (metrics library, runner, analyser, audit,
review-notebook builder, rulings log, published tier of the item bank) will
be published in a public repository whose URL and commit hash are named in
the dated addendum. Qistas inherits its runner, integrity protocol (dated
snapshots, SHA-256 verification certificates) and dual-review practice from
the sibling project Mizan (arXiv:2609.13980).

Item bank and addendum. The bank is not frozen at registration. Its sizes
are registered as targets, and the power statements are given as functions
of size; the frozen bank's SHA-256 digest, the exact per-type counts, the
first-arm order of every pair, the final system list with versions and
decoding parameters, and the repository commit of the analysis code are
posted as a dated addendum to this registration before any registered run
begins. Half of the templates are held in a sealed tier that is never
published; the published half suffices to verify the structure of the
bank.

Second-author audit. Items enter the bank on the first author's checklist
verdict; before the freeze the second author audits a stratified sample of
20 to 25 percent of template groups without access to the first author's
verdicts. One documented design disagreement between the authors (whether
naming the two groups in an ambiguous-choice item is itself a cue, and
whether naming a sect in a refusal pair changes its legitimacy) is recorded
in the public rulings log and carried to that audit; it does not change the
registered design.

Axes run but not scored under this registration. The quality-gap axis
(pairwise comparison of generated text on counterfactual pairs by human
raters against a rubric) is run and archived but is not scored here; the
rubric, its calibration sample and the agreement threshold will be
registered as a dated amendment before any quality adjudication begins, and
only after independent raters are secured. The terminological-framing items
are coded by the two authors (author-coders, no independent raters) and
reported descriptively with coder agreement; no confirmatory hypothesis is
registered for them. Human adjudication in the pilot covers all framing
items, a 25% sample of refusal-axis responses and, after the amendment, a
15% calibration sample of counterfactual-pair outputs, each by two raters.

Reporting constraints. Results are reported per system and per domain as
scorecards with intervals; no ranking of systems, no composite score across
domains or axes, and no characterisation of any system as "neutral" or
"biased" in the absolute. Systems whose intervals overlap are reported as a
single statistical tie tier, and every symmetry metric is displayed with
its companion response-rate indicator. Fairness is understood procedurally
(symmetry of treatment, balance, transparency), never as a verdict on
contested truth, and the protocol never ranks the constituencies it
studies.

Deviations. Any departure from this registration is recorded in a public
deviation appendix with date, reason and effect, and in the project's
rulings log.

Competing interests. Both authors are members of the national technical
team building Iraq's first large language model. Any system in which an
author has a role is marked as such on every scorecard.

Disclosure. An LLM research assistant was used throughout the project for
drafting and tooling, including the drafting of this registration from the
authors' decisions; every design decision and every item verdict is the
authors' own and is recorded in the rulings log. No model has been
evaluated at the time of registration.

# Addendum (to be posted before the first registered run)

Date of freeze; SHA-256 digest of the frozen internal bank and of the
published tier; per-type item counts; first-arm order of every pair;
system list with provider, version string, decoding parameters and
endpoint type; repository URL and commit hash of the analysis code; random
seeds of both runs.
