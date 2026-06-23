from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class StabilityLabel(IntEnum):
    STABLE = 0
    WARNING = 1
    CRITICAL = 2


@dataclass(frozen=True)
class TelemetrySample:
    time_s: float
    speed_mps: float
    steering_angle_rad: float
    steering_rate_radps: float
    yaw_rate_radps: float
    lateral_accel_mps2: float
    throttle: float = 0.0
    brake: float = 0.0


TELEMETRY_FIELDS = [
    "time_s",
    "speed_mps",
    "steering_angle_rad",
    "steering_rate_radps",
    "yaw_rate_radps",
    "lateral_accel_mps2",
    "throttle",
    "brake",
]


def clamp(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)
