"""Utilitas bersama dashboard: load data (cached), palet warna, filter global."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data" / "processed"
SAILOR_ID = 17255
OF = "Oceanus Folk"

# Palet kategorikal tervalidasi (urutan tetap, tidak di-cycle). Lihat skill dataviz/references/palette.md.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
NEUTRAL = "#a3a29c"          # konteks / "genre lain"
HIGHLIGHT = SERIES[0]         # Oceanus Folk / Sailor
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

EDGE_COLORS = {"InStyleOf": SERIES[0], "InterpolatesFrom": SERIES[1], "CoverOf": SERIES[2],
               "LyricalReferenceTo": SERIES[3], "DirectlySamples": SERIES[6]}
ERA_MARKERS = [(2023, "Gabung Ivy Echos"), (2026, "Ivy Echos bubar"), (2028, "Single viral")]


@st.cache_data(show_spinner=False)
def load(name: str) -> pd.DataFrame:
    return pd.read_parquet(DATA / f"{name}.parquet")


@st.cache_resource(show_spinner=False)
def _build_data_once() -> bool:
    """Bangun star schema dari data/raw bila belum ada (mis. saat pertama kali jalan di hosting).

    cache_resource memastikan ETL hanya berjalan sekali per proses server, walau banyak pengunjung.
    """
    if (DATA / "rising_star_predictions.parquet").exists():
        return True
    import sys
    sys.path.insert(0, str(DATA.parents[1] / "etl"))
    import build_schema  # noqa: E402
    build_schema.main()
    return True


def ensure_data() -> None:
    if not (DATA / "rising_star_predictions.parquet").exists():
        with st.spinner("Menyiapkan data pertama kali (ETL dari MC1_graph.json)…"):
            try:
                _build_data_once()
            except Exception as e:  # noqa: BLE001
                st.error(f"Gagal membangun data: {e}. Jalankan manual: `python etl/build_schema.py`")
                st.stop()


def setup(title: str, icon: str = "🌊") -> None:
    st.set_page_config(page_title=f"{title} · Oceanus Folk BI", page_icon=icon, layout="wide")
    ensure_data()
    st.markdown(
        """<style>
        [data-testid="stMetricValue"] {font-size: 1.9rem;}
        .block-container {padding-top: 2rem;}
        .note {color: var(--text-color); opacity: .7; font-size: .85rem;}
        </style>""",
        unsafe_allow_html=True,
    )


def year_filter(key: str = "years", default=(1975, 2040)) -> tuple[int, int]:
    return st.sidebar.slider("Rentang tahun rilis", 1975, 2040, default, key=key)


def style(fig: go.Figure, height: int = 380, legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=40, b=10), colorway=SERIES,
        hovermode="closest", showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=1, xanchor="right", title=None),
        title=dict(x=0, y=0.98, yanchor="top", font=dict(size=15)),
        font=dict(size=13),
    )
    fig.update_xaxes(showgrid=False, ticks="outside")
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.18)", zeroline=False)
    return fig


def add_era_lines(fig: go.Figure, y_ref: str = "paper") -> go.Figure:
    # Tiga penanda berdekatan (2023, 2026, 2028): label ditumpuk ke bawah agar tidak saling menimpa.
    for i, (yr, label) in enumerate(ERA_MARKERS):
        fig.add_vline(x=yr, line_width=1, line_dash="dot", line_color="rgba(128,128,128,.7)")
        fig.add_annotation(x=yr, y=1 - i * 0.075, yref="paper", text=f"{yr} · {label}", showarrow=False,
                           xanchor="left", xshift=4, yanchor="top", font=dict(size=11), opacity=.85,
                           bgcolor="rgba(255,255,255,.75)")
    return fig


def artist_name(ids) -> pd.Series:
    a = load("dim_artist").set_index("artist_id")["display_name"]
    return pd.Series(ids).map(a)


def show_table(df: pd.DataFrame, label: str = "Lihat tabel data") -> None:
    with st.expander(label):
        st.dataframe(df, width="stretch", hide_index=True)
