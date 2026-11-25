"""Halaman 2 — Profil Sailor Shift (VAST Q1a, Q1b, Q1c)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from common import (EDGE_COLORS, HIGHLIGHT, NEUTRAL, OF, SAILOR_ID, SERIES, add_era_lines, load, setup,
                    show_table, style)

setup("Profil Sailor Shift", "🎤")

A = load("dim_artist").set_index("artist_id")
fr = load("fact_release").set_index("work_id")
br = load("bridge_artist_work")
inf = load("artist_influence")
col = load("artist_collab")
rel = load("fact_relation")


def nm(i):
    if i in fr.index:
        return fr.at[i, "name"]
    return A.at[i, "display_name"] if i in A.index else str(i)


st.title("🎤 Profil Karier Sailor Shift")

ss_works = br[br["artist_id"] == SAILOR_ID].drop_duplicates("work_id")
ivy = int(A.index[A["name"] == "Ivy Echos"][0])
members = rel[(rel["edge_type"] == "MemberOf") & (rel["target"] == ivy)]["source"].tolist()
collabs = col[col["artist_id"] == SAILOR_ID]
by = inf[inf["src_artist"] == SAILOR_ID]          # Sailor DIPENGARUHI oleh tgt_artist
to = inf[inf["tgt_artist"] == SAILOR_ID]          # src_artist DIPENGARUHI oleh Sailor

c = st.columns(5)
c[0].metric("Karya", len(ss_works), f"{(ss_works['genre'] == OF).mean() * 100:.0f}% Oceanus Folk", delta_color="off", delta_arrow="off")
c[1].metric("Tahun aktif", f"{int(ss_works['release_year'].min())}–{int(ss_works['release_year'].max())}")
c[2].metric("Kolaborator unik", collabs["collaborator_id"].nunique())
c[3].metric("Relasi pengaruh diterima", by["relation_id"].nunique(), help="Jumlah edge pengaruh dari karya/diri Sailor ke karya/artis lain.")
c[4].metric("Artis dipengaruhi langsung", to["src_artist"].nunique())

# ---------- garis waktu karier ----------
st.subheader("Garis waktu karier")
tl = ss_works.merge(fr[["work_type", "notable", "charted", "name"]], left_on="work_id", right_index=True)
tl["peran"] = tl["work_id"].map(br[br["artist_id"] == SAILOR_ID].groupby("work_id")["role"]
                                .agg(lambda s: ", ".join(sorted(set(s)))))
tl["status"] = tl.apply(lambda r: "Masuk chart" if r["charted"] else ("Notable" if r["notable"] else "Biasa"), axis=1)
tl["y"] = tl["work_type"]
fig = px.strip(tl, x="release_year", y="y", color="status",
               color_discrete_map={"Masuk chart": SERIES[1], "Notable": SERIES[0], "Biasa": NEUTRAL},
               hover_data={"name": True, "genre": True, "peran": True, "y": False, "release_year": True},
               labels={"release_year": "Tahun rilis", "y": ""})
fig.update_traces(marker=dict(size=11, line=dict(width=2, color="white")), jitter=0.5)
st.plotly_chart(add_era_lines(style(fig, 260)), width="stretch")
st.caption(f"2023: bergabung dengan **Ivy Echos** (ejaan di data: *Ivy Echos*; anggota: "
           f"{', '.join(A.loc[m, 'display_name'] for m in members if m != SAILOR_ID)}). "
           "Sejak 2024 ia menjadi lyricist hampir semua album Oceanus Folk penting.")

st.divider()

# ---------- Q1a ----------
st.header("Q1a · Siapa yang paling memengaruhi Sailor dari waktu ke waktu?")
rows = []
for rid, g in by.groupby("relation_id"):
    r0 = g.iloc[0]
    perf = [A.at[a, "display_name"] for a, ro in zip(g["tgt_artist"], g["tgt_artist_role"])
            if "Performer" in ro or ro == "Artist"]
    rows.append({"tahun": r0["year"], "karya Sailor": nm(r0["src_entity"]), "jenis": r0["edge_type"],
                 "sumber pengaruh": nm(r0["tgt_entity"]), "tahun sumber": r0["target_year"],
                 "genre sumber": r0["target_genre"] if pd.notna(r0["target_genre"]) else "(artis)",
                 "performer sumber": ", ".join(perf), "level": r0["level"]})
q1a = pd.DataFrame(rows)

direct = q1a[q1a["level"] == "artist"]
left, right = st.columns([3, 2])
with left:
    st.markdown("**Pengaruh tingkat karya**: setiap titik adalah satu karya Sailor yang meminjam dari karya lain")
    wl = q1a[q1a["level"] == "work"].copy()
    fig = go.Figure()
    for et, color in EDGE_COLORS.items():
        d = wl[wl["jenis"] == et]
        if d.empty:
            continue
        fig.add_trace(go.Scatter(
            x=d["tahun"], y=d["genre sumber"], mode="markers", name=et,
            marker=dict(size=13, color=color, line=dict(width=2, color="white")),
            customdata=d[["karya Sailor", "sumber pengaruh", "tahun sumber", "performer sumber"]],
            hovertemplate="<b>%{customdata[0]}</b> (%{x})<br>" + et +
                          " → %{customdata[1]} (%{customdata[2]})<br>%{customdata[3]}<extra></extra>"))
    fig.update_xaxes(title="Tahun rilis karya Sailor", range=[2023, 2041])
    fig.update_yaxes(title="Genre karya sumber", categoryorder="total ascending")
    st.plotly_chart(style(fig, 420), width="stretch")
with right:
    st.markdown("**Pengaruh tingkat artis**: Sailor sendiri yang ditautkan langsung")
    for _, r in direct.iterrows():
        t = A.index[A["display_name"] == r["sumber pengaruh"]]
        meta = A.loc[t[0]] if len(t) else None
        info = f"{meta['dominant_genre']}, {int(meta['first_year'])}–{int(meta['last_year'])}" if meta is not None else ""
        st.markdown(f"- **{r['sumber pengaruh']}** · `{r['jenis']}` · {info}")
    gs = wl["genre sumber"].value_counts()
    st.markdown(f"**Genre yang paling sering dipinjam:** "
                f"{', '.join(f'{g} ({n})' for g, n in gs.head(5).items())}")
    st.info("Pengaruh paling awal dan paling personal berasal dari **Ivy Echos** (band lamanya, ia "
            "*DirectlySamples* Ivy Echos) serta grup Oceanus Folk generasi lama, yaitu **The Saltwater Weavers** "
            "(1995–2001) dan **Drowned Harbor** (2005–2013), ditambah grup Celtic Folk **The Fiddle & The Fjord**. "
            "Di tingkat karya, rujukannya menyebar ke banyak genre (Synthwave, Indie Rock, Alternative Rock, "
            "Psychedelic Rock) dan tidak ada satu artis yang dirujuk lebih dari sekali.")
show_table(q1a.sort_values("tahun"), "Tabel semua relasi pengaruh ke Sailor")

st.divider()

# ---------- Q1b ----------
st.header("Q1b · Kolaborator dan artis yang ia pengaruhi")
hop = st.radio("Kedalaman jaringan pengaruh", [1, 2], horizontal=True,
               format_func=lambda h: f"{h} langkah" + (" (langsung)" if h == 1 else " (tidak langsung)"))

G = nx.Graph()
G.add_node(SAILOR_ID, kind="Sailor Shift")
for m in members:
    if m != SAILOR_ID:
        G.add_node(m, kind="Anggota Ivy Echos")
        G.add_edge(SAILOR_ID, m, kind="Band")
G.add_node(ivy, kind="Anggota Ivy Echos")
G.add_edge(SAILOR_ID, ivy, kind="Band")
cw = collabs.groupby("collaborator_id").size()
for cid, n in cw.items():
    if cid not in G:
        G.add_node(cid, kind="Kolaborator")
    G.add_edge(SAILOR_ID, cid, kind="Kolaborasi", w=n)
lvl1 = set(to["src_artist"])
for a in lvl1:
    if a not in G:
        G.add_node(a, kind="Dipengaruhi (langsung)")
    G.add_edge(SAILOR_ID, a, kind="Pengaruh")
# pengaruh tidak langsung: lewat kolaborator dan lewat artis yang dipengaruhi langsung
seeds = set(cw.index) | lvl1
lvl2 = inf[inf["tgt_artist"].isin(seeds) & ~inf["src_artist"].isin(seeds | {SAILOR_ID})]
n_indirect = lvl2["src_artist"].nunique()   # selalu dihitung; grafik hanya menggambarnya di mode 2 langkah
if hop == 2:
    top2 = lvl2.groupby("src_artist").size().sort_values(ascending=False).head(60).index
    lvl2 = lvl2[lvl2["src_artist"].isin(top2)]
    for _, r in lvl2.drop_duplicates(["src_artist", "tgt_artist"]).iterrows():
        if r["src_artist"] not in G:
            G.add_node(r["src_artist"], kind="Dipengaruhi (tidak langsung)")
        G.add_edge(r["tgt_artist"], r["src_artist"], kind="Pengaruh")

pos = nx.spring_layout(G, seed=7, k=0.9 / max(1, len(G) ** 0.5))
KIND_COLOR = {"Sailor Shift": "#13293D", "Anggota Ivy Echos": SERIES[3], "Kolaborator": SERIES[0],
              "Dipengaruhi (langsung)": SERIES[1], "Dipengaruhi (tidak langsung)": SERIES[2]}
fig = go.Figure()
for kind, dash, color in [("Band", "solid", SERIES[3]), ("Kolaborasi", "solid", "rgba(128,128,128,.35)"),
                          ("Pengaruh", "dot", SERIES[1])]:
    xs, ys = [], []
    for u, v, d in G.edges(data=True):
        if d["kind"] == kind:
            xs += [pos[u][0], pos[v][0], None]
            ys += [pos[u][1], pos[v][1], None]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(width=1, color=color, dash=dash),
                             hoverinfo="skip", showlegend=False))
for kind, color in KIND_COLOR.items():
    ns = [n for n, d in G.nodes(data=True) if d["kind"] == kind]
    if not ns:
        continue
    fig.add_trace(go.Scatter(
        x=[pos[n][0] for n in ns], y=[pos[n][1] for n in ns], mode="markers+text" if kind != "Kolaborator" and kind != "Dipengaruhi (tidak langsung)" else "markers",
        name=kind, text=[nm(n) for n in ns], textposition="top center", textfont=dict(size=11),
        marker=dict(size=[26 if n == SAILOR_ID else 12 for n in ns], color=color, line=dict(width=2, color="white")),
        customdata=[[nm(n), A.at[n, "dominant_genre"] if n in A.index else "", G.degree(n)] for n in ns],
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>%{customdata[2]} koneksi<extra>" + kind + "</extra>"))
fig.update_xaxes(visible=False)
fig.update_yaxes(visible=False)
st.plotly_chart(style(fig, 560), width="stretch")

c = st.columns(3)
c[0].metric("Kolaborator langsung", len(cw))
c[1].metric("Dipengaruhi langsung", len(lvl1))
c[2].metric("Dipengaruhi tidak langsung", n_indirect,
            help="Artis yang meminjam dari kolaborator Sailor atau dari artis yang ia pengaruhi langsung. Pilih \"2 langkah\" untuk menggambarnya di grafik.")
top_c = cw.sort_values(ascending=False).head(10).rename("karya bersama").rename_axis("artist_id").reset_index()
top_c["artis"] = top_c["artist_id"].map(nm)
top_c["genre dominan"] = top_c["artist_id"].map(A["dominant_genre"])
left, right = st.columns(2)
with left:
    st.markdown("**Kolaborator paling sering**")
    st.dataframe(top_c[["artis", "karya bersama", "genre dominan"]], hide_index=True, width="stretch")
with right:
    st.markdown("**Dipengaruhi langsung oleh Sailor**")
    d1 = to.assign(artis=to["src_artist"].map(nm), genre=to["src_artist"].map(A["dominant_genre"]))
    st.dataframe(d1[["artis", "edge_type", "genre"]].rename(columns={"edge_type": "jenis"}), hide_index=True,
                 width="stretch")

st.divider()

# ---------- Q1c ----------
st.header("Q1c · Pengaruh Sailor pada kolaborator di komunitas Oceanus Folk")
st.markdown("Bagaimana karier para kolaborator berubah **sebelum vs sesudah** pertama kali berkarya bersama Sailor?")
first = collabs.groupby("collaborator_id")["release_year"].min().rename("tahun_kolab")
aw = br.drop_duplicates(["artist_id", "work_id"]).merge(fr[["charted"]], left_on="work_id", right_index=True)
aw = aw[aw["artist_id"].isin(first.index)].join(first, on="artist_id")
aw["fase"] = (aw["release_year"] >= aw["tahun_kolab"]).map({True: "Sesudah", False: "Sebelum"})
ss_set = set(ss_works["work_id"])
aw_noss = aw[~aw["work_id"].isin(ss_set)]          # karya tanpa Sailor: dampak pada karier mandiri
summ = aw_noss.groupby(["artist_id", "fase"]).agg(karya=("work_id", "nunique"),
                                                  of=("genre", lambda s: (s == OF).mean() * 100),
                                                  chart=("charted", "sum")).unstack("fase")
summ.columns = [f"{a}_{b}" for a, b in summ.columns]
summ = summ.reindex(index=first.index)  # kolaborator tanpa karya mandiri tetap dihitung (nilai 0)
summ = summ.reindex(columns=["karya_Sebelum", "karya_Sesudah", "of_Sebelum", "of_Sesudah", "chart_Sebelum",
                             "chart_Sesudah"]).fillna({"karya_Sebelum": 0, "karya_Sesudah": 0, "chart_Sebelum": 0,
                                                       "chart_Sesudah": 0})
summ["artis"] = summ.index.map(nm)
summ["tahun kolab"] = first
summ["karya bersama Sailor"] = cw
summ = summ.sort_values("karya bersama Sailor", ascending=False)

c = st.columns(4)
indep_after = (summ["karya_Sesudah"] > 0).sum()
c[0].metric("Kolaborator", len(summ))
c[1].metric("Tetap berkarya mandiri setelah kolab", f"{indep_after}", f"{indep_after / len(summ) * 100:.0f}%", delta_color="off", delta_arrow="off")
c[2].metric("Karya mandiri sesudah kolab", int(summ["karya_Sesudah"].sum()))
c[3].metric("Masuk chart sesudah kolab", int(summ["chart_Sesudah"].sum()))

plot = summ[(summ["karya_Sebelum"] + summ["karya_Sesudah"]) > 0].head(20).iloc[::-1]
fig = go.Figure()
for _, r in plot.iterrows():
    fig.add_trace(go.Scatter(x=[r["karya_Sebelum"], r["karya_Sesudah"]], y=[r["artis"]] * 2, mode="lines",
                             line=dict(color="rgba(128,128,128,.5)", width=2), showlegend=False, hoverinfo="skip"))
fig.add_trace(go.Scatter(x=plot["karya_Sebelum"], y=plot["artis"], mode="markers", name="Sebelum kolab",
                         marker=dict(size=11, color=NEUTRAL, line=dict(width=2, color="white")),
                         hovertemplate="%{y}: %{x} karya mandiri sebelum<extra></extra>"))
fig.add_trace(go.Scatter(x=plot["karya_Sesudah"], y=plot["artis"], mode="markers", name="Sesudah kolab",
                         marker=dict(size=11, color=HIGHLIGHT, line=dict(width=2, color="white")),
                         hovertemplate="%{y}: %{x} karya mandiri sesudah<extra></extra>"))
fig.update_xaxes(title="Jumlah karya tanpa Sailor")
st.plotly_chart(style(fig, 560), width="stretch")
st.caption("Hanya menghitung karya **tanpa** Sailor, agar terlihat apakah kolaborator tumbuh secara mandiri.")
show_table(summ[["artis", "tahun kolab", "karya bersama Sailor", "karya_Sebelum", "karya_Sesudah",
                 "of_Sebelum", "of_Sesudah", "chart_Sebelum", "chart_Sesudah"]].round(0), "Tabel kolaborator")

ofa = set(br[br["genre"] == OF]["artist_id"])
seeds = set(cw.index) | {SAILOR_ID}
chain = inf[inf["tgt_artist"].isin(seeds) & inf["src_artist"].isin(ofa) & ~inf["src_artist"].isin(seeds)]
st.markdown(f"**Rantai pengaruh ke komunitas OF:** {chain['src_artist'].nunique()} artis Oceanus Folk di luar "
            f"lingkaran kolaborasi dipengaruhi oleh Sailor atau kolaboratornya, yaitu "
            f"{', '.join(sorted(set(chain['src_artist'].map(nm))))}.")
