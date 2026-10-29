#!/usr/bin/env python3
"""Inter-reviewer agreement for the semantic review of the seed bank.

Compares two review-notebook exports (same template set) and reports:
  - verdict agreement: raw agreement and Cohen's kappa on the three-way
    verdict (accepted / needs_fix / rejected), plus the binary collapse
    (accepted vs. not accepted);
  - per-check agreement: for each checklist item of each type, raw
    agreement on "failed / not failed" across templates of that type;
  - the list of templates where the two verdicts differ, with both notes.

Usage:
    python3 review_agreement.py review_pass1_results.json review_pass1_results_mustafa.json
Output is identifiers, counts, and notes only - no item text.
"""
import json
import sys
from collections import Counter, defaultdict


def cohen_kappa(a, b, labels):
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum((ca[l] / n) * (cb[l] / n) for l in labels)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    r1 = json.load(open(sys.argv[1], encoding="utf-8"))
    r2 = json.load(open(sys.argv[2], encoding="utf-8"))
    m1 = {x["template_id"]: x for x in r1["results"]}
    m2 = {x["template_id"]: x for x in r2["results"]}
    common = sorted(set(m1) & set(m2))
    only1, only2 = sorted(set(m1) - set(m2)), sorted(set(m2) - set(m1))
    judged = [t for t in common if m1[t]["verdict"] and m2[t]["verdict"]]

    print(f"reviewers: {r1.get('reviewer')} vs {r2.get('reviewer')}")
    print(f"templates in common: {len(common)}; judged by both: {len(judged)}")
    if only1 or only2:
        print(f"  only in first: {only1}\n  only in second: {only2}")

    v1 = [m1[t]["verdict"] for t in judged]
    v2 = [m2[t]["verdict"] for t in judged]
    labels3 = ["accepted", "needs_fix", "rejected"]
    raw3 = sum(1 for x, y in zip(v1, v2) if x == y) / max(1, len(judged))
    k3 = cohen_kappa(v1, v2, labels3)
    b1 = ["acc" if v == "accepted" else "not" for v in v1]
    b2 = ["acc" if v == "accepted" else "not" for v in v2]
    k2 = cohen_kappa(b1, b2, ["acc", "not"])
    # Cohen's kappa collapses when both reviewers use one category for most
    # templates (the prevalence paradox), so the prevalence-robust companions
    # are reported alongside it: PABAK = 2*po - 1 and Gwet's AC1.
    def gwet_ac1(a, b, labels):
        n = len(a)
        if n == 0:
            return float("nan")
        po = sum(1 for x, y in zip(a, b) if x == y) / n
        pi = {l: (a.count(l) + b.count(l)) / (2 * n) for l in labels}
        q = len(labels)
        pe = sum(pi[l] * (1 - pi[l]) for l in labels) / (q - 1) if q > 1 else 0.0
        return (po - pe) / (1 - pe) if pe < 1 else 1.0
    raw2 = sum(1 for x, y in zip(b1, b2) if x == y) / max(1, len(judged))
    print(f"\nVERDICT (3-way): raw agreement {raw3:.2f}, Cohen's kappa {k3:.2f}, "
          f"PABAK {2*raw3-1:.2f}, Gwet AC1 {gwet_ac1(v1, v2, labels3):.2f}")
    print(f"VERDICT (accepted vs not): raw agreement {raw2:.2f}, Cohen's kappa {k2:.2f}, "
          f"PABAK {2*raw2-1:.2f}, Gwet AC1 {gwet_ac1(b1, b2, ['acc', 'not']):.2f}")

    # Instrument-consistency flags (what the v1 notebook allowed and v2 forbids)
    for name, m in (("reviewer 1", m1), ("reviewer 2", m2)):
        acc_fail = [t for t in judged if m[t]["verdict"] == "accepted" and m[t]["failed_checks"]]
        no_note = [t for t in judged if m[t]["verdict"] in ("needs_fix", "rejected") and not (m[t].get("note") or "").strip()]
        print(f"  consistency {name}: accepted-with-failed-checks={len(acc_fail)}, "
              f"non-acceptance-without-note={len(no_note)}")
    print("  verdict counts reviewer 1:", dict(Counter(v1)))
    print("  verdict counts reviewer 2:", dict(Counter(v2)))

    # per-check agreement
    by_type = defaultdict(list)
    for t in judged:
        by_type[m1[t]["type"]].append(t)
    print("\nPER-CHECK agreement (failed / not failed), by type:")
    for typ, tpls in sorted(by_type.items()):
        checks = sorted({c for t in tpls for c in m1[t]["failed_checks"] + m2[t]["failed_checks"]})
        if not checks:
            print(f"  {typ}: no failed checks recorded by either reviewer on {len(tpls)} templates")
            continue
        for c in checks:
            f1 = [c in m1[t]["failed_checks"] for t in tpls]
            f2 = [c in m2[t]["failed_checks"] for t in tpls]
            agree = sum(1 for x, y in zip(f1, f2) if x == y) / len(tpls)
            print(f"  {c}: raw agreement {agree:.2f} over {len(tpls)} templates "
                  f"(flagged by r1={sum(f1)}, r2={sum(f2)}, both={sum(1 for x, y in zip(f1, f2) if x and y)})")

    # pooled check-level agreement over every (template, check) decision
    NCHECKS = {"T1": 6, "T2": 6, "T3": 5, "T4": 4}
    f1_all, f2_all = [], []
    for t in judged:
        typ = m1[t]["type"]
        for i in range(1, NCHECKS.get(typ, 0) + 1):
            c = f"{typ}-{i}"
            f1_all.append("fail" if c in m1[t]["failed_checks"] else "pass")
            f2_all.append("fail" if c in m2[t]["failed_checks"] else "pass")
    if f1_all:
        pooled = sum(1 for x, y in zip(f1_all, f2_all) if x == y) / len(f1_all)
        print(f"\nPOOLED CHECK DECISIONS: {len(f1_all)} decisions, raw agreement {pooled:.2f}, "
              f"PABAK {2*pooled-1:.2f}, Gwet AC1 {gwet_ac1(f1_all, f2_all, ['fail', 'pass']):.2f}; "
              f"flagged by r1={f1_all.count('fail')}, r2={f2_all.count('fail')}, "
              f"both={sum(1 for x, y in zip(f1_all, f2_all) if x == y == 'fail')}")

    print("\nDISAGREEMENTS (verdict differs):")
    diffs = [t for t in judged if m1[t]["verdict"] != m2[t]["verdict"]]
    if not diffs:
        print("  none")
    for t in diffs:
        print(f"  {t}: r1={m1[t]['verdict']} {m1[t]['failed_checks']} | r2={m2[t]['verdict']} {m2[t]['failed_checks']}")
        if m1[t].get("note"):
            print(f"     r1 note: {m1[t]['note']}")
        if m2[t].get("note"):
            print(f"     r2 note: {m2[t]['note']}")


if __name__ == "__main__":
    main()
