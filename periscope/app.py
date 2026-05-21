"""Dash app construction for PeriScope."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html
from dash.exceptions import PreventUpdate

from .ephemeris import empty_ephemeris_frame

MAX_MAGNITUDE = 30


def keep_angle_excluding(angle: float, min_angle: float, max_angle: float) -> bool:
    """Return ``True`` when ``angle`` is outside the excluded circular range.

    ``min_angle`` and ``max_angle`` define the range to hide, not the range to
    keep. If ``min_angle`` is larger than ``max_angle``, the excluded interval
    wraps through 0 degrees.
    """
    if pd.isna(angle):
        return False
    if min_angle <= max_angle:
        return bool((angle < min_angle) or (angle > max_angle))
    return bool((angle > max_angle) and (angle < min_angle))


def build_color_map(df: pd.DataFrame) -> dict[str, str]:
    """Return a stable target-to-color mapping based on input-list order."""
    if df.empty or "target" not in df.columns:
        return {}

    base_colors = px.colors.qualitative.Alphabet
    unique_targets = (
        df[["target", "object_index"]].drop_duplicates().sort_values("object_index")
    )
    return {
        row.target: base_colors[(int(row.object_index) - 1) % len(base_colors)]
        for row in unique_targets.itertuples(index=False)
    }


def _filter_ephemerides(
    data_df: pd.DataFrame,
    mag_range: list[float],
    ta_range: list[float],
) -> pd.DataFrame:
    """Apply the user-controlled magnitude and true-anomaly filters."""
    min_mag, max_mag = mag_range
    min_ta, max_ta = ta_range

    df_filtered = data_df[
        (data_df["mean_v"] >= min_mag) & (data_df["mean_v"] <= max_mag)
    ].copy()

    # Keep these coercions near the callbacks because Dash interactions can
    # surface old cached dataframes from earlier package versions during reloads.
    for column in ("mean_v", "mean_ta", "RA", "DEC", "object_index"):
        if column in df_filtered:
            df_filtered[column] = pd.to_numeric(df_filtered[column], errors="coerce")

    return df_filtered[
        df_filtered["mean_ta"].apply(
            lambda value: keep_angle_excluding(value, min_ta, max_ta)
        )
    ]


def create_app(
    data_df: pd.DataFrame | None = None,
    *,
    site_code: str,
    title_label: str,
    title_local_date: str,
) -> Dash:
    """Build the interactive Dash application for already-fetched ephemerides.

    Horizons queries happen before app construction so the Dash callbacks can be
    purely interactive: they filter, replot, and report selections without
    re-contacting Horizons on every slider move.
    """
    data_df = data_df.copy() if data_df is not None else empty_ephemeris_frame()
    app = Dash(__name__)

    app.layout = html.Div(
        [
            html.H2("Minor Planet Elevations with Magnitude and True Anomaly"),
            html.Div(
                [
                    html.Label("Magnitude Range (keep inside):"),
                    dcc.RangeSlider(
                        id="mag-slider",
                        min=0,
                        max=MAX_MAGNITUDE,
                        step=0.5,
                        value=[10, 23],
                        marks={m: str(m) for m in range(0, MAX_MAGNITUDE + 1, 5)},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Div(id="mag-slider-output", style={"marginTop": 10}),
                ],
                style={"marginBottom": 40},
            ),
            html.Div(
                [
                    html.Label("True Anomaly Range (exclude inside):"),
                    dcc.RangeSlider(
                        id="ta-slider",
                        min=0,
                        max=360,
                        step=1,
                        value=[60, 260],
                        marks={a: str(a) for a in range(0, 361, 60)},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Div(id="ta-slider-output", style={"marginTop": 10}),
                ],
                style={"marginBottom": 40},
            ),
            html.Div(
                [
                    html.Label("Selected time for RA/Dec view:"),
                    dcc.Slider(
                        id="time-slider",
                        min=0,
                        max=0,
                        step=1,
                        value=0,
                        marks={0: "No data"},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Div(id="time-slider-output", style={"marginTop": 10}),
                ],
                style={"marginBottom": 40},
            ),
            dcc.Graph(id="planet-graph", style={"height": "55vh"}),
            dcc.Graph(id="radec-graph", style={"height": "55vh"}),
            html.Div(
                id="clicked-object-output",
                style={"marginTop": "20px", "fontWeight": "bold"},
            ),
        ]
    )

    @app.callback(
        Output("planet-graph", "figure"),
        Output("mag-slider-output", "children"),
        Output("ta-slider-output", "children"),
        Output("time-slider", "min"),
        Output("time-slider", "max"),
        Output("time-slider", "value"),
        Output("time-slider", "marks"),
        Output("time-slider-output", "children"),
        Input("mag-slider", "value"),
        Input("ta-slider", "value"),
    )
    def update_figure(mag_range, ta_range):
        """Refresh the elevation plot and keep the RA/Dec time slider aligned."""
        df_filtered = _filter_ephemerides(data_df, mag_range, ta_range)
        color_map = build_color_map(df_filtered)
        fig = go.Figure()

        for target_name in df_filtered["target"].unique():
            subset = df_filtered[df_filtered["target"] == target_name]
            mean_v = subset["mean_v"].iloc[0]
            mean_ta = subset["mean_ta"].iloc[0]

            if pd.notna(mean_v) and pd.notna(mean_ta):
                legend_label = f"{target_name} (f={mean_ta:.1f} deg, V={mean_v:.1f})"
            elif pd.notna(mean_v):
                legend_label = f"{target_name} (V={mean_v:.1f})"
            elif pd.notna(mean_ta):
                legend_label = f"{target_name} (f={mean_ta:.1f} deg)"
            else:
                legend_label = target_name

            object_index = int(subset["object_index"].iloc[0])
            fig.add_trace(
                go.Scatter(
                    x=subset["datetime_utc"],
                    y=subset["EL"],
                    mode="lines",
                    name=f"{object_index}: {legend_label}",
                    line=dict(color=color_map.get(target_name)),
                    customdata=np.column_stack(
                        [
                            np.full(len(subset), object_index),
                            subset["target"].to_numpy(),
                        ]
                    ),
                    hovertemplate=(
                        "Index %{customdata[0]}<br>"
                        "Target %{customdata[1]}<br>"
                        "UTC %{x}<br>"
                        "Elevation %{y:.1f} deg<extra></extra>"
                    ),
                )
            )

        fig.update_layout(
            title=(
                f"{title_label} - Minor Planet Elevations "
                f"(Site {site_code}), {title_local_date}"
            ),
            xaxis=dict(title="UTC Time", type="date"),
            yaxis=dict(title="Elevation (degrees)", range=[0, 90]),
        )

        if not df_filtered.empty:
            fig.update_layout(
                xaxis=dict(
                    title="UTC Time",
                    type="date",
                    range=[
                        df_filtered["datetime_utc"].min(),
                        df_filtered["datetime_utc"].max(),
                    ],
                )
            )

        fig.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=[
                    dict(count=6, label="6h", step="hour", stepmode="backward"),
                    dict(count=12, label="12h", step="hour", stepmode="backward"),
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(step="all", label="All"),
                ]
            ),
        )

        if not df_filtered.empty:
            unique_times = sorted(
                pd.to_datetime(df_filtered["datetime_utc"]).dropna().unique()
            )
            slider_min = 0
            slider_max = max(len(unique_times) - 1, 0)
            slider_value = slider_max
            selected_ts = pd.Timestamp(unique_times[slider_value])
            tick_positions = sorted({0, slider_max // 2, slider_max})
            slider_marks = {
                pos: pd.Timestamp(unique_times[pos]).strftime("%m-%d %H:%M")
                for pos in tick_positions
            }
            time_text = f"RA/Dec time: {selected_ts.strftime('%Y-%m-%d %H:%M UTC')}"
        else:
            slider_min = 0
            slider_max = 0
            slider_value = 0
            slider_marks = {0: "No data"}
            time_text = "RA/Dec time: no data"

        min_mag, max_mag = mag_range
        min_ta, max_ta = ta_range
        mag_text = f"Magnitude filter (keep inside): [{min_mag}, {max_mag}]"
        ta_text = f"True Anomaly excluded range: [{min_ta}, {max_ta}]"

        return (
            fig,
            mag_text,
            ta_text,
            slider_min,
            slider_max,
            slider_value,
            slider_marks,
            time_text,
        )

    @app.callback(
        Output("radec-graph", "figure"),
        Input("time-slider", "value"),
        Input("mag-slider", "value"),
        Input("ta-slider", "value"),
    )
    def update_radec_figure(time_index, mag_range, ta_range):
        """Plot filtered target positions at the selected ephemeris time."""
        df_filtered = _filter_ephemerides(data_df, mag_range, ta_range)
        fig = go.Figure()

        if df_filtered.empty:
            fig.update_layout(
                title="RA/Dec at selected time",
                xaxis_title="RA (deg)",
                yaxis_title="Dec (deg)",
            )
            return fig

        unique_times = sorted(
            pd.to_datetime(df_filtered["datetime_utc"]).dropna().unique()
        )
        if not unique_times:
            fig.update_layout(
                title="RA/Dec at selected time",
                xaxis_title="RA (deg)",
                yaxis_title="Dec (deg)",
            )
            return fig

        if time_index is None:
            time_index = len(unique_times) - 1
        time_index = max(0, min(int(time_index), len(unique_times) - 1))
        selected_ts = pd.Timestamp(unique_times[time_index])
        df_time = df_filtered[df_filtered["datetime_utc"] == selected_ts].copy()
        color_map = build_color_map(df_filtered)

        for target_name in df_time["target"].unique():
            subset = df_time[df_time["target"] == target_name]
            if subset.empty:
                continue

            row = subset.iloc[0]
            object_index = int(row["object_index"])
            fig.add_trace(
                go.Scatter(
                    x=[row["RA"]],
                    y=[row["DEC"]],
                    mode="markers+text",
                    name=f"{object_index}: {target_name}",
                    marker=dict(size=14, color=color_map.get(target_name)),
                    text=[str(object_index)],
                    textposition="middle center",
                    textfont=dict(color="white"),
                    customdata=[[object_index, target_name, row["V"], row["EL"]]],
                    hovertemplate=(
                        "Index %{customdata[0]}<br>"
                        "Target %{customdata[1]}<br>"
                        "RA %{x:.3f} deg<br>"
                        "Dec %{y:.3f} deg<br>"
                        "V %{customdata[2]:.2f}<br>"
                        "Elevation %{customdata[3]:.1f} deg<extra></extra>"
                    ),
                )
            )

        fig.update_layout(
            title=f"RA/Dec at {selected_ts.strftime('%Y-%m-%d %H:%M UTC')}",
            xaxis_title="RA (deg)",
            yaxis_title="Dec (deg)",
            legend_title="Objects",
        )
        return fig

    @app.callback(
        Output("clicked-object-output", "children"),
        Input("planet-graph", "clickData"),
        Input("planet-graph", "figure"),
        Input("radec-graph", "clickData"),
        Input("radec-graph", "figure"),
        prevent_initial_call=True,
    )
    def get_clicked_object(planet_click, planet_fig, radec_click, radec_fig):
        """Report the trace clicked in either linked plot."""
        click_data = radec_click if radec_click else planet_click
        figure = radec_fig if radec_click else planet_fig

        if not click_data:
            raise PreventUpdate

        curve_number = click_data["points"][0]["curveNumber"]
        if "data" not in figure or len(figure["data"]) <= curve_number:
            return "Could not find a matching trace."

        trace_name = figure["data"][curve_number].get("name", "Unknown")
        return f"You clicked on: {trace_name}"

    return app
