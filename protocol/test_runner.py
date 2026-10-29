#!/usr/bin/env python3
"""Offline tests for the v0.2 runner: ladder, classification, and evidence
preservation, verified against a stubbed transport (no network required).
Run: python3 test_runner.py
"""
import run_protocol as rp


def _ok_envelope(text="answer"):
    return {"choices": [{"finish_reason": "stop",
                         "message": {"content": text}}]}


def _empty_envelope():
    return {"choices": [{"finish_reason": "length",
                         "message": {"content": ""}}]}


def _refusal_envelope():
    return {"choices": [{"finish_reason": "content_filter",
                         "message": {"content": "", "refusal": "policy"}}]}


class _Script:
    """call_endpoint stub that plays back a scripted sequence of outcomes
    and records the max_tokens budget of every attempt."""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.budgets = []

    def __call__(self, base_url, api_key, model, item_text, system_prompt,
                 temperature, max_tokens, timeout=120.0):
        self.budgets.append(max_tokens)
        return self.outcomes.pop(0)


def _run_ladder(script):
    logged = []
    rp.time.sleep = lambda s: None  # no waiting in tests
    original = rp.call_endpoint
    rp.call_endpoint = script
    try:
        result = rp.run_trial_with_ladder("http://x", "k", "m", "q", "",
                                          0.0, logged.append)
    finally:
        rp.call_endpoint = original
    return result, logged


def test_ok_first_attempt():
    script = _Script([("ok", _ok_envelope())])
    (status, env, recoveries), logged = _run_ladder(script)
    assert status == "ok" and not recoveries and not logged
    assert script.budgets == [rp.BASE_MAX_TOKENS]


def test_empty_then_recovered_at_escalated_budget():
    script = _Script([("empty", _empty_envelope()), ("ok", _ok_envelope())])
    (status, env, recoveries), logged = _run_ladder(script)
    assert status == "ok"
    assert script.budgets == [rp.BASE_MAX_TOKENS, rp.ESCALATED_MAX_TOKENS]
    assert any(r["type"] == "recovery" for r in logged), \
        "every recovery must be logged (audit-trail requirement)"


def test_transient_exhausts_ladder():
    script = _Script([("transient", {"http_status": 503})] * 3)
    (status, env, recoveries), logged = _run_ladder(script)
    assert status == "unrecovered_transient"
    assert len(script.budgets) == 1 + rp.MAX_ESCALATIONS
    assert sum(1 for r in logged if r["type"] == "ladder_step") == 3


def test_refusal_short_circuits_no_retry():
    script = _Script([("refusal", _refusal_envelope())])
    (status, env, recoveries), logged = _run_ladder(script)
    assert status == "refusal"
    assert script.budgets == [rp.BASE_MAX_TOKENS], \
        "a deterministic refusal must not be retried"
    assert env["choices"][0]["finish_reason"] == "content_filter", \
        "the raw envelope (material evidence) must be preserved"


def test_classification_rules():
    class FakeResp:
        def __init__(self, status_code, body):
            self.status_code = status_code
            self._body = body
            self.text = "raw"

        def json(self):
            return self._body

    calls = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        calls["max_tokens"] = json["max_tokens"]
        return FakeResp(*calls["next"])

    original_post = rp.requests.post
    rp.requests.post = fake_post
    try:
        calls["next"] = (200, _refusal_envelope())
        s, _ = rp.call_endpoint("http://x", "k", "m", "q", "", 0.0, 100)
        assert s == "refusal"

        calls["next"] = (200, _empty_envelope())
        s, _ = rp.call_endpoint("http://x", "k", "m", "q", "", 0.0, 100)
        assert s == "empty"

        calls["next"] = (429, {"error": "rate"})
        s, _ = rp.call_endpoint("http://x", "k", "m", "q", "", 0.0, 100)
        assert s == "transient"

        calls["next"] = (400, {"error": "policy"})
        s, _ = rp.call_endpoint("http://x", "k", "m", "q", "", 0.0, 100)
        assert s == "refusal", "non-transient HTTP errors are deterministic"

        calls["next"] = (200, _ok_envelope("text"))
        s, env = rp.call_endpoint("http://x", "k", "m", "q", "", 0.0, 100)
        assert s == "ok" and rp.extract_text(env) == "text"
    finally:
        rp.requests.post = original_post


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"PASS  {t.__name__}")
    print(f"\n{passed}/{len(tests)} tests passed")
