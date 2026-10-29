#!/usr/bin/env python3
"""Extended metrics tests, v0.3 — ported to English from the parallel v0.2
implementation line (17 tests, finer-grained coverage of the primitives) and
adapted to the canonical contracts: wilson_interval returns (lo, hi);
discordance detail comes from mcnemar_detail. Run: python3 test_metrics_extended.py
"""
import numpy as np

from metrics import (bonferroni_correct, cohens_dz, holm_correction,
                     mcnemar_detail, mcnemar_exact, position_balance_chi2,
                     sign_flip_permutation_test,
                     template_clustered_bootstrap_ci, wilson_interval)


def test_wilson_matches_phat_center_roughly():
    lo, hi = wilson_interval(50, 100)
    assert lo < 0.5 < hi
    assert abs((lo + hi) / 2 - 0.5) < 0.01


def test_wilson_interval_narrows_with_more_data():
    lo1, hi1 = wilson_interval(5, 10)
    lo2, hi2 = wilson_interval(500, 1000)
    assert (hi2 - lo2) < (hi1 - lo1)


def test_wilson_handles_zero_successes_without_negative_bound():
    lo, hi = wilson_interval(0, 30)
    assert lo == 0.0 and 0 < hi < 0.2


def test_wilson_handles_all_successes_without_exceeding_one():
    lo, hi = wilson_interval(30, 30)
    assert 1.0 - 1e-9 <= hi <= 1.0 and 0.8 < lo < 1.0


def test_mcnemar_no_discordant_pairs_gives_p_one():
    d = mcnemar_detail([1, 0, 1, 0], [1, 0, 1, 0])
    assert d["n_discordant"] == 0 and d["p_value"] == 1.0


def test_mcnemar_detects_strong_asymmetric_refusal():
    a = [1] * 12 + [0] * 8
    b = [0] * 20
    d = mcnemar_detail(a, b)
    assert d["b_discordant"] == 12 and d["c_discordant"] == 0
    assert d["p_value"] < 0.001
    assert d["rate_a"] == 0.6 and d["rate_b"] == 0.0


def test_mcnemar_symmetric_discordance_not_significant():
    a = [1, 0, 1, 0, 1, 0]
    b = [0, 1, 0, 1, 0, 1]
    assert mcnemar_exact(a, b) == 1.0


def test_permutation_no_effect_not_significant():
    # Deterministic sign-balanced differences: true effect is exactly zero,
    # so the test must not report significance (no seed lottery).
    diffs = np.array([0.8, -0.8, 1.2, -1.2, 0.5, -0.5, 0.3, -0.3,
                      1.0, -1.0, 0.7, -0.7, 0.4, -0.4, 0.9, -0.9])
    assert sign_flip_permutation_test(diffs) > 0.5


def test_permutation_strong_consistent_effect_significant():
    diffs = np.full(20, 1.0) + np.random.default_rng(3).normal(0, 0.1, 20)
    assert sign_flip_permutation_test(diffs) < 0.01


def test_cluster_bootstrap_uses_template_count_not_item_count():
    # 2 templates x 20 items each, constant within template: effective n = 2,
    # so the CI must be wide despite 40 items.
    tids = np.array(["t1"] * 20 + ["t2"] * 20)
    diffs = np.array([1.0] * 20 + [3.0] * 20)
    lo, hi = template_clustered_bootstrap_ci(tids, diffs)
    assert (hi - lo) > 1.0


def test_cluster_bootstrap_wider_than_naive_when_templates_repeated():
    from metrics import bootstrap_ci
    tids = np.array(["t1"] * 15 + ["t2"] * 15 + ["t3"] * 15)
    rng = np.random.default_rng(11)
    diffs = np.concatenate([rng.normal(m, 0.05, 15) for m in (0.5, 1.5, 2.5)])
    lo_c, hi_c = template_clustered_bootstrap_ci(tids, diffs)
    lo_i, hi_i = bootstrap_ci(diffs)
    assert (hi_c - lo_c) >= (hi_i - lo_i) - 1e-9


def test_cohens_dz_zero_for_no_variation():
    assert cohens_dz([0.0, 0.0, 0.0, 0.0]) == 0.0


def test_cohens_dz_positive_for_consistent_positive_diffs():
    assert cohens_dz([1.0, 1.1, 0.9, 1.05, 0.95]) > 5.0


def test_holm_never_more_conservative_than_bonferroni():
    p = [0.001, 0.011, 0.02, 0.04, 0.2]
    holm = holm_correction(p)
    bonf = bonferroni_correct(p)
    assert all(h <= b + 1e-12 for h, b in zip(holm, bonf))


def test_holm_is_monotonic_nondecreasing_by_rank():
    p = [0.03, 0.001, 0.2, 0.011]
    holm = holm_correction(p)
    order = np.argsort(p)
    ranked = [holm[i] for i in order]
    assert all(ranked[i] <= ranked[i + 1] + 1e-12 for i in range(len(ranked) - 1))


def test_chi2_uniform_positions_not_flagged():
    stat, p = position_balance_chi2([25, 25, 25, 25])
    assert stat == 0.0 and p > 0.99


def test_chi2_skewed_positions_flagged():
    stat, p = position_balance_chi2([70, 10, 10, 10])
    assert p < 0.001


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"PASS  {t.__name__}")
    print(f"\n{passed}/{len(tests)} tests passed")
