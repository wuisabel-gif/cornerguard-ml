from cornerguard_ml.bicycle_model import simulate_corner_run
from cornerguard_ml.features import feature_names, window_features
from cornerguard_ml.labeling import future_labels
from cornerguard_ml.telemetry import StabilityLabel


def test_simulator_produces_telemetry_and_future_labels():
    samples = simulate_corner_run(run_id=1, duration_s=3.0, seed=1)
    labels = future_labels(samples)

    assert len(samples) == 300
    assert len(labels) == len(samples)
    assert all(isinstance(label, StabilityLabel) for label, _ in labels)
    assert all(0.0 <= probability <= 1.0 for _, probability in labels)


def test_window_features_are_stable_and_named():
    samples = simulate_corner_run(run_id=2, duration_s=2.2, seed=2)
    features = window_features(samples[:200])
    names = feature_names()

    assert set(features) == set(names)
    assert features["speed_mps_mean"] > 0.0
    assert features["yaw_error_radps_std"] >= 0.0
