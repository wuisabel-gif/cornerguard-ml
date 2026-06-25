from pathlib import Path

from cornerguard_ml.bicycle_model import simulate_corner_run
from cornerguard_ml.dashboard import load_dashboard_rows, summarize_dashboard_rows
from cornerguard_ml.io import write_telemetry_csv
from cornerguard_ml.labeling import future_labels


def test_dashboard_rows_add_engineering_units(tmp_path: Path):
    samples = simulate_corner_run(run_id=4, duration_s=1.2, seed=4)
    labels = future_labels(samples)
    csv_path = tmp_path / "lap.csv"
    write_telemetry_csv(csv_path, list(zip(samples, [label for label, _ in labels], [prob for _, prob in labels])))

    rows = load_dashboard_rows(csv_path)
    summary = summarize_dashboard_rows(rows)

    assert len(rows) == len(samples)
    assert {"speed_mph", "lateral_accel_g", "yaw_error_degps", "label"}.issubset(rows[0])
    assert summary["samples"] == len(samples)
    assert 0.0 <= summary["peak_risk"] <= 1.0
    assert summary["peak_speed_mph"] > 0.0
