#!/usr/bin/env python3
"""Seed-bank structural audit, v1 (recalibration step 1 of the procedure in
the approved authoring-guides document, section 9).

Runs every automatable check from the approved taxonomy matrix and authoring
guides against the seed CSV and prints a report of COUNTS AND IDS ONLY —
item text is never printed, so the report is safe to share in any channel.

Hard violations (exit code 1) break binding rules and block an item from
dual review. Warnings are recalibration work items for the human pass.

Usage:
    python3 audit_seed_bank.py [path-to-internal-csv]
"""
import csv
import glob
import json
import os
import sys
import unicodedata
from collections import Counter, defaultdict

DEFAULT_PATH = "dataset_internal_FULL_DO_NOT_PUBLISH.csv"

REQUIRED_FIELDS = [
    "id", "template_id", "domain", "bias_form", "test_type",
    "reference_category", "test_text", "swapped_variable", "swapped_value",
    "register", "region_tag", "layer", "correct_position",
    "reviewers", "agreement", "status", "notes",
]

# Cells closed by design in the approved matrix (domain x bias_form).
CLOSED_CELLS = {
    ("D2_religious_communal", "representational"),
    ("D2_religious_communal", "framing_language"),
    ("D3_historical_political", "unequal_refusal"),
    ("D3_historical_political", "representational"),
}

VALID_DOMAINS = {"D1_social_regional", "D2_religious_communal",
                 "D3_historical_political"}
VALID_FORMS = {"asymmetry", "unequal_refusal", "representational",
               "framing_language"}
VALID_TYPES = {"T1", "T2", "T2_disambiguated", "T3", "T4"}
REGISTER_MSA = "\u0641\u0635\u062d\u0649"          # MSA register value
REGISTER_IRAQI = "\u0639\u0631\u0627\u0642\u064a\u0629"  # Iraqi register value


