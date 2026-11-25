"""Halaman 1 — Ringkasan Eksekutif.  Jalankan:  streamlit run app/Home.py"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from common import HIGHLIGHT, NEUTRAL, OF, SERIES, add_era_lines, load, setup, show_table, style, year_filter

setup("Ringkasan Eksekutif")

fr = load("fact_release")
br = load("bridge_artist_work")
genres = load("dim_genre")
rel = load("fact_relation")
labels = load("dim_label")

st.title("🌊 Oceanus Folk — Ringkasan Eksekutif")
st.caption("Knowledge graph VAST Challenge 2025 MC1 · 17.412 entitas · 37.853 relasi (setelah dibersihkan) · 1975–2040")

# ---------- filter ----------
y0, y1 = year_filter()
fam = st.sidebar.multiselect("Keluarga genre", sorted(genres["genre_family"].unique()), placeholder="Semua")
wtype = st.sidebar.multiselect("Tipe karya", ["Song", "Album"], placeholder="Semua")

g2f = genres.set_index("genre")["genre_family"]
f = fr[(fr["release_year"] >= y0) & (fr["release_year"] <= y1)].copy()
f["family"] = f["genre"].map(g2f)
if fam:
    f = f[f["family"].isin(fam)]
if wtype:
    f = f[f["work_type"].isin(wtype)]

if f.empty:
    st.warning("Tidak ada karya pada filter ini.")
    st.stop()

# ---------- KPI ----------
of_f = f[f["genre"] == OF]
span = min(10, max(1, (y1 - y0 + 1) // 2))  # 10 th terakhir vs 10 th sebelumnya
recent = of_f[of_f["release_year"] > y1 - span].shape[0]
prior = of_f[(of_f["release_year"] <= y1 - span) & (of_f["release_year"] > y1 - 2 * span)].shape[0]
growth = (recent - prior) / prior * 100 if prior else None
active = br[br["work_id"].isin(f["work_id"])]["artist_id"].nunique()
top_genre = f["genre"].value_counts()

c = st.columns(5)
c[0].metric("Total karya", f"{len(f):,}".replace(",", "."))
c[1].metric("Masuk chart", f"{f['charted'].mean() * 100:.1f}%", help="Karya yang punya notoriety_date (benar-benar masuk top chart).")
c[2].metric("Notable", f"{f['notable'].mean() * 100:.1f}%", help="Flag notable bernilai True di ~93% karya, sehingga kurang membedakan; gunakan 'Masuk chart' sebagai proksi popularitas utama.")
c[3].metric("Genre teratas", top_genre.index[0], f"{top_genre.iloc[0]} karya", delta_color="off", delta_arrow="off")
c[4].metric("Artis aktif", f"{active:,}".replace(",", "."))

c = st.columns(5)
c[0].metric("Karya Oceanus Folk", f"{len(of_f)}", f"{len(of_f) / len(f) * 100:.1f}% dari total", delta_color="off", delta_arrow="off")
c[1].metric(f"Pertumbuhan OF {y1 - span + 1}–{y1}", f"{growth:+.0f}%" if growth is not None else "–",
            f"{recent} vs {prior} karya ({y1 - 2 * span + 1}–{y1 - span})", delta_color="off", delta_arrow="off",
            help="Setelah 2030 volume rilis seluruh genre turun drastis, sehingga perbandingan yang melewati 2030 cenderung negatif.")
ytn = f["years_to_notable"].dropna()
c[2].metric("Jeda rilis → chart", f"{ytn.mean():.1f} th" if len(ytn) else "–",
            f"{(ytn == 0).mean() * 100:.0f}% di tahun yang sama" if len(ytn) else None, delta_color="off", delta_arrow="off")
of_era = fr[fr["genre"] == OF]
c[3].metric("Rilis OF sejak 2023", f"{(of_era['release_year'] >= 2023).mean() * 100:.0f}%",
            help="183 dari 305 karya Oceanus Folk dirilis sejak Sailor bergabung dengan Ivy Echos (2023). Sejak single viral 2028: 31%.")
c[4].metric("Genre", f"{f['genre'].nunique()}")

st.divider()

# ---------- tren tahunan ----------
left, right = st.columns([3, 2])
with left:
    st.subheader("Rilis per tahun: Oceanus Folk vs genre lain")
    yr = f.assign(grp=f["genre"].eq(OF).map({True: OF, False: "Genre lain"})) \
          .groupby(["release_year", "grp"]).size().reset_index(name="karya")
    fig = px.bar(yr, x="release_year", y="karya", color="grp",
                 color_discrete_map={OF: HIGHLIGHT, "Genre lain": NEUTRAL},
                 labels={"release_year": "Tahun rilis", "karya": "Jumlah karya", "grp": ""})
    fig.update_traces(marker_line_width=0, hovertemplate="%{x}: %{y} karya<extra>%{fullData.name}</extra>")
    fig.update_layout(bargap=0.15)
    st.plotly_chart(add_era_lines(style(fig)), width="stretch")

with right:
    st.subheader("Porsi Oceanus Folk (bergulir 3 th)")
    share = f.groupby("release_year").agg(total=("work_id", "size"), of=("genre", lambda s: (s == OF).sum()))
    share = share.reindex(range(y0, y1 + 1), fill_value=0)
    share.index.name = "release_year"
    roll = share.rolling(3, min_periods=1).sum()          # rata-rata bergulir 3 tahun meredam tahun bervolume kecil
    share["persen"] = roll["of"] / roll["total"].replace(0, float("nan")) * 100
    share = share.reset_index()
    fig = go.Figure(go.Scatter(x=share["release_year"], y=share["persen"], mode="lines",
                               line=dict(color=HIGHLIGHT, width=2),
                               hovertemplate="%{x}: %{y:.1f}%<extra></extra>"))
    fig.update_yaxes(title="% karya OF", ticksuffix="%")
    fig.update_xaxes(title="Tahun rilis")
    st.plotly_chart(add_era_lines(style(fig, legend=False)), width="stretch")
    st.caption("Setelah 2030 jumlah rilis total sangat kecil (≤ 40/tahun), dan karya yang tersisa didominasi "
               "lingkaran Sailor, sehingga porsi OF melonjak.")

left, right = st.columns(2)
with left:
    st.subheader("Genre dengan karya terbanyak")
    gc = f["genre"].value_counts().head(12).rename_axis("genre").reset_index(name="karya").iloc[::-1]
    fig = go.Figure(go.Bar(x=gc["karya"], y=gc["genre"], orientation="h",
                           marker_color=[HIGHLIGHT if g == OF else NEUTRAL for g in gc["genre"]],
                           hovertemplate="%{y}: %{x} karya<extra></extra>"))
    fig.update_xaxes(title="Jumlah karya")
    st.plotly_chart(style(fig, 420, legend=False), width="stretch")

with right:
    st.subheader("Dominasi label rekaman")
    lr = rel[rel["edge_type"].isin(["RecordedBy", "DistributedBy"]) & rel["source"].isin(f["work_id"])]
    lab = (lr.groupby("target")["source"].nunique().sort_values(ascending=False).head(12)
           .rename("karya").reset_index().merge(labels[["label_id", "name"]], left_on="target", right_on="label_id"))
    total_w = lr["source"].nunique()
    lab["share"] = lab["karya"] / total_w * 100
    lab = lab.iloc[::-1]
    fig = go.Figure(go.Bar(x=lab["karya"], y=lab["name"], orientation="h", marker_color=SERIES[0],
                           customdata=lab["share"],
                           hovertemplate="%{y}: %{x} karya (%{customdata:.1f}%)<extra></extra>"))
    fig.update_xaxes(title="Karya yang direkam/didistribusikan")
    st.plotly_chart(style(fig, 420, legend=False), width="stretch")
    shares = lr.groupby("target")["source"].nunique() / total_w * 100
    st.caption(f"Pasar label sangat terfragmentasi: {lr['target'].nunique()} label, "
               f"HHI = {(shares ** 2).sum():.0f} (< 1.500 = tidak terkonsentrasi).")

show_table(f[["name", "work_type", "genre", "release_year", "notable", "charted", "notoriety_year"]]
           .sort_values("release_year"), "Lihat tabel karya (sesuai filter)")

st.markdown("""
---
**Navigasi:** gunakan menu di kiri untuk membuka **Profil Sailor Shift** (Q1), **Sebaran Oceanus Folk** (Q2),
dan **Radar Rising Star** (Q3).
""")
