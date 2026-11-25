"""Halaman 4 — Radar Rising Star (VAST Q3a, Q3b)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import NEUTRAL, OF, SAILOR_ID, SERIES, load, setup, show_table, style

setup("Radar Rising Star", "⭐")

A = load("dim_artist").set_index("artist_id")
ay = load("artist_year")
br = load("bridge_artist_work")

st.title("⭐ Radar Rising Star")

COMP = {"notable_5y": "Karya notable", "charted_5y": "Masuk chart", "growth": "Pertumbuhan rilis",
        "influence_5y": "Pengaruh diterima", "collab_5y": "Kolaborator unik", "labels_5y": "Jangkauan label"}
DEFAULT_W = {"notable_5y": 20, "charted_5y": 15, "growth": 20, "influence_5y": 15, "collab_5y": 15, "labels_5y": 15}

with st.expander("ℹ️ Apa itu skor Rising Star?", expanded=False):
    st.markdown("""
Untuk setiap artis per tahun dihitung enam komponen dalam **jendela 5 tahun terakhir**. Tiap komponen diubah
menjadi **persentil (0–100)** terhadap seluruh artis-tahun dalam data, lalu dirata-rata dengan bobot di bawah.
Persentil dihitung *pooled* (bukan per tahun) karena jumlah artis aktif turun dari 3.766 (2030) ke 36 (2040).

**Profil rising star** (dari data): rilis cepat bertambah, karya notable/masuk chart, banyak kolaborator,
dan mulai dirujuk karya lain. Bobot bisa diubah di sidebar; seluruh halaman akan dihitung ulang.
""")

st.sidebar.markdown("### Bobot skor")
w = {k: st.sidebar.slider(v, 0, 50, DEFAULT_W[k], 5, key=f"w_{k}") for k, v in COMP.items()}
tw = sum(w.values()) or 1
ay = ay.copy()
ay["score"] = sum(ay[f"pct_{k}"] * v for k, v in w.items()) / tw
ay["rank"] = ay.groupby("year")["score"].rank(ascending=False, method="min")

# ---------- Q3a ----------
st.header("Q3a · Perbandingan karier tiga artis")
named = A[A["n_works"] > 0].sort_values("n_works", ascending=False)
opts = named.index.tolist()
default = [SAILOR_ID, int(A.index[A["name"] == "Orla Seabloom"][0]), int(A.index[A["name"] == "Jay Walters"][0])]
pick = st.multiselect("Pilih hingga 3 artis", opts, default=default, max_selections=3,
                      format_func=lambda i: f"{A.at[i, 'display_name']} · {A.at[i, 'dominant_genre']} · {A.at[i, 'artist_type']}")
if not pick:
    st.stop()
color = {a: SERIES[i] for i, a in enumerate(pick)}   # warna mengikuti entitas, bukan peringkat

sub = ay[ay["artist_id"].isin(pick)].copy()
sub["tahun_karier"] = sub["year"] - sub["artist_id"].map(A["first_year"])
aw = br.drop_duplicates(["artist_id", "work_id"])
fr = load("fact_release").set_index("work_id")

cols = st.columns(len(pick))
for c, a in zip(cols, pick):
    s = sub[sub["artist_id"] == a]
    works = aw[aw["artist_id"] == a]
    peak = s.loc[s["score"].idxmax()] if len(s) else None
    c.markdown(f"<span style='color:{color[a]};font-size:1.3rem'>●</span> **{A.at[a, 'display_name']}**",
               unsafe_allow_html=True)
    c.caption(f"{A.at[a, 'dominant_genre']} · {int(A.at[a, 'first_year'])}–{int(A.at[a, 'last_year'])}")
    c.metric("Karya / masuk chart", f"{len(works)} / {int(fr.loc[works['work_id'], 'charted'].sum())}")
    if peak is not None:
        c.metric("Puncak skor", f"{peak['score']:.0f}", f"tahun {int(peak['year'])} (karier th ke-{int(peak['tahun_karier'])})",
                 delta_color="off", delta_arrow="off")
        c.metric("Total dirujuk karya lain", int(s["cum_influence"].max()))

metrics = [("cum_works", "Karya kumulatif"), ("cum_notable", "Notable kumulatif"),
           ("cum_influence", "Dirujuk karya lain (kumulatif)"), ("score", "Skor rising star")]
grid = st.columns(2)
for i, (m, label) in enumerate(metrics):
    fig = go.Figure()
    for a in pick:
        s = sub[sub["artist_id"] == a].sort_values("tahun_karier")
        fig.add_trace(go.Scatter(x=s["tahun_karier"], y=s[m], mode="lines+markers", name=A.at[a, "display_name"],
                                 line=dict(color=color[a], width=2), marker=dict(size=8, line=dict(width=2, color="white")),
                                 customdata=s["year"],
                                 hovertemplate="th ke-%{x} (%{customdata}): %{y:.0f}<extra>%{fullData.name}</extra>"))
    fig.update_layout(title=label, hovermode="x unified")
    fig.update_xaxes(title="Tahun sejak debut")
    grid[i % 2].plotly_chart(style(fig, 320), width="stretch")

left, right = st.columns([2, 3])
with left:
    st.markdown("**Profil komponen pada tahun puncak**")
    fig = go.Figure()
    for a in pick:
        s = sub[sub["artist_id"] == a]
        if s.empty:
            continue
        p = s.loc[s["score"].idxmax()]
        vals = [p[f"pct_{k}"] for k in COMP] + [p[f"pct_{list(COMP)[0]}"]]
        fig.add_trace(go.Scatterpolar(r=vals, theta=list(COMP.values()) + [list(COMP.values())[0]], name=A.at[a, "display_name"],
                                      line=dict(color=color[a], width=2), fill="toself", opacity=.55,
                                      hovertemplate="%{theta}: persentil %{r:.0f}<extra>%{fullData.name}</extra>"))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100], showticklabels=False)))
    st.plotly_chart(style(fig, 420), width="stretch")
with right:
    st.markdown("**Bagaimana membacanya**")
    st.markdown("""