def nfc(s):
    return unicodedata.normalize("NFC", (s or "").strip())


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    hard = []   # (check, ids)
    warn = []   # (check, detail)
    info = []

    # The published file carries sealed-tier rows with their text and value
    # replaced by a redaction marker. Those rows cannot pass content checks
    # by construction, so they are counted and set aside; the full audit
    # runs on the internal file.
    REDACTED_PREFIX = "[محجوب"  # "[redacted" marker
    redacted = [r for r in rows if nfc(r["test_text"]).startswith(REDACTED_PREFIX)]
    if redacted:
        info.append(f"redacted sealed-tier rows set aside ({len(redacted)}); "
                    "content checks run on the published tier only")
        rows = [r for r in rows if r not in redacted]

    # ---- schema ----------------------------------------------------------
    missing_cols = [c for c in REQUIRED_FIELDS if c not in rows[0]]
    if missing_cols:
        hard.append(("missing required columns", missing_cols))
    if "disambig_direction" not in rows[0]:
        warn.append(("schema gap vs authoring guides 7.2",
                     "no disambig_direction column"))
    else:
        tpl_missing = sorted({nfc(r["template_id"]) for r in rows
                              if nfc(r["test_type"]).startswith("T2")
                              and not nfc(r["disambig_direction"])})
        if tpl_missing:
            warn.append(("T2 templates awaiting disambig_direction "
                         "(human pass)", tpl_missing))
    if "sensitivity_level" not in rows[0]:
        warn.append(("schema gap vs authoring guides 7.2",
                     "no sensitivity_level column"))
    else:
        t3_missing = sorted(nfc(r["id"]) for r in rows
                            if nfc(r["test_type"]) == "T3"
                            and not nfc(r["sensitivity_level"]))
        if t3_missing:
            warn.append(("T3 items awaiting sensitivity_level "
                         "(human pass)", t3_missing))

    for col in ("term_watchlist", "event_ref"):
        if col in rows[0]:
            missing = sorted(nfc(r["id"]) for r in rows
                             if nfc(r["test_type"]) == "T4" and not nfc(r[col]))
            if missing:
                warn.append((f"T4 items awaiting {col} (authoring)", missing))
        else:
            warn.append(("schema gap vs authoring guides 7.2", f"no {col} column"))

    # ---- row-level hard checks ------------------------------------------
    ids = [nfc(r["id"]) for r in rows]
    dupes = [i for i, n in Counter(ids).items() if n > 1]
    if dupes:
        hard.append(("duplicate ids", dupes))

    VALID_DIRECTION = {"with_stereotype", "against_stereotype"}
    VALID_SENSITIVITY = {"innocuous", "moderate", "sensitive"}
    FORM_OF_TYPE = {"T1": "asymmetry", "T2": "representational",
                    "T2_disambiguated": "representational",
                    "T3": "unequal_refusal", "T4": "framing_language"}
    CANNOT = "\u0644\u0627 \u064a\u0645\u0643\u0646"  # cannot-determine marker
    import re as _re
    bad_enum, closed_hits, d3_nonfact, empty_text = [], [], [], []
    t2_missing_pos, nont2_with_pos = [], []
    form_type_mismatch, t2_key_mismatch = [], []
    bad_direction, bad_sensitivity = [], []
    for r in rows:
        rid = nfc(r["id"])
        dom, form, ttype = nfc(r["domain"]), nfc(r["bias_form"]), nfc(r["test_type"])
        if dom not in VALID_DOMAINS or form not in VALID_FORMS or ttype not in VALID_TYPES:
            bad_enum.append(rid)
        if (dom, form) in CLOSED_CELLS:
            closed_hits.append(rid)
        if dom == "D3_historical_political" and nfc(r["reference_category"]) != "verifiable_fact":
            d3_nonfact.append(rid)
        if not nfc(r["test_text"]):
            empty_text.append(rid)
        pos = nfc(r["correct_position"])
        if ttype.startswith("T2") and not pos:
            t2_missing_pos.append(rid)
        if not ttype.startswith("T2") and pos:
            nont2_with_pos.append(rid)
        dd = nfc(r.get("disambig_direction", ""))
        if dd and dd not in VALID_DIRECTION:
            bad_direction.append(rid)
        sl = nfc(r.get("sensitivity_level", ""))
        if sl and sl not in VALID_SENSITIVITY:
            bad_sensitivity.append(rid)
        if ttype in FORM_OF_TYPE and form != FORM_OF_TYPE[ttype]:
            form_type_mismatch.append(rid)
        if ttype.startswith("T2") and pos:
            # locate the option letter that carries the cannot-determine body
            m = _re.search(r"\(([\u0623\u0628\u062c])\)\s*[^()]*?" + CANNOT,
                           nfc(r["test_text"]))
            cannot_letter = m.group(1) if m else None
            if cannot_letter is None:
                t2_key_mismatch.append(rid + ":no-cannot-option")
            elif ttype == "T2" and pos != cannot_letter:
                t2_key_mismatch.append(rid)
            elif ttype == "T2_disambiguated" and pos == cannot_letter:
                t2_key_mismatch.append(rid)

    for name, lst in [("invalid enum values", bad_enum),
                      ("items in CLOSED matrix cells", closed_hits),
                      ("D3 items not verifiable_fact", d3_nonfact),
                      ("empty test_text", empty_text),
                      ("T2 items missing correct_position", t2_missing_pos),
                      ("bias_form does not match its test_type binding",
                       form_type_mismatch),
                      ("invalid disambig_direction value", bad_direction),
                      ("invalid sensitivity_level value", bad_sensitivity),
                      ("T2 answer key inconsistent with option text "
                       "(ambiguous must key the cannot-determine option; "
                       "disambiguated must not)", t2_key_mismatch)]:
        if lst:
            hard.append((name, lst))
    if nont2_with_pos:
        warn.append(("non-T2 items carrying correct_position", nont2_with_pos))

    # ---- T2 twin pairing -------------------------------------------------
    t2a = defaultdict(list)
    t2d = defaultdict(list)
    for r in rows:
        t = nfc(r["test_type"])
        if t == "T2":
            t2a[nfc(r["template_id"])].append(nfc(r["id"]))
        elif t == "T2_disambiguated":
            t2d[nfc(r["template_id"])].append(nfc(r["id"]))
    orphans_a = sorted(tpl for tpl in t2a if tpl not in t2d)
    orphans_d = sorted(tpl for tpl in t2d if tpl not in t2a)
    if orphans_a:
        hard.append(("T2 ambiguous templates without disambiguated twin", orphans_a))
    if orphans_d:
        hard.append(("T2 disambiguated templates without ambiguous twin", orphans_d))

    # ---- pair completeness for T1 / T3 ----------------------------------
    unpaired = []
    for ttype in ("T1", "T3"):
        groups = defaultdict(set)
        for r in rows:
            if nfc(r["test_type"]) == ttype:
                key = (nfc(r["template_id"]), nfc(r["register"]))
                groups[key].add(nfc(r["swapped_value"]))
        for (tpl, reg), vals in sorted(groups.items()):
            if len(vals) < 2:
                unpaired.append(f"{ttype}:{tpl}:{reg.encode('unicode_escape').decode()}")
    if unpaired:
        hard.append(("T1/T3 template-register groups with a single swapped "
                     "value (no counterpart)", unpaired))

    # ---- register and region tags ----------------------------------------
    iraqi_no_region = [nfc(r["id"]) for r in rows
                       if nfc(r["register"]) == REGISTER_IRAQI
                       and not nfc(r["region_tag"])]
    if iraqi_no_region:
        warn.append(("Iraqi-register items missing region_tag", iraqi_no_region))

    # placeholder twins: Iraqi-register rows whose text is a bracketed stub
    # ("[Iraqi equivalent of template ...]" + MSA text) are not authored yet
    PLACEHOLDER_PREFIX = "[\u0646\u0633\u062e\u0629 \u0639\u0631\u0627\u0642\u064a\u0629"
    placeholder_ids = sorted(nfc(r["id"]) for r in rows
                             if nfc(r["register"]) == REGISTER_IRAQI
                             and nfc(r["test_text"]).startswith(PLACEHOLDER_PREFIX))
    if placeholder_ids:
        warn.append(("Iraqi twins that are placeholders (unauthored; "
                     "excluded from factorial coverage)", placeholder_ids))

    # factorial coverage: templates represented in BOTH registers with REAL twins
    regs_per_tpl = defaultdict(set)
    for r in rows:
        if nfc(r["id"]) in placeholder_ids:
            continue
        regs_per_tpl.setdefault(nfc(r["template_id"]), set())
        regs_per_tpl[nfc(r["template_id"])].add(nfc(r["register"]))
    n_tpl = len(regs_per_tpl)
    n_fact = sum(1 for s in regs_per_tpl.values()
                 if {REGISTER_MSA, REGISTER_IRAQI} <= s)
    pct = 100.0 * n_fact / n_tpl if n_tpl else 0.0
    line = f"factorial (both-register) templates: {n_fact}/{n_tpl} = {pct:.0f}% (target band 40-50%)"
    (info if 40.0 <= pct <= 50.0 else warn).append(
        ("factorial coverage", line) if not 40.0 <= pct <= 50.0 else line)

    # ---- T2 correct-position balance -------------------------------------
    pos_counts = Counter(nfc(r["correct_position"]) for r in rows
                         if nfc(r["test_type"]).startswith("T2")
                         and nfc(r["correct_position"]))
    counts = [pos_counts.get(k, 0) for k in sorted(pos_counts)]
    try:
        sys.path.insert(0, "../metrics")
        from metrics import chi_square_uniformity
        res = chi_square_uniformity(counts)
        msg = (f"T2 correct-position counts {counts}: chi2={res['chi_square']:.2f}, "
               f"p={res['p_value'] if res['p_value'] is not None else 'n/a (scipy missing)'}")
        if res["p_value"] is not None and res["p_value"] < 0.05:
            warn.append(("T2 position balance", msg))
        else:
            info.append(msg)
    except Exception as e:  # pragma: no cover
        warn.append(("T2 position balance not computed", f"{type(e).__name__}: {e}"))

    # ---- semantic-review log (template-level verdicts) --------------------
    # The builder's verdicts are layered: the seed review (pass 1) first, then
    # every E1 authoring-batch review in file-name order. A later verdict on a
    # template supersedes an earlier one, and an "accepted" verdict in a later
    # layer marks the earlier fix as resolved. The second reviewer's
    # independent exports (*_mustafa*) measure agreement and are not layered.
    review_dir = os.path.dirname(os.path.abspath(path))
    review_path = os.path.join(review_dir, "review_pass1_results.json")
    layers = []
    if os.path.exists(review_path):
        layers.append(review_path)
    layers += sorted(glob.glob(os.path.join(review_dir, "review_e1_*results.json")))
    if layers:
        verdicts, fix_status = {}, {}
        for lp in layers:
            with open(lp, encoding="utf-8") as rf:
                review = json.load(rf)
            later = lp != review_path
            for x in review.get("results", []):
                if not x.get("verdict"):
                    continue
                t = x["template_id"]
                verdicts[t] = x["verdict"]
                if later and x["verdict"] == "accepted":
                    fix_status[t] = "resolved"
                elif later:
                    fix_status[t] = "open"
                else:
                    fix_status[t] = x.get("fix_status", "open")
        all_tpls = sorted({nfc(r["template_id"]) for r in rows})
        unjudged = [t for t in all_tpls if not verdicts.get(t)]
        counts = Counter(verdicts.get(t) for t in all_tpls if verdicts.get(t))
        info.append("semantic review (seed pass 1 + "
                    f"{len(layers) - (1 if os.path.exists(review_path) else 0)} E1 layer(s)), "
                    "latest verdict per template: "
                    + ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
                    + f" (of {len(all_tpls)} templates)")
        if unjudged:
            warn.append(("templates with no semantic-review verdict", unjudged))
        verdicts = {t: v for t, v in verdicts.items() if t in all_tpls}
        fixes_open = sorted(t for t, v in verdicts.items()
                            if v == "needs_fix" and fix_status.get(t) != "resolved")
        resolved = sorted(t for t, v in verdicts.items()
                          if v == "needs_fix" and fix_status.get(t) == "resolved")
        if resolved:
            info.append(f"fix verdicts resolved ({len(resolved)}): " + ", ".join(resolved))
        if fixes_open:
            warn.append((f"templates with open or partial fix verdicts ({len(fixes_open)})",
                         fixes_open))
        rejected = sorted(t for t, v in verdicts.items() if v == "rejected")
        if rejected:
            hard.append(("rejected templates still present in the bank", rejected))
    else:
        warn.append(("no semantic-review log found",
                     "dataset/review_pass1_results.json missing"))

    # ---- crosstab for the human pass --------------------------------------
    cross = Counter((nfc(r["domain"]), nfc(r["test_type"])) for r in rows)
    info.append("domain x test_type counts: "
                + "; ".join(f"{d}/{t}={n}" for (d, t), n in sorted(cross.items())))
    ACTIVE_CELLS = [
        ("D1_social_regional", "asymmetry"), ("D1_social_regional", "unequal_refusal"),
        ("D1_social_regional", "representational"), ("D1_social_regional", "framing_language"),
        ("D2_religious_communal", "asymmetry"), ("D2_religious_communal", "unequal_refusal"),
        ("D3_historical_political", "asymmetry"), ("D3_historical_political", "framing_language"),
    ]
    cell_counts = Counter((nfc(r["domain"]), nfc(r["bias_form"])) for r in rows)
    uncovered = [f"{d[:2]}x{f}" for d, f in ACTIVE_CELLS if cell_counts.get((d, f), 0) == 0]
    info.append("active matrix cells with ZERO seed items (authoring worklist): "
                + (", ".join(uncovered) if uncovered else "none"))
    if "disambig_direction" in rows[0]:
        dir_by_tpl = {}
        for r in rows:
            if nfc(r["test_type"]).startswith("T2") and nfc(r["disambig_direction"]):
                dir_by_tpl[nfc(r["template_id"])] = nfc(r["disambig_direction"])
        n_with = sum(1 for v in dir_by_tpl.values() if v == "with_stereotype")
        n_against = len(dir_by_tpl) - n_with
        if dir_by_tpl:
            msg = (f"T2 disambiguation-direction split: {n_with} with / "
                   f"{n_against} against (guides require a half-split "
                   "across the bank)")
            if abs(n_with - n_against) > 1:
                warn.append(("T2 direction parity broken (authoring "
                             "worklist: add against-stereotype twins)", msg))
            else:
                info.append(msg)
    if "sensitivity_level" in rows[0]:
        lvl = Counter(nfc(r["sensitivity_level"]) for r in rows
                      if nfc(r["test_type"]) == "T3"
                      and nfc(r["sensitivity_level"]))
        if lvl:
            missing = [x for x in ("innocuous", "moderate", "sensitive")
                       if lvl.get(x, 0) == 0]
            msg = ("T3 sensitivity gradient counts: "
                   + ", ".join(f"{k}={v}" for k, v in sorted(lvl.items())))
            if missing:
                warn.append(("T3 gradient bands empty (authoring worklist): "
                             + ", ".join(missing), msg))
            else:
                info.append(msg)
    refcat = Counter((nfc(r["domain"]), nfc(r["reference_category"])) for r in rows)
    info.append("domain x reference_category counts: "
                + "; ".join(f"{d}/{c}={n}" for (d, c), n in sorted(refcat.items())))

    # ---- report -----------------------------------------------------------
    print(f"SEED AUDIT — {path} — {len(rows)} rows")
    print(f"\nHARD VIOLATIONS: {len(hard)}")
    for name, detail in hard:
        print(f"  [FAIL] {name}: {detail}")
    print(f"\nWARNINGS (recalibration work items): {len(warn)}")
    for item in warn:
        name, detail = item if isinstance(item, tuple) else ("note", item)
        print(f"  [WARN] {name}: {detail}")
    print("\nINFO:")
    for line in info:
        print(f"  [INFO] {line}")
    sys.exit(1 if hard else 0)


if __name__ == "__main__":
    main()
