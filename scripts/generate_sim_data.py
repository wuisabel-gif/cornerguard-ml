#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cornerguard_ml.bicycle_model import simulate_corner_run
from cornerguard_ml.io import write_telemetry_csv
from cornerguard_ml.labeling import future_labels


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic CornerGuard telemetry.")
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--duration-s", type=float, default=8.0)
    parser.add_argument("--dt-s", type=float, default=0.01)
    parser.add_argument("--out", default="data/processed/simulated_cornering.csv")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = []
    counts: Counter[str] = Counter()

    for run_id in range(args.runs):
        samples = simulate_corner_run(
            run_id=run_id,
            duration_s=args.duration_s,
            dt_s=args.dt_s,
            seed=args.seed + run_id,
        )
        labels = future_labels(samples, horizon_s=1.0, dt_s=args.dt_s)
        for sample, (label, probability) in zip(samples, labels):
            rows.append((sample, label, probability))
            counts[label.name.lower()] += 1

    write_telemetry_csv(args.out, rows)
    print(f"wrote {len(rows)} rows to {args.out}")
    print(dict(counts))


if __name__ == "__main__":
    main()
