#!/usr/bin/env python3
"""Generates SYNTHETIC random scores for the pipeline smoke test.

The output represents NO real model and must never be cited as a research
result; its only purpose is to prove the full pipeline (dataset -> scores ->
paired statistics -> scorecard) runs end to end. Deterministic under --seed.

Usage: python3 make_smoke_scores.py --dataset ../dataset/dataset.csv \
           --out smoke_test_synthetic_scores.csv --seed 0
"""
import argparse
import csv
import random


def main(dataset_path: str, out_path: str, seed: int) -> None:
    rng = random.Random(seed)
    with open(dataset_path, encoding="utf-8-sig") as f:
        items = list(csv.DictReader(f))
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["item_id", "rubric_overall_score",
                                          "refused", "synthetic"])
        w.writeheader()
        for item in items:
            w.writerow({
                "item_id": item["id"],
                "rubric_overall_score": round(rng.uniform(1.0, 5.0), 2),
                "refused": 1 if rng.random() < 0.1 else 0,
                "synthetic": "yes",  # explicit marker on every row
            })
    print(f"synthetic scores for {len(items)} items -> {out_path} "
          f"(SYNTHETIC -- not a research result)")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--dataset", default="../dataset/dataset.csv")
    p.add_argument("--out", default="smoke_test_synthetic_scores.csv")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()
    main(args.dataset, args.out, args.seed)
