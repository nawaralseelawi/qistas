#!/usr/bin/env python3
"""Tests for the v0.2 analyzer's scored branch, using temp fixtures with a
planted asymmetry. Verifies: paired parity gaps with clustered CIs, exact
McNemar on refusals (the v0.1 dead-data defect), the Holm/Bonferroni table,
Wilson interval lines, multi-arm exclusion notes, and deterministic pair
orientation. Run: python3 test_analyzer.py
"""
import csv
import os
import tempfile

from analyze_results import build_scorecard, orient_pair

FIELDS = ["id", "pair_id", "domain", "bias_form", "test_type",
          "reference_category", "test_text", "swapped_variable",
          "swapped_value", "language_dialect", "paraphrase_variant_id",
          "references", "reviewers", "status", "notes"]


def _write_fixtures(tmp):
    dataset, scores = [], []
    # Domain D1: 8 pairs with a planted parity gap (A always scores higher)
    # and a planted one-directional refusal asymmetry (B refuses, A never).
    for k in range(8):
        pid = f"PX{k:02d}"
        for side, sval in (("a", "group_A"), ("b", "group_B")):
            iid = f"D1-{k:02d}-{side}"
            dataset.append(dict.fromkeys(FIELDS, ""))
            dataset[-1].update({"id": iid, "pair_id": pid, "domain": "D1",
                                "swapped_value": sval, "test_text": "x"})
            scores.append({"item_id": iid,
                           "rubric_overall_score": 4.5 if side == "a" else 2.5,
                           "refused": 0 if side == "a" else 1})
    # Domain D2: a 3-variant group -> must be excluded with a note.
    for j, sval in enumerate(["v1", "v2", "v3"]):
        iid = f"D2-{j}"
        dataset.append(dict.fromkeys(FIELDS, ""))
        dataset[-1].update({"id": iid, "pair_id": "PTRIPLE", "domain": "D2",
                            "swapped_value": sval, "test_text": "y"})
        scores.append({"item_id": iid, "rubric_overall_score": 3.0,
                       "refused": 0})

    dpath = os.path.join(tmp, "dataset.csv")
    spath = os.path.join(tmp, "scores.csv")
    with open(dpath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(dataset)
    with open(spath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["item_id", "rubric_overall_score",
                                          "refused"])
        w.writeheader()
        w.writerows(scores)
    return dpath, spath


def test_scored_branch_end_to_end():
    with tempfile.TemporaryDirectory() as tmp:
        dpath, spath = _write_fixtures(tmp)
        out = os.path.join(tmp, "scorecard.md")
        build_scorecard(dpath, spath, out)
        card = open(out, encoding="utf-8").read()

    assert "parity_gap: gap=2.000" in card, "planted 2.0 gap must be reported"
    assert "cluster-bootstrap CI" in card, "pair-clustered CI must be used"
    assert "exact McNemar" in card, \
        "refusal data must reach the McNemar test (v0.1 dead-data defect)"
    assert "refusal rate A: 0/8" in card and "refusal rate B: 8/8" in card
    assert "Wilson" in card
    assert "Holm (primary)" in card and "Bonferroni" in card
    assert "| yes |" in card, "planted asymmetries must survive Holm"
    assert "3+ variants excluded" in card, "multi-arm groups must be noted"
    assert "no aggregate single number" in card.lower() or \
           "no aggregate number" in card.lower()


def test_orientation_is_deterministic():
    items = {"i1": {"swapped_value": "beta"}, "i2": {"swapped_value": "alpha"}}
    assert orient_pair(items, "i1", "i2") == ("i2", "i1")
    assert orient_pair(items, "i2", "i1") == ("i2", "i1"), \
        "orientation must not depend on input order"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"PASS  {t.__name__}")
    print(f"\n{passed}/{len(tests)} tests passed")
