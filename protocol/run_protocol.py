#!/usr/bin/env python3
"""Qistas run protocol (Phase 7) -- evaluation runner, v0.2.

Design contract (inherited from the Mizan runner, QISTAS_GENOME 2.2):

* Provider-agnostic: speaks to ANY OpenAI-compatible chat-completions
  endpoint via a configurable --base-url, which covers commercial APIs and
  self-hosted quantized models alike. No vendor lock-in.
* Uniform conditions: identical prompts, identical settings, and an explicit
  completion-budget ladder for every model. Temperature is a REQUIRED
  argument -- a protocol decision, never a silent default.
* Failure ladder (one-sentence policy): transient failures are retried and
  recovered; deterministic refusals are recorded as refusals on the affected
  items and reported separately as over-refusal. The ladder is: base
  max-tokens, then up to two retries at the escalated budget with backoff,
  each recovery logged so the run log is a complete audit trail.
* Evidence preservation: the FULL raw response envelope (finish_reason,
  refusal fields, usage, everything the endpoint returns) is written to the
  JSONL log for every trial. For the differential-refusal axis (T3) the
  official envelope is the material evidence -- it must never be discarded.
* Provenance: a self-describing manifest (schema qistas-results-v1) records
  the runner version, endpoint, model, settings, seed, and the SHA-256 of the
  exact dataset file used, so every published score maps to one immutable
  input.

Authentication: the API key is read from the QISTAS_API_KEY environment
variable (fallback: OPENAI_API_KEY). It is never written to the log.

Usage:
    python3 run_protocol.py \
        --dataset ../dataset/dataset.csv \
        --base-url https://api.example.com/v1 \
        --model some-model-id \
        --temperature 0.0 \
        --repeats 3 \
        --out runs/run_$(date -u +%Y%m%dT%H%M%SZ).jsonl

Dependencies: requests.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import time
from datetime import datetime, timezone

import requests

RUNNER_VERSION = "qistas-runner-0.2.0"
RESULTS_SCHEMA = "qistas-results-v1"
BASE_MAX_TOKENS = 2048        # base completion budget (Mizan convention)
ESCALATED_MAX_TOKENS = 8192   # ladder budget on empty/transient outcomes
MAX_ESCALATIONS = 2           # retries at the escalated budget
BACKOFF_SECONDS = (2.0, 8.0)  # backoff before each escalation
TRANSIENT_HTTP = {408, 409, 425, 429, 500, 502, 503, 504}
REFUSAL_FINISH_REASONS = {"content_filter", "refusal"}


def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_items(dataset_path: str) -> list[dict]:
    with open(dataset_path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def get_api_key() -> str:
    key = os.environ.get("QISTAS_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("set QISTAS_API_KEY (or OPENAI_API_KEY) in the "
                         "environment; the key is never logged")
    return key


def call_endpoint(base_url: str, api_key: str, model: str, item_text: str,
                  system_prompt: str, temperature: float, max_tokens: int,
                  timeout: float = 120.0) -> tuple[str, dict]:
    """Single POST to an OpenAI-compatible /chat/completions endpoint.

    Returns (classification, envelope) where classification is one of:
    "ok", "empty", "refusal", "transient". The envelope is the parsed raw
    response body (or an error descriptor) and is ALWAYS preserved by the
    caller in the run log.
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": item_text})
    try:
        resp = requests.post(
            base_url.rstrip("/") + "/chat/completions",
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": "application/json"},
            json={"model": model, "messages": messages,
                  "temperature": temperature, "max_tokens": max_tokens},
            timeout=timeout,
        )
    except requests.RequestException as exc:
        return "transient", {"transport_error": str(exc)}

    if resp.status_code in TRANSIENT_HTTP:
        return "transient", {"http_status": resp.status_code,
                             "body": _safe_json(resp)}
    if resp.status_code != 200:
        # Non-transient API error (auth, bad request, policy block at the
        # HTTP layer). Treated as deterministic for this item; preserved raw.
        return "refusal", {"http_status": resp.status_code,
                           "body": _safe_json(resp)}

    envelope = _safe_json(resp)
    choice = (envelope.get("choices") or [{}])[0]
    finish = str(choice.get("finish_reason") or "").lower()
    message = choice.get("message") or {}
    text = message.get("content") or ""
    refusal_field = message.get("refusal")

    if finish in REFUSAL_FINISH_REASONS or refusal_field:
        return "refusal", envelope
    if not text.strip():
        return "empty", envelope
    return "ok", envelope


def _safe_json(resp: requests.Response) -> dict:
    try:
        return resp.json()
    except ValueError:
        return {"non_json_body": resp.text[:20000]}


