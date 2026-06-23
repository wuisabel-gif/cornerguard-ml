from __future__ import annotations

from collections.abc import Iterable
from statistics import fmean, pstdev

from .bicycle_model import VehicleParams, ideal_yaw_rate
from .telemetry import TelemetrySample


BASE_SIGNALS = [
    "speed_mps",
    "steering_angle_rad",
    "steering_rate_radps",
    "yaw_rate_radps",
    "lateral_accel_mps2",
    "throttle",
    "brake",
    "yaw_error_radps",
]


def sample_to_values(sample: TelemetrySample) -> dict[str, float]:
    expected_yaw = ideal_yaw_rate(
        sample.speed_mps,
        sample.steering_angle_rad,
        VehicleParams().wheelbase_m,
    )
    return {
        "speed_mps": sample.speed_mps,
        "steering_angle_rad": sample.steering_angle_rad,
        "steering_rate_radps": sample.steering_rate_radps,
        "yaw_rate_radps": sample.yaw_rate_radps,
        "lateral_accel_mps2": sample.lateral_accel_mps2,
        "throttle": sample.throttle,
        "brake": sample.brake,
        "yaw_error_radps": expected_yaw - sample.yaw_rate_radps,
    }


def window_features(window: Iterable[TelemetrySample]) -> dict[str, float]:
    values_by_signal = {signal: [] for signal in BASE_SIGNALS}
    samples = list(window)
    if not samples:
        raise ValueError("window_features requires at least one sample")

    for sample in samples:
        values = sample_to_values(sample)
        for signal in BASE_SIGNALS:
            values_by_signal[signal].append(values[signal])

    features: dict[str, float] = {}
    for signal, values in values_by_signal.items():
        features[f"{signal}_mean"] = fmean(values)
        features[f"{signal}_std"] = pstdev(values) if len(values) > 1 else 0.0
        features[f"{signal}_min"] = min(values)
        features[f"{signal}_max"] = max(values)
        features[f"{signal}_last"] = values[-1]

    return features


def feature_names() -> list[str]:
    names: list[str] = []
    for signal in BASE_SIGNALS:
        names.extend(
            [
                f"{signal}_mean",
                f"{signal}_std",
                f"{signal}_min",
                f"{signal}_max",
                f"{signal}_last",
            ]
        )
    return names
