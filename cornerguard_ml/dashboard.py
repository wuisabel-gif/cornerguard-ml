from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from statistics import fmean

from .features import sample_to_values
from .io import read_telemetry_csv


REQUIRED_COLUMNS = {
    "time_s",
    "speed_mps",
    "steering_angle_rad",
    "steering_rate_radps",
    "yaw_rate_radps",
    "lateral_accel_mps2",
}

LABEL_COLORS = {
    "stable": "#22B26B",
    "warning": "#F6B017",
    "critical": "#E5251D",
    "unknown": "#6F6658",
}


def csv_columns(path: str | Path) -> set[str]:
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        return set(reader.fieldnames or [])


def validate_dashboard_csv(path: str | Path) -> None:
    missing = sorted(REQUIRED_COLUMNS - csv_columns(path))
    if missing:
        raise ValueError(f"missing required telemetry columns: {', '.join(missing)}")


def load_dashboard_rows(path: str | Path) -> list[dict[str, float | str]]:
    validate_dashboard_csv(path)
    samples = read_telemetry_csv(path)
    labels_by_time: dict[float, tuple[str, float]] = {}

    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            time_s = float(row["time_s"])
            label = (row.get("label") or "unknown").strip().lower() or "unknown"
            probability_raw = row.get("loss_of_control_probability") or ""
            probability = float(probability_raw) if probability_raw else 0.0
            labels_by_time[time_s] = (label, probability)

    rows: list[dict[str, float | str]] = []
    for sample in samples:
        values = sample_to_values(sample)
        label, probability = labels_by_time.get(sample.time_s, ("unknown", 0.0))
        rows.append(
            {
                "time_s": sample.time_s,
                "speed_mps": sample.speed_mps,
                "speed_mph": sample.speed_mps * 2.2369362921,
                "steering_angle_deg": sample.steering_angle_rad * 57.2957795131,
                "steering_rate_degps": sample.steering_rate_radps * 57.2957795131,
                "yaw_rate_degps": sample.yaw_rate_radps * 57.2957795131,
                "lateral_accel_g": sample.lateral_accel_mps2 / 9.80665,
                "yaw_error_degps": values["yaw_error_radps"] * 57.2957795131,
                "throttle": sample.throttle,
                "brake": sample.brake,
                "label": label,
                "loss_of_control_probability": probability,
            }
        )
    return rows


def summarize_dashboard_rows(rows: list[dict[str, float | str]]) -> dict[str, float | int | str]:
    if not rows:
        return {
            "samples": 0,
            "duration_s": 0.0,
            "peak_risk": 0.0,
            "peak_speed_mph": 0.0,
            "peak_lateral_g": 0.0,
            "dominant_state": "unknown",
        }

    labels = Counter(str(row.get("label") or "unknown") for row in rows)
    duration_s = float(rows[-1]["time_s"]) - float(rows[0]["time_s"])
    return {
        "samples": len(rows),
        "duration_s": duration_s,
        "peak_risk": max(float(row["loss_of_control_probability"]) for row in rows),
        "mean_risk": fmean(float(row["loss_of_control_probability"]) for row in rows),
        "peak_speed_mph": max(float(row["speed_mph"]) for row in rows),
        "peak_lateral_g": max(abs(float(row["lateral_accel_g"])) for row in rows),
        "dominant_state": labels.most_common(1)[0][0],
    }
