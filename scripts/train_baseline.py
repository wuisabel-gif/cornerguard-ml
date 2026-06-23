#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cornerguard_ml.features import feature_names, window_features
from cornerguard_ml.telemetry import TelemetrySample


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a CornerGuard baseline classifier.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--model-out", default="models/cornerguard_baseline.joblib")
    parser.add_argument("--window-s", type=float, default=2.0)
    parser.add_argument("--dt-s", type=float, default=0.01)
    return parser.parse_args()


def load_rows(path: str) -> tuple[list[TelemetrySample], list[str]]:
    samples: list[TelemetrySample] = []
    labels: list[str] = []
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if not row.get("label"):
                continue
            samples.append(
                TelemetrySample(
                    time_s=float(row["time_s"]),
                    speed_mps=float(row["speed_mps"]),
                    steering_angle_rad=float(row["steering_angle_rad"]),
                    steering_rate_radps=float(row["steering_rate_radps"]),
                    yaw_rate_radps=float(row["yaw_rate_radps"]),
                    lateral_accel_mps2=float(row["lateral_accel_mps2"]),
                    throttle=float(row.get("throttle") or 0.0),
                    brake=float(row.get("brake") or 0.0),
                )
            )
            labels.append(row["label"])
    return samples, labels


def main() -> None:
    try:
        import joblib
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import classification_report
        from sklearn.model_selection import train_test_split
    except ImportError as exc:
        raise SystemExit(
            "Missing ML dependencies. Run: pip install -e '.[ml]'"
        ) from exc

    args = parse_args()
    samples, labels = load_rows(args.data)
    window_steps = max(1, round(args.window_s / args.dt_s))
    names = feature_names()
    x_rows = []
    y_rows = []

    for idx in range(window_steps, len(samples)):
        features = window_features(samples[idx - window_steps : idx])
        x_rows.append([features[name] for name in names])
        y_rows.append(labels[idx])

    x_train, x_test, y_train, y_test = train_test_split(
        x_rows,
        y_rows,
        test_size=0.25,
        random_state=7,
        stratify=y_rows,
    )
    model = RandomForestClassifier(
        n_estimators=250,
        max_depth=12,
        min_samples_leaf=4,
        class_weight="balanced",
        random_state=7,
        n_jobs=-1,
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    print(classification_report(y_test, predictions))

    Path(args.model_out).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "feature_names": names, "window_steps": window_steps}, args.model_out)
    print(f"saved model to {args.model_out}")


if __name__ == "__main__":
    main()
