#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cornerguard_ml.features import window_features
from cornerguard_ml.io import read_telemetry_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay telemetry through a trained model.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--critical-threshold", type=float, default=0.65)
    parser.add_argument("--warning-threshold", type=float, default=0.35)
    return parser.parse_args()


def main() -> None:
    try:
        import joblib
    except ImportError as exc:
        raise SystemExit("Missing ML dependencies. Run: pip install -e '.[ml]'") from exc

    args = parse_args()
    bundle = joblib.load(args.model)
    model = bundle["model"]
    names = bundle["feature_names"]
    window_steps = bundle["window_steps"]
    window = deque(maxlen=window_steps)

    for sample in read_telemetry_csv(args.data):
        window.append(sample)
        if len(window) < window_steps:
            continue
        features = window_features(window)
        x_row = [[features[name] for name in names]]
        probabilities = dict(zip(model.classes_, model.predict_proba(x_row)[0]))
        risk = probabilities.get("critical", 0.0) + 0.5 * probabilities.get("warning", 0.0)
        if risk >= args.critical_threshold:
            state = "critical"
        elif risk >= args.warning_threshold:
            state = "warning"
        else:
            state = "stable"
        print(f"{sample.time_s:7.2f}s {state:8s} risk={risk:.2f} speed={sample.speed_mps:5.1f}m/s")


if __name__ == "__main__":
    main()
