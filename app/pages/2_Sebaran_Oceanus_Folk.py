"""Halaman 3 — Sebaran pengaruh Oceanus Folk (VAST Q2a, Q2b, Q2c)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from common import EDGE_COLORS, HIGHLIGHT, OF, SEQ, SERIES, add_era_lines, load, setup, show_table, style, year_filter

setup("Sebaran Oceanus Folk", "🌐")

rel = load("fact_relation")
inf = load("artist_influence")
A = load("dim_artist").set_index("artist_id")
time = load("dim_time").set_index("year")

st.title("🌐 Sebaran Pengaruh Oceanus Folk")
y0, y1 = year_filter()
types = st.sidebar.multiselect("Jenis pengaruh", list(EDGE_COLORS), default=list(EDGE_COLORS))

P = rel[(rel["layer"] == "Pengaruh") & rel["edge_type"].isin(types) & rel["source_genre"].notna()
        & rel["target_genre"].notna()]
P = P[(P["source_year"] >= y0) & (P["source_year"] <= y1)]
out = P[(P["target_genre"] == OF) & (P["source_genre"] != OF)]   # genre lain DIPENGARUHI OF
inn = P[(P["source_genre"] == OF) & (P["target_genre"] != OF)]   # OF DIPENGARUHI genre lain

c = st.columns(4)
c[0].metric("Karya genre lain terinspirasi OF", out["source"].nunique())
c[1].metric("Genre yang terjangkau", out["source_genre"].nunique())
perf = inf[inf["relation_id"].isin(out["relation_id"]) & inf["src_artist_role"].str.contains("Performer")]
c[2].metric("Artis (performer) terpengaruh", perf["src_artist"].nunique())
c[3].metric("Karya OF yang meminjam genre lain", inn["source"].nunique())

st.divider()

# ---------- Q2a ----------
st.header("Q2a · Pengaruhnya naik bertahap atau putus-putus?")
yr = out.groupby("source_year").agg(karya=("source", "nunique"), genre=("source_genre", "nunique"))
yr = yr.reindex(range(max(y0, 2000), y1 + 1), fill_value=0)
yr.index.name = "tahun"
yr = yr.reset_index()
yr["kumulatif"] = yr["karya"].cumsum()
left, right = st.columns(2)
with left:
    fig = go.Figure(go.Bar(x=yr["tahun"], y=yr["karya"], marker_color=HIGHLIGHT, marker_line_width=0,
                           hovertemplate="%{x}: %{y} karya baru terinspirasi OF<extra></extra>"))
    fig.update_layout(title="Karya baru per tahun")
    fig.update_xaxes(title="Tahun rilis karya yang terinspirasi")
    fig.update_yaxes(title="Karya")
    st.plotly_chart(add_era_lines(style(fig, 360, legend=False)), width="stretch")
with right:
    fig = go.Figure(go.Scatter(x=yr["tahun"], y=yr["kumulatif"], mode="lines", line=dict(color=HIGHLIGHT, width=2),
                               fill="tozeroy", fillcolor="rgba(42,120,214,.12)",
                               hovertemplate="s.d. %{x}: %{y} karya<extra></extra>"))
    fig.update_layout(title="Kumulatif")
    fig.update_xaxes(title="Tahun")
    fig.update_yaxes(title="Karya (kumulatif)")
    st.plotly_chart(add_era_lines(style(fig, 360, legend=False)), width="stretch")

zero = (yr[(yr["tahun"] >= 2000) & (yr["tahun"] <= 2022)]["karya"] == 0).sum()
st.info(f"**Putus-putus sebelum 2023, lalu melonjak.** Pada 2000–2022 ada {zero} tahun tanpa satu pun karya baru "
        "yang terinspirasi OF, dan puncak kecilnya (2017) bersifat sporadis. Mulai 2023 (Sailor bergabung dengan "
        "Ivy Echos) pengaruhnya naik tajam dan konsisten dengan puncak 2026–2029. Setelah 2030 grafiknya turun "
        "karena volume data rilis keseluruhan memang menyusut drastis.")

st.divider()

# ---------- Q2b ----------
st.header("Q2b · Genre dan artis yang paling terpengaruh")
left, right = st.columns([3, 2])
with left:
    g = out.groupby(["source_genre", "edge_type"]).size().reset_index(name="n")
    order = g.groupby("source_genre")["n"].sum().sort_values().index.tolist()
    fig = px.bar(g, y="source_genre", x="n", color="edge_type", orientation="h",
                 category_orders={"source_genre": order[::-1], "edge_type": list(EDGE_COLORS)},
                 color_discrete_map=EDGE_COLORS, labels={"source_genre": "", "n": "Relasi pengaruh", "edge_type": ""})
    fig.update_traces(marker_line_width=2, marker_line_color="white",
                      hovertemplate="%{y}: %{x}<extra>%{fullData.name}</extra>")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(style(fig, 520), width="stretch")
with right:
    st.markdown("**Top artis terpengaruh** (performer karya yang terinspirasi OF)")
    ta = (perf.groupby("src_artist")["relation_id"].nunique().sort_values(ascending=False).head(15)
          .rename("relasi").rename_axis("artist_id").reset_index())
    ta["artis"] = ta["artist_id"].map(A["display_name"])
    ta["tipe"] = ta["artist_id"].map(A["artist_type"])
    ta["genre dominan"] = ta["artist_id"].map(A["dominant_genre"])
    st.dataframe(ta[["artis", "tipe", "genre dominan", "relasi"]], hide_index=True, width="stretch", height=480)

st.divider()

# ---------- Q2c ----------
st.header("Q2c · Bagaimana Oceanus Folk berubah seiring naiknya Sailor?")
inn = inn.assign(era=inn["source_year"].map(time["era"]))
eras = list(time["era"].dropna().unique())
left, right = st.columns([3, 2])
with left:
    top = inn["target_genre"].value_counts().head(8).index
    e = inn[inn["target_genre"].isin(top)].groupby(["era", "target_genre"]).size().reset_index(name="n")
    tot = inn.groupby("era").size()
    e["persen"] = e["n"] / e["era"].map(tot) * 100
    fig = px.bar(e, x="persen", y="target_genre", color="era", orientation="h", barmode="group",
                 category_orders={"era": eras, "target_genre": list(top)},
                 color_discrete_sequence=SERIES[:3],
                 custom_data=["n"], labels={"persen": "% sumber inspirasi karya OF di era tsb", "target_genre": "", "era": ""})
    fig.update_traces(marker_line_width=2, marker_line_color="white",
                      hovertemplate="%{y}: %{x:.1f}% (%{customdata[0]} relasi)<extra>%{fullData.name}</extra>")
    fig.update_xaxes(ticksuffix="%")
    st.plotly_chart(style(fig, 480), width="stretch")
with right:
    lag = inn.assign(lag=inn["source_year"] - inn["target_year"]).groupby("era").agg(
        relasi=("relation_id", "size"), genre_unik=("target_genre", "nunique"), median_jeda_th=("lag", "median"))
    lag["porsi Indie Folk"] = inn.groupby("era")["target_genre"].apply(lambda s: f"{(s == 'Indie Folk').mean() * 100:.0f}%")
    st.dataframe(lag.reindex(eras), width="stretch")
    st.markdown("""
