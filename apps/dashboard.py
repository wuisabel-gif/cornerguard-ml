from __future__ import annotations

from pathlib import Path
import tempfile

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from cornerguard_ml.dashboard import LABEL_COLORS, load_dashboard_rows, summarize_dashboard_rows


DEFAULT_DATA = Path("data/processed/simulated_cornering.csv")
REPO_URL = "https://github.com/wuisabel-gif/cornerguard-ml"


def load_rows_from_upload(uploaded_file) -> list[dict[str, float | str]]:
    if uploaded_file is None:
        if not DEFAULT_DATA.exists():
            return []
        return load_dashboard_rows(DEFAULT_DATA)

    with tempfile.NamedTemporaryFile("wb", suffix=".csv", delete=False) as handle:
        handle.write(uploaded_file.getbuffer())
        path = Path(handle.name)
    try:
        return load_dashboard_rows(path)
    finally:
        path.unlink(missing_ok=True)


def add_state_bands(fig: go.Figure, df: pd.DataFrame) -> None:
    if df.empty or "label" not in df:
        return

    labels = df["label"].fillna("unknown").astype(str).tolist()
    times = df["time_s"].tolist()
    start = times[0]
    current = labels[0]

    for idx in range(1, len(df)):
        if labels[idx] == current:
            continue
        fig.add_vrect(
            x0=start,
            x1=times[idx],
            fillcolor=LABEL_COLORS.get(current, LABEL_COLORS["unknown"]),
            opacity=0.10,
            line_width=0,
            layer="below",
        )
        start = times[idx]
        current = labels[idx]

    fig.add_vrect(
        x0=start,
        x1=times[-1],
        fillcolor=LABEL_COLORS.get(current, LABEL_COLORS["unknown"]),
        opacity=0.10,
        line_width=0,
        layer="below",
    )


def line_chart(df: pd.DataFrame, y_columns: list[str], title: str) -> go.Figure:
    fig = px.line(df, x="time_s", y=y_columns, title=title)
    add_state_bands(fig, df)
    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        legend_title_text="Signal",
        margin=dict(l=20, r=20, t=50, b=20),
        height=360,
    )
    fig.update_xaxes(title="Time (s)")
    return fig


def main() -> None:
    st.set_page_config(page_title="CornerGuard Dashboard", page_icon="CG", layout="wide")

    st.title("CornerGuard ML Dashboard")
    st.caption("Replay racing telemetry, inspect future-risk labels, and compare driver inputs near the grip limit.")

    with st.sidebar:
        st.header("Telemetry")
        uploaded = st.file_uploader("Upload telemetry CSV", type=["csv"])
        st.caption("Expected columns: time_s, speed_mps, steering_angle_rad, steering_rate_radps, yaw_rate_radps, lateral_accel_mps2.")
        show_raw = st.checkbox("Show raw rows", value=False)
        st.link_button("View GitHub repo", REPO_URL)

    try:
        rows = load_rows_from_upload(uploaded)
    except Exception as exc:
        st.error(f"Could not load telemetry: {exc}")
        return

    if not rows:
        st.info("Generate demo data first: `python scripts/generate_sim_data.py --runs 200 --out data/processed/simulated_cornering.csv`")
        return

    df = pd.DataFrame(rows)
    summary = summarize_dashboard_rows(rows)

    metric_cols = st.columns(5)
    metric_cols[0].metric("Samples", f"{summary['samples']:,}")
    metric_cols[1].metric("Duration", f"{summary['duration_s']:.1f} s")
    metric_cols[2].metric("Peak risk", f"{summary['peak_risk']:.2f}")
    metric_cols[3].metric("Peak speed", f"{summary['peak_speed_mph']:.1f} mph")
    metric_cols[4].metric("Peak lateral", f"{summary['peak_lateral_g']:.2f} g")

    st.subheader("Risk Timeline")
    risk_fig = px.area(
        df,
        x="time_s",
        y="loss_of_control_probability",
        color="label",
        color_discrete_map=LABEL_COLORS,
        title="Predicted loss-of-control probability",
    )
    risk_fig.update_layout(template="plotly_white", hovermode="x unified", margin=dict(l=20, r=20, t=50, b=20), height=360)
    risk_fig.update_yaxes(range=[0, 1], title="Risk")
    risk_fig.update_xaxes(title="Time (s)")
    st.plotly_chart(risk_fig, use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            line_chart(df, ["speed_mph", "lateral_accel_g"], "Speed and lateral load"),
            use_container_width=True,
        )
        st.plotly_chart(
            line_chart(df, ["steering_angle_deg", "steering_rate_degps"], "Steering input"),
            use_container_width=True,
        )
    with right:
        st.plotly_chart(
            line_chart(df, ["yaw_rate_degps", "yaw_error_degps"], "Yaw response"),
            use_container_width=True,
        )
        st.plotly_chart(
            line_chart(df, ["throttle", "brake"], "Pedal inputs"),
            use_container_width=True,
        )

    st.subheader("State Distribution")
    counts = df["label"].value_counts().rename_axis("state").reset_index(name="samples")
    bar = px.bar(counts, x="state", y="samples", color="state", color_discrete_map=LABEL_COLORS)
    bar.update_layout(template="plotly_white", showlegend=False, margin=dict(l=20, r=20, t=20, b=20), height=300)
    st.plotly_chart(bar, use_container_width=True)

    if show_raw:
        st.subheader("Raw Dashboard Rows")
        st.dataframe(df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
