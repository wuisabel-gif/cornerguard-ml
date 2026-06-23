from __future__ import annotations

import csv
from pathlib import Path

from .telemetry import TELEMETRY_FIELDS, StabilityLabel, TelemetrySample


def write_telemetry_csv(
    path: str | Path,
    rows: list[tuple[TelemetrySample, StabilityLabel | None, float | None]],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = TELEMETRY_FIELDS + ["label", "loss_of_control_probability"]

    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for sample, label, probability in rows:
            row = {field: getattr(sample, field) for field in TELEMETRY_FIELDS}
            row["label"] = "" if label is None else label.name.lower()
            row["loss_of_control_probability"] = "" if probability is None else probability
            writer.writerow(row)


def read_telemetry_csv(path: str | Path) -> list[TelemetrySample]:
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        return [
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
            for row in reader
        ]