- **Sailor Shift** · *bintang yang tumbuh stabil*: rilis konsisten setiap 1–2 tahun sejak 2024, menjadi
  lyricist banyak album OF, dan kolaborator unik naik hingga 27 dalam 5 tahun. Skornya sudah di **top 10%
  pada 2025** (peringkat 337 dari 3.469 artis aktif), tiga tahun sebelum single-nya viral (2028), dan menjadi **#1 pada 2034–2035**.
- **Orla Seabloom** · *meledak sekali*: 8 karya dalam satu tahun (2029), 7 masuk chart. Popularitasnya
  tertinggi di antara semua artis OF, tetapi tanpa kolaborasi dan tanpa rilis lanjutan, skornya tidak bertahan.
- **Jay Walters** · *pengaruh yang naik perlahan*: rilis sedikit per tahun selama 46 tahun (1984–2030), tetapi
  karyanya terus dirujuk dan menjadi artis yang **paling banyak dirujuk** di seluruh graf. Popularitas
  datang belakangan, lewat warisan.

**Kesimpulan profil rising star:** sinyal paling awal adalah **pertumbuhan rilis + jaringan kolaborasi** yang
melebar. Masuk chart sendirian (tanpa jaringan) cenderung tidak berkelanjutan.
""")

# ---------- backtest ----------
st.subheader("Validasi: apakah skor ini bisa 'menemukan' Sailor sebelum viral?")
ss = ay[ay["artist_id"] == SAILOR_ID]
n_active = ay.groupby("year").size()
ss = ss.assign(top_pct=ss["rank"] / ss["year"].map(n_active) * 100)
fig = go.Figure(go.Scatter(x=ss["year"], y=ss["top_pct"], mode="lines+markers", line=dict(color=SERIES[0], width=2),
                           marker=dict(size=8, line=dict(width=2, color="white")),
                           customdata=np.c_[ss["rank"], ss["year"].map(n_active)],
                           hovertemplate="%{x}: peringkat %{customdata[0]:.0f} dari %{customdata[1]} artis aktif (top %{y:.1f}%)<extra></extra>"))
fig.update_yaxes(title="Top-% di antara artis aktif", autorange="reversed", ticksuffix="%")
fig.add_vline(x=2028, line_dash="dot", line_color="rgba(128,128,128,.7)")
fig.add_annotation(x=2028, y=1, yref="paper", text="Single viral", showarrow=False, xanchor="left", yanchor="top")
st.plotly_chart(style(fig, 300, legend=False), width="stretch")

st.divider()

# ---------- Q3b ----------
st.header("Q3b · Prediksi bintang Oceanus Folk 2041–2045")
st.markdown("**Kriteria kandidat:** ≥ 50% karya Oceanus Folk · debut ≥ 2020 · bukan Sailor Shift. "
            "**Skor prediksi** = rata-rata skor rising star 2036–2040 (tahun tanpa aktivitas = 0). "
            "Anggota yang seluruh karyanya sudah tercakup dalam grup digabung ke grupnya.")
aw_g = aw.assign(of=aw["genre"].eq(OF))
of_share = aw_g.groupby("artist_id")["of"].mean()
recent = ay[ay["year"].between(2036, 2040)].pivot_table(index="artist_id", columns="year", values="score") \
    .reindex(columns=range(2036, 2041))
pred = pd.DataFrame({"pred": recent.fillna(0).mean(axis=1)})
pred = pred.join(A[["display_name", "artist_type", "first_year", "last_year", "n_works"]])
pred["of_share"] = of_share
pred = pred[(pred["of_share"] >= .5) & (pred["first_year"] >= 2020) & (pred.index != SAILOR_ID)]
pred = pred.sort_values(["pred", "n_works"], ascending=False)
work_sets = aw.groupby("artist_id")["work_id"].agg(frozenset)
acc, members = [], {}
for a in pred.index:
    host = next((h for h in acc if work_sets[a] <= work_sets[h]), None)
    if host is None:
        acc.append(a)
    else:
        members.setdefault(host, []).append(A.at[a, "display_name"])
top = pred.loc[acc].head(10).copy()
top["anggota/terkait"] = [", ".join(members.get(a, [])) for a in top.index]
last = ay.sort_values("year").groupby("artist_id").last()
for k in ["charted_5y", "collab_5y", "works_5y"]:
    top[k] = last[k]
sw = set(aw[aw["artist_id"] == SAILOR_ID]["work_id"])
top["karya bersama Sailor"] = [len(work_sets[a] & sw) for a in top.index]

fig = go.Figure(go.Bar(x=top["pred"].iloc[::-1], y=top["display_name"].iloc[::-1], orientation="h",
                       marker_color=[SERIES[0] if i < 3 else NEUTRAL for i in range(len(top))][::-1],
                       hovertemplate="%{y}: %{x:.1f}<extra></extra>"))
fig.update_xaxes(title="Skor prediksi")
st.plotly_chart(style(fig, 400, legend=False), width="stretch")

cards = st.columns(3)
reasons = {
    "The Brine Choir": "Grup OF debut 2034 yang merilis 3 album bersama Sailor sebagai lyricist (2034, 2035, 2038) "
                       "plus single mandiri hingga 2038. Kelima anggotanya (Lyra Blaze, Orion Cruz, Elara May, "
                       "Cassian Rae, Arlo Sterling) adalah komposer/penulis lirik. Pola ini mirip Sailor: "
                       "rilis konsisten dan jaringan yang melebar.",
    "Copper Canyon Ghosts": "Satu-satunya act OF baru dengan 5 karya masuk chart dalam 2 tahun (2034–2035), dan "
                            "artis yang *DirectlySamples* Sailor. Ia menggabungkan popularitas cepat ala Orla "
                            "Seabloom dengan kolaborasi (Beatrice Albright, Daniel O'Connell).",
    "Selkie's Hollow": "Debut paling baru (2037): 4 single + album 'Ballads for the Low Tide' bersama Sailor "
                       "(lyricist) dan Maya Jensen (eks Ivy Echos). Didukung langsung lingkaran inti Sailor "
                       "pada awal karier, persis seperti posisi Sailor tahun 2024.",
}
for c, (a, r) in zip(cards, top.head(3).iterrows()):
    c.markdown(f"### {int(list(top.index).index(a)) + 1}. {r['display_name']}")
    c.caption(f"{r['artist_type']} · debut {int(r['first_year'])} · {int(r['n_works'])} karya · skor {r['pred']:.1f}")
    c.markdown(reasons.get(r["display_name"], "Skor tinggi berdasarkan komponen rising star 2036–2040."))

show_table(top[["display_name", "artist_type", "first_year", "last_year", "n_works", "of_share", "pred",
                "charted_5y", "collab_5y", "karya bersama Sailor", "anggota/terkait"]].round(2),
           "Tabel 10 kandidat teratas")
st.caption("Catatan: data setelah 2030 sangat tipis (≤ 40 rilis/tahun), sehingga prediksi bersifat indikatif. "
           "Ubah bobot di sidebar untuk menguji ketahanan peringkat.")