- **Sebelum Sailor**, OF sangat bergantung pada **Indie Folk** (~60% sumber inspirasi) dan Synthwave.
- **Era Ivy Echos** menambah warna baru: **Synthpop, Doom Metal, Desert Rock**.
- **Era solo Sailor** paling beragam: Indie Folk turun drastis, digantikan **Dream Pop, Indie Rock,
  Psychedelic Rock, Alternative Rock**. OF bergeser dari folk murni ke arah rock/pop yang lebih luas.
- Jeda tahun ke karya sumber makin panjang (≈7 → ≈11–13 th): OF modern banyak "menggali" karya lama.
""")

st.divider()

# ---------- matriks aliran ----------
st.header("Matriks aliran pengaruh antar-genre")
st.caption("Baris = genre yang **meminjam**, kolom = genre yang **dipinjam**. Warna = jumlah relasi pengaruh (sesuai filter).")
m = P.groupby(["source_genre", "target_genre"]).size().unstack(fill_value=0)
order = P["target_genre"].value_counts().index
m = m.reindex(index=order, columns=order, fill_value=0)
fig = go.Figure(go.Heatmap(z=m.values, x=m.columns, y=m.index, colorscale=[[i / (len(SEQ) - 1), c] for i, c in enumerate(SEQ)],
                           xgap=2, ygap=2, hovertemplate="%{y} meminjam dari %{x}: %{z}<extra></extra>",
                           colorbar=dict(title="relasi")))
fig.update_yaxes(autorange="reversed")
fig.update_xaxes(tickangle=-45)
st.plotly_chart(style(fig, 720, legend=False), width="stretch")
show_table(m.reset_index().rename(columns={"source_genre": "genre peminjam"}), "Lihat matriks sebagai tabel")
