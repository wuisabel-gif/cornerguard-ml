from __future__ import annotations

from .bicycle_model import GRAVITY_MPS2, VehicleParams, ideal_yaw_rate
from .telemetry import StabilityLabel, TelemetrySample, clamp


def instability_score(sample: TelemetrySample, params: VehicleParams | None = None) -> float:
    params = params or VehicleParams()
    friction_ratio = abs(sample.lateral_accel_mps2) / (params.tire_mu * GRAVITY_MPS2)
    expected_yaw = ideal_yaw_rate(
        sample.speed_mps,
        sample.steering_angle_rad,
        params.wheelbase_m,
    )
    yaw_error = abs(expected_yaw - sample.yaw_rate_radps)
    yaw_error_score = yaw_error / max(abs(expected_yaw), 0.35)
    steering_rate_score = abs(sample.steering_rate_radps) / 4.5
    brake_while_turning = sample.brake * min(abs(sample.steering_angle_rad) / 0.25, 1.0)

    return clamp(
        0.58 * friction_ratio
        + 0.25 * yaw_error_score
        + 0.10 * steering_rate_score
        + 0.07 * brake_while_turning,
        0.0,
        1.6,
    )


def label_from_score(score: float) -> StabilityLabel:
    if score >= 1.0:
        return StabilityLabel.CRITICAL
    if score >= 0.74:
        return StabilityLabel.WARNING
    return StabilityLabel.STABLE


def future_labels(
    samples: list[TelemetrySample],
    horizon_s: float = 1.0,
    dt_s: float = 0.01,
) -> list[tuple[StabilityLabel, float]]:
    horizon_steps = max(1, round(horizon_s / dt_s))
    labels: list[tuple[StabilityLabel, float]] = []

    for idx in range(len(samples)):
        future = samples[idx + 1 : idx + 1 + horizon_steps]
        if not future:
            future = samples[idx : idx + 1]
        score = max(instability_score(sample) for sample in future)
        probability = clamp((score - 0.45) / 0.75, 0.0, 1.0)
        labels.append((label_from_score(score), probability))

    return labels