def extract_text(envelope: dict) -> str:
    choice = (envelope.get("choices") or [{}])[0]
    return ((choice.get("message") or {}).get("content")) or ""


def run_trial_with_ladder(base_url: str, api_key: str, model: str,
                          item_text: str, system_prompt: str,
                          temperature: float, log_fn) -> tuple[str, dict, list]:
    """Execute one trial under the failure ladder.

    Attempt 1 uses the base budget. On "empty" or "transient", up to
    MAX_ESCALATIONS retries run at the escalated budget with backoff, each
    step logged so the JSONL constitutes a complete audit trail. A "refusal"
    classification is deterministic by policy and returns immediately:
    retrying a policy refusal would only blur the over-refusal measurement.
    """
    ladder = [BASE_MAX_TOKENS] + [ESCALATED_MAX_TOKENS] * MAX_ESCALATIONS
    recoveries = []
    status, envelope = "transient", {}
    for attempt, budget in enumerate(ladder):
        if attempt > 0:
            time.sleep(BACKOFF_SECONDS[min(attempt - 1,
                                           len(BACKOFF_SECONDS) - 1)])
        status, envelope = call_endpoint(base_url, api_key, model, item_text,
                                         system_prompt, temperature, budget)
        if status == "refusal":
            return status, envelope, recoveries
        if status == "ok":
            if attempt > 0:
                recoveries.append({"attempt": attempt, "budget": budget,
                                   "recovered_from": last_status})
                log_fn({"type": "recovery", "attempt": attempt,
                        "budget": budget, "recovered_from": last_status})
            return status, envelope, recoveries
        last_status = status  # "empty" or "transient" -> continue the ladder
        log_fn({"type": "ladder_step", "attempt": attempt, "budget": budget,
                "outcome": status})
    # Ladder exhausted without success or refusal.
    return ("unrecovered_" + status), envelope, recoveries


def run(dataset_path: str, base_url: str, model: str, repeats: int,
        system_prompt: str, temperature: float, out_path: str,
        seed: int) -> None:
    api_key = get_api_key()
    items = load_items(dataset_path)
    rng = random.Random(seed)

    manifest = {
        "type": "manifest",
        "schema": RESULTS_SCHEMA,
        "runner_version": RUNNER_VERSION,
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "base_url": base_url,
        "model": model,
        "temperature": temperature,
        "system_prompt": system_prompt,
        "repeats": repeats,
        "seed": seed,
        "n_items": len(items),
        "dataset_path": os.path.abspath(dataset_path),
        "dataset_sha256": sha256_of_file(dataset_path),
        "budget_ladder": {"base": BASE_MAX_TOKENS,
                          "escalated": ESCALATED_MAX_TOKENS,
                          "max_escalations": MAX_ESCALATIONS},
        "failure_policy": ("transient failures are retried and recovered; "
                           "deterministic refusals are recorded as refusals "
                           "and reported separately as over-refusal"),
    }

    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)

    with open(out_path, "a", encoding="utf-8") as f:  # append-only audit log

        def log(record: dict) -> None:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()

        log(manifest)

        # Shuffle (item, repeat) trials so repeats of one item never run
        # back-to-back and order effects are spread across the run.
        trials = [(item, rep) for item in items for rep in range(repeats)]
        rng.shuffle(trials)

        for item, rep in trials:
            started = datetime.now(timezone.utc).isoformat()
            status, envelope, recoveries = run_trial_with_ladder(
                base_url, api_key, model, item["test_text"], system_prompt,
                temperature, log)
            log({
                "type": "trial",
                "run_id": manifest["run_id"],
                "item_id": item["id"],
                "pair_id": item["pair_id"],
                "domain": item["domain"],
                "repeat_index": rep,
                "timestamp": started,
                "status": status,             # ok | refusal | unrecovered_*
                "output_text": extract_text(envelope) if status == "ok" else None,
                "n_recoveries": len(recoveries),
                "raw_envelope": envelope,     # material evidence -- never drop
            })
            time.sleep(0.2)  # basic rate-limit courtesy between trials

    print(f"run complete: {len(trials)} trials -> {out_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--dataset", default="../dataset/dataset.csv")
    p.add_argument("--base-url", required=True,
                   help="OpenAI-compatible endpoint root, e.g. "
                        "https://api.example.com/v1 or a local server")
    p.add_argument("--model", required=True)
    p.add_argument("--temperature", type=float, required=True,
                   help="protocol decision -- must be explicit, no default")
    p.add_argument("--repeats", type=int, default=3,
                   help="repetitions per item (GENOME 3.5 default: 3)")
    p.add_argument("--system-prompt", default="")
    p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    run(args.dataset, args.base_url, args.model, args.repeats,
        args.system_prompt, args.temperature, args.out, args.seed)
