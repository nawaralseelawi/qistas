#!/usr/bin/env python3
"""Qistas analysis (Phase 8) -- per-domain scorecard builder, v0.2.

Inputs:
  dataset.csv   item bank with pair_id links (the pairing structure).
  scores.csv    scored trials, one row per item, with at least:
                item_id, rubric_overall_score (1-5), refused (0/1).

Output: a Markdown scorecard, one section per domain, following the binding
reporting rules (GENOME M-4, M-5, DL-013):

* Paired parity gaps with template-clustered bootstrap CIs (the pair/template
  id is the cluster: items sharing a pair_id are not independent).
* Differential refusal per domain via the exact McNemar test -- v0.2 fixes a
  v0.1 defect in which refusal data were collected but never analysed.
* Holm step-down correction across domains (primary), with plain Bonferroni
  shown alongside for comparability.
* No aggregate single number is ever produced; groups with insufficient
  pairs are reported as such, never silently averaged in.
* Pair orientation is deterministic: within each pair, condition A is the
  lexicographically smaller swapped_value, so re-runs assign sides
  identically and the sign of every gap is reproducible.

Version: 0.2.0 (supersedes impl-v0.1-mustafa/analyze_results.py)
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "metrics"))
from metrics import (bonferroni_correct, differential_refusal_rate,
                     holm_correct, parity_gap, wilson_interval)

MIN_PAIRS = 2  # below this, a domain is reported as insufficient, not scored


def load_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def orient_pair(items: dict, id_x: str, id_y: str) -> tuple[str, str]:
    """Deterministic A/B assignment inside a pair (see module docstring)."""
    kx = (items[id_x].get("swapped_value", ""), id_x)
    ky = (items[id_y].get("swapped_value", ""), id_y)
    return (id_x, id_y) if kx <= ky else (id_y, id_x)


def build_scorecard(dataset_path: str, scores_path: str, out_path: str) -> None:
    items = {i["id"]: i for i in load_csv(dataset_path)}
    scores = {s["item_id"]: s for s in load_csv(scores_path)}

    pairs = defaultdict(list)
    for item_id, item in items.items():
        pairs[item["pair_id"]].append(item_id)

    # domain -> parallel lists over usable pairs
    gaps = defaultdict(lambda: {"a": [], "b": [], "cluster": []})
    refusals = defaultdict(lambda: {"a": [], "b": [], "cluster": []})
    skipped_groups = defaultdict(int)  # pair groups with != 2 members

    for pair_id, ids in pairs.items():
        if len(ids) != 2:
            # Groups of 3+ variants need a different design (reported, not
            # forced into an incorrect pairwise comparison).
            skipped_groups[items[ids[0]]["domain"]] += 1
            continue
        a_id, b_id = orient_pair(items, ids[0], ids[1])
        if a_id not in scores or b_id not in scores:
            continue
        domain = items[a_id]["domain"]
        try:
            sa = float(scores[a_id]["rubric_overall_score"])
            sb = float(scores[b_id]["rubric_overall_score"])
        except (KeyError, ValueError):
            sa = sb = None
        if sa is not None:
            gaps[domain]["a"].append(sa)
            gaps[domain]["b"].append(sb)
            gaps[domain]["cluster"].append(pair_id)
        try:
            ra = int(scores[a_id]["refused"])
            rb = int(scores[b_id]["refused"])
        except (KeyError, ValueError):
            ra = rb = None
        if ra is not None:
            refusals[domain]["a"].append(ra)
            refusals[domain]["b"].append(rb)
            refusals[domain]["cluster"].append(pair_id)

    lines = ["# Qistas Scorecard (per-domain; no aggregate number by design)",
             ""]
    p_values, p_labels = [], []

    for domain in sorted(set(list(gaps) + list(refusals) + list(skipped_groups))):
        lines.append(f"## {domain}")
        lines.append("")

        g = gaps.get(domain)
        if g and len(g["a"]) >= MIN_PAIRS:
            r = parity_gap(g["a"], g["b"], cluster_ids=g["cluster"])
            p_values.append(r.p_value)
            p_labels.append(f"{domain} / parity_gap")
            lines.append(f"- {r.summary()}")
        elif g and g["a"]:
            lines.append(f"- parity_gap: insufficient pairs "
                         f"(n={len(g['a'])} < {MIN_PAIRS}) -- not scored")

        rr = refusals.get(domain)
        if rr and len(rr["a"]) >= MIN_PAIRS:
            r = differential_refusal_rate(rr["a"], rr["b"],
                                          cluster_ids=rr["cluster"])
            p_values.append(r.p_value)
            p_labels.append(f"{domain} / differential_refusal")
            n = len(rr["a"])
            ka, kb = sum(rr["a"]), sum(rr["b"])
            wa, wb = wilson_interval(ka, n), wilson_interval(kb, n)
            lines.append(f"- {r.summary()}")
            lines.append(f"  - refusal rate A: {ka}/{n} "
                         f"[Wilson {wa[0]:.3f}, {wa[1]:.3f}]; "
                         f"refusal rate B: {kb}/{n} "
                         f"[Wilson {wb[0]:.3f}, {wb[1]:.3f}]")
        elif rr and rr["a"]:
            lines.append(f"- differential_refusal: insufficient pairs "
                         f"(n={len(rr['a'])} < {MIN_PAIRS}) -- not scored")

        if skipped_groups.get(domain):
            lines.append(f"- note: {skipped_groups[domain]} template group(s) "
                         f"with 3+ variants excluded from pairwise analysis "
                         f"(require a multi-arm design)")
        lines.append("")

    if p_values:
        holm = holm_correct(p_values)
        bonf = bonferroni_correct(p_values)
        lines.append("## Multiple-comparison correction across domains")
        lines.append("")
        lines.append("| comparison | raw p | Holm (primary) | Bonferroni |"
                     " significant after Holm |")
        lines.append("|---|---|---|---|---|")
        for label, p, ph, pb in zip(p_labels, p_values, holm, bonf):
            sig = "yes" if ph < 0.05 else "no"
            lines.append(f"| {label} | {p:.4f} | {ph:.4f} | {pb:.4f} | {sig} |")
        lines.append("")

    if not p_values:
        had_pairs = any(g["a"] for g in gaps.values()) or \
                    any(r["a"] for r in refusals.values())
        if had_pairs:
            lines.append(f"_Pairs exist but no domain reached the minimum of "
                         f"{MIN_PAIRS} scorable pairs; expand the bank before "
                         f"drawing any conclusion._")
        else:
            lines.append("_No analysable paired data found: run "
                         "run_protocol.py and complete human scoring "
                         "(rubric_appendix_b.xlsx) first._")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"scorecard written to {out_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--dataset", default="../dataset/dataset.csv")
    p.add_argument("--scores", required=True)
    p.add_argument("--out", default="scorecard.md")
    args = p.parse_args()
    build_scorecard(args.dataset, args.scores, args.out)
