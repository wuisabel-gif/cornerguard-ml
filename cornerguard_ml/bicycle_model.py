from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .telemetry import TelemetrySample, clamp


GRAVITY_MPS2 = 9.80665


@dataclass(frozen=True)
class VehicleParams:
    wheelbase_m: float = 1.55
    cornering_gain: float = 0.86
    yaw_lag_s: float = 0.18
    max_steering_rad: float = 0.48
    tire_mu: float = 1.15


def ideal_yaw_rate(speed_mps: float, steering_angle_rad: float, wheelbase_m: float) -> float:
    if speed_mps <= 0.1:
        return 0.0
    return speed_mps * math.tan(steering_angle_rad) / wheelbase_m


def simulate_corner_run(
    run_id: int,
    duration_s: float = 8.0,
    dt_s: float = 0.01,
    params: VehicleParams | None = None,
    seed: int | None = None,
) -> list[TelemetrySample]:
    """Generate one synthetic cornering run.

    The model is intentionally simple: a bicycle-model yaw target with lag,
    friction-limited lateral acceleration, and randomized driver input. It is
    good enough for pipeline development, not for final vehicle validation.
    """

    params = params or VehicleParams()
    rng = random.Random(seed if seed is not None else run_id)
    speed = rng.uniform(9.0, 31.0)
    steering_bias = rng.choice([-1.0, 1.0]) * rng.uniform(0.03, 0.16)
    steering_amp = rng.uniform(0.03, 0.42)
    steering_freq = rng.uniform(0.18, 0.9)
    panic_time = rng.uniform(2.0, duration_s - 1.0)
    panic_size = rng.choice([0.0, rng.uniform(0.08, 0.28)])
    brake_time = panic_time + rng.uniform(-0.3, 0.5)

    samples: list[TelemetrySample] = []
    yaw_rate = 0.0
    prev_steering = 0.0
    steps = int(duration_s / dt_s)

    for step in range(steps):
        t = step * dt_s
        throttle = clamp(0.55 + 0.25 * math.sin(0.65 * t + run_id), 0.0, 1.0)
        brake = 0.0
        if abs(t - brake_time) < 0.35 and panic_size > 0:
            brake = clamp(0.8 - abs(t - brake_time), 0.0, 1.0)
            throttle *= 0.35

        speed += (1.2 * throttle - 5.0 * brake - 0.06 * speed) * dt_s
        speed = clamp(speed, 3.0, 38.0)

        steering = steering_bias + steering_amp * math.sin(2 * math.pi * steering_freq * t)
        if t > panic_time:
            steering += panic_size * (1.0 - math.exp(-(t - panic_time) / 0.35))
        steering += rng.gauss(0.0, 0.004)
        steering = clamp(steering, -params.max_steering_rad, params.max_steering_rad)

        steering_rate = (steering - prev_steering) / dt_s
        prev_steering = steering

        target_yaw = ideal_yaw_rate(speed, steering, params.wheelbase_m) * params.cornering_gain
        lateral_accel_target = speed * target_yaw
        saturation = abs(lateral_accel_target) / (params.tire_mu * GRAVITY_MPS2)
        if saturation > 1.0:
            target_yaw /= 1.0 + 1.8 * (saturation - 1.0)
            if saturation > 1.22:
                target_yaw += math.copysign((saturation - 1.22) * 0.9, steering)

        yaw_rate += (target_yaw - yaw_rate) * dt_s / params.yaw_lag_s
        yaw_rate += rng.gauss(0.0, 0.008)
        lateral_accel = speed * yaw_rate + rng.gauss(0.0, 0.08)

        samples.append(
            TelemetrySample(
                time_s=t,
                speed_mps=speed,
                steering_angle_rad=steering,
                steering_rate_radps=steering_rate,
                yaw_rate_radps=yaw_rate,
                lateral_accel_mps2=lateral_accel,
                throttle=throttle,
                brake=brake,
            )
        )

    return samples
