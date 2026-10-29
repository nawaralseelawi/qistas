#!/usr/bin/env python3
"""Unit tests for the Qistas metrics library (v0.2).

Preserves the semantics of the eight v0.1 tests and adds coverage for the
machinery introduced in v0.2: Wilson intervals, exact McNemar, Holm
correction, template-clustered bootstrap, and the chi-square position audit.
Run: python3 test_metrics.py
"""
import numpy as np

from metrics import (bonferroni_correct, bootstrap_ci, bootstrap_ci_clustered,
                     chi_square_uniformity, cohens_d_paired,
                     differential_refusal_rate, holm_correct, mcnemar_exact,
                     narrative_diversity, parity_gap, permutation_test_paired,
                     stereotype_rate, sycophancy_rate, wilson_interval)


# --- v0.1 semantics, preserved ---------------------------------------------

def test_no_gap_when_identical():
    a = [4, 4, 5, 3, 4, 5, 4, 3]
    r = parity_gap(a, a)
    assert abs(r.gap) < 1e-9
    assert r.p_value > 0.5, "identical data must not look significant"


def test_detects_real_gap():
    rng = np.random.default_rng(0)
    a = rng.normal(4.2, 0.3, 60)
    b = rng.normal(3.0, 0.3, 60)
    r = parity_gap(a, b)
    assert r.gap > 0.8
    assert r.p_value < 0.01, "a large real gap must be detected"
    assert r.ci_low > 0, "CI must exclude zero for a clearly real gap"


def test_small_noise_not_significant():
    rng = np.random.default_rng(1)
    a = rng.normal(4.0, 1.0, 8)
    b = rng.normal(4.0, 1.0, 8)
    r = parity_gap(a, b)
    assert r.p_value > 0.05, "noise in a small sample must not be significant"


def test_stereotype_rate_bounds():
    rate, ci = stereotype_rate([1, 1, 1, 0, 0])
    assert rate == 0.6
    assert 0 <= ci[0] <= ci[1] <= 1


def test_refusal_rate_symmetric_zero():
    r = differential_refusal_rate([0, 1, 0, 1], [0, 1, 0, 1])
    assert r.gap == 0
    assert r.p_value == 1.0, "no discordant pairs -> McNemar p must be 1"


def test_bonferroni_caps_at_one():
    out = bonferroni_correct([0.3, 0.4, 0.5])
    assert all(p <= 1.0 for p in out)
    assert out[0] == min(1.0, 0.3 * 3)


def test_cohens_d_zero_when_no_diff():
    assert cohens_d_paired([0, 0, 0, 0]) == 0.0


def test_narrative_diversity_ratio():
    assert narrative_diversity([2, 2, 2], 2) == 1.0
    assert narrative_diversity([1, 1], 2) == 0.5


# --- v0.2 additions --------------------------------------------------------

def test_wilson_known_value():
    # 0 successes out of 0 -> undefined; 5/10 -> symmetric around 0.5.
    lo, hi = wilson_interval(5, 10)
    assert abs((lo + hi) / 2 - 0.5) < 1e-9
    assert 0.23 < lo < 0.24 and 0.76 < hi < 0.77  # canonical Wilson values
    lo0, hi0 = wilson_interval(0, 20)
    assert lo0 == 0.0 and hi0 < 0.2, "boundary case must stay inside [0,1]"


def test_mcnemar_detects_asymmetry():
    # 10 discordant pairs, all in one direction -> strongly significant.
    a = [1] * 10 + [0] * 10
    b = [0] * 10 + [0] * 10
    p = mcnemar_exact(a, b)
    assert p < 0.01
    # Balanced discordance -> no evidence of asymmetry.
    a2 = [1, 0, 1, 0]
    b2 = [0, 1, 0, 1]
    assert mcnemar_exact(a2, b2) == 1.0


def test_differential_refusal_uses_mcnemar():
    r = differential_refusal_rate([1] * 8 + [0] * 2, [0] * 10)
    assert r.p_method == "exact McNemar"
    assert r.p_value < 0.05
    assert r.gap == 0.8


def test_holm_monotone_and_leq_bonferroni():
    p = [0.01, 0.02, 0.04, 0.30]
    holm = holm_correct(p)
    bonf = bonferroni_correct(p)
    assert all(h <= b + 1e-12 for h, b in zip(holm, bonf)), \
        "Holm must never be more conservative than Bonferroni"
    order = np.argsort(p)
    adj_sorted = [holm[i] for i in order]
    assert all(adj_sorted[i] <= adj_sorted[i + 1] + 1e-12
               for i in range(len(adj_sorted) - 1)), "Holm must be monotone"
    assert all(x <= 1.0 for x in holm)


def test_clustered_ci_respects_dependence():
    # Two clusters with identical internal values: only two effective
    # observations, so the cluster CI must be at least as wide as the naive
    # item-level CI computed on the same data.
    values = np.array([1.0] * 20 + [3.0] * 20)
    clusters = np.array(["t1"] * 20 + ["t2"] * 20)
    lo_i, hi_i = bootstrap_ci(values)
    lo_c, hi_c = bootstrap_ci_clustered(values, clusters)
    assert (hi_c - lo_c) >= (hi_i - lo_i) - 1e-9
    assert (hi_c - lo_c) > 1.0, "two effective clusters -> wide interval"


def test_parity_gap_clustered_flag():
    a = [4, 4, 3, 3, 5, 5]
    b = [3, 3, 3, 3, 4, 4]
    r = parity_gap(a, b, cluster_ids=["t1", "t1", "t2", "t2", "t3", "t3"])
    assert r.clustered is True
    assert r.n_pairs == 6


def test_chi_square_uniformity_audit():
    res_uniform = chi_square_uniformity([25, 25, 25, 25])
    assert res_uniform["chi_square"] == 0.0 and res_uniform["df"] == 3
    res_skewed = chi_square_uniformity([70, 10, 10, 10])
    assert res_skewed["chi_square"] > 7.81  # 95% critical value at df=3
    if res_skewed["p_value"] is not None:
        assert res_skewed["p_value"] < 0.05


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"PASS  {t.__name__}")
    print(f"\n{passed}/{len(tests)} tests passed")
