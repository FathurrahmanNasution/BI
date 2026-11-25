"""Tahap 3 — Metrik: proyeksi pengaruh antar-artis, KPI tahunan, dan skor Rising Star."""
from __future__ import annotations

import numpy as np
import pandas as pd

from transform import ARTIST_TYPES, WORK_TYPES

WINDOW = 5  # jendela tahun untuk skor rising star

# Bobot skor rising star (lihat IMPLEMENTATION_PLAN.md, Tahap 3).
# `notable` bernilai True di 93% karya sehingga lemah; `charted_5y` (punya notoriety_date) ditambahkan
# sebagai sinyal popularitas yang lebih tajam.
WEIGHTS = {
    "notable_5y": 0.20,
    "charted_5y": 0.15,
    "growth": 0.20,
    "influence_5y": 0.15,
    "collab_5y": 0.15,
    "labels_5y": 0.15,
}

# Kandidat prediksi: artis berfokus Oceanus Folk, aktif belakangan, belum mapan.
PRED_YEARS = range(2036, 2041)
PRED_MIN_OF_SHARE = 0.5
PRED_MIN_DEBUT = 2020
SAILOR_ID = 17255  # referensi bintang yang sudah mapan, tidak diprediksi


def influence_projection(rel: pd.DataFrame, bridge: pd.DataFrame) -> pd.DataFrame:
    """Proyeksikan edge pengaruh (karya→karya / artis→artis) menjadi artis→artis.

    Baris berarti: src_artist (lewat src_work) DIPENGARUHI tgt_artist (lewat tgt_entity) pada tahun `year`.
    """
    infl = rel[rel["layer"] == "Pengaruh"][["relation_id", "source", "target", "edge_type", "source_type",
                                             "target_type", "source_year", "target_year",
                                             "source_genre", "target_genre", "level"]]
    wa = (bridge.groupby(["work_id", "artist_id"])["role"]
          .agg(lambda s: ",".join(sorted(set(s)))).reset_index())

    def side(df, col, typ, out):
        is_work = df[typ].isin(WORK_TYPES)
        w = df[is_work].merge(wa, left_on=col, right_on="work_id", how="inner").drop(columns="work_id")
        w = w.rename(columns={"artist_id": out, "role": f"{out}_role"})
        a = df[df[typ].isin(ARTIST_TYPES)].copy()
        a[out] = a[col]
        a[f"{out}_role"] = "Artist"  # edge pengaruh langsung antar-artis
        return pd.concat([w, a], ignore_index=True)

    p = side(infl, "source", "source_type", "src_artist")
    p = side(p, "target", "target_type", "tgt_artist")
    p = p[p["src_artist"] != p["tgt_artist"]]
    p = p.rename(columns={"source": "src_entity", "target": "tgt_entity"})
    p["year"] = p["source_year"].fillna(p["target_year"]).astype("Int64")
    return p.drop_duplicates(["relation_id", "src_artist", "tgt_artist"]).reset_index(drop=True)


def collaboration_pairs(bridge: pd.DataFrame) -> pd.DataFrame:
    """Pasangan artis yang berbagi karya (arah dua sisi), dengan tahun karya."""
    wa = bridge.drop_duplicates(["work_id", "artist_id"])[["work_id", "artist_id", "release_year", "genre"]]
    pr = wa.merge(wa[["work_id", "artist_id"]], on="work_id", suffixes=("", "_other"))
    pr = pr[pr["artist_id"] != pr["artist_id_other"]]
    return pr.rename(columns={"artist_id_other": "collaborator_id"}).reset_index(drop=True)


def release_year_genre(fact_release: pd.DataFrame) -> pd.DataFrame:
    return (fact_release.groupby(["release_year", "genre"])
            .agg(n_works=("work_id", "size"), n_notable=("notable", "sum"), n_charted=("charted", "sum"),
                 n_songs=("work_type", lambda s: (s == "Song").sum()))
            .reset_index().rename(columns={"release_year": "year"}))


def genre_flows(proj_rel: pd.DataFrame) -> pd.DataFrame:
    """Aliran pengaruh antar-genre tingkat karya: source_genre DIPENGARUHI target_genre."""
    f = proj_rel[(proj_rel["layer"] == "Pengaruh") & proj_rel["source_genre"].notna() & proj_rel["target_genre"].notna()]
    return (f.groupby(["source_year", "source_genre", "target_genre", "edge_type"]).size()
            .reset_index(name="n").rename(columns={"source_year": "year"}))


def _yearly(df: pd.DataFrame, key: str, year: str, val: str | None, years: np.ndarray, ids: np.ndarray,
            agg: str = "count") -> np.ndarray:
    """Matriks artis × tahun dari tabel event."""
    d = df.dropna(subset=[year])
    if agg == "count":
        s = d.groupby([key, year]).size()
    else:
        s = d.groupby([key, year])[val].sum()
    m = s.unstack(fill_value=0).reindex(index=ids, columns=years, fill_value=0)
    return m.to_numpy(dtype=float)


def _rolling(m: np.ndarray, w: int) -> np.ndarray:
    c = np.cumsum(np.pad(m, ((0, 0), (1, 0))), axis=1)
    out = np.empty_like(m)
    for j in range(m.shape[1]):
        lo = max(0, j + 1 - w)
        out[:, j] = c[:, j + 1] - c[:, lo]
    return out


def _rolling_unique(events: pd.DataFrame, key: str, val: str, years: np.ndarray, ids: np.ndarray, w: int) -> np.ndarray:
    idx = {a: i for i, a in enumerate(ids)}
    out = np.zeros((len(ids), len(years)))
    ev = events.dropna(subset=["release_year"])
    for j, t in enumerate(years):
        sub = ev[(ev["release_year"] > t - w) & (ev["release_year"] <= t)]
        s = sub.groupby(key)[val].nunique()
        rows = s.index.map(idx).to_numpy()
        out[rows, j] = s.to_numpy()
    return out


def artist_year_metrics(dim_artist: pd.DataFrame, bridge: pd.DataFrame, fact_release: pd.DataFrame,
                        rel: pd.DataFrame, proj: pd.DataFrame, pairs: pd.DataFrame) -> pd.DataFrame:
    """KPI per artis per tahun + komponen jendela 5 tahun + skor rising star (persentil)."""
    years = np.arange(int(fact_release["release_year"].min()), int(fact_release["release_year"].max()) + 1)
    ids = dim_artist.loc[dim_artist["n_works"] > 0, "artist_id"].to_numpy()

    aw = bridge.drop_duplicates(["artist_id", "work_id"]).merge(
        fact_release[["work_id", "notable", "charted"]], on="work_id")
    aw["notable"] = aw["notable"].astype(int)
    aw["charted"] = aw["charted"].astype(int)

    works = _yearly(aw, "artist_id", "release_year", None, years, ids)
    notable = _yearly(aw, "artist_id", "release_year", "notable", years, ids, "sum")
    charted = _yearly(aw, "artist_id", "release_year", "charted", years, ids, "sum")
    # satu relasi pengaruh dihitung sekali per artis yang dirujuk (bukan per kreator karya peminjam)
    received = proj.drop_duplicates(["relation_id", "tgt_artist"]).rename(columns={"tgt_artist": "artist_id"})
    infl = _yearly(received, "artist_id", "year", None, years, ids)

    labels = rel[rel["edge_type"].isin(["RecordedBy", "DistributedBy"])][["source", "target"]]
    al = aw[["artist_id", "work_id", "release_year"]].merge(labels, left_on="work_id", right_on="source")
    collab_5y = _rolling_unique(pairs, "artist_id", "collaborator_id", years, ids, WINDOW)
    labels_5y = _rolling_unique(al, "artist_id", "target", years, ids, WINDOW)

    works_5y = _rolling(works, WINDOW)
    prev = np.pad(works_5y, ((0, 0), (WINDOW, 0)))[:, : len(years)]
    comp = {
        "works": works, "notable": notable, "charted": charted, "influence": infl,
        "works_5y": works_5y,
        "notable_5y": _rolling(notable, WINDOW),
        "charted_5y": _rolling(charted, WINDOW),
        "influence_5y": _rolling(infl, WINDOW),
        "collab_5y": collab_5y,
        "labels_5y": labels_5y,
        "growth": works_5y - prev,
        "cum_works": np.cumsum(works, axis=1),
        "cum_notable": np.cumsum(notable, axis=1),
        "cum_influence": np.cumsum(infl, axis=1),
    }

    rows = []
    a_idx, y_idx = np.nonzero(works_5y > 0)  # hanya artis yang aktif dalam jendela 5 tahun
    base = pd.DataFrame({"artist_id": ids[a_idx], "year": years[y_idx]})
    for k, m in comp.items():
        base[k] = m[a_idx, y_idx]
    rows.append(base)
    out = pd.concat(rows, ignore_index=True)

    # Skor = rata-rata tertimbang persentil (skala 0–100). Persentil dihitung terhadap SELURUH
    # artis-tahun (pooled), bukan per tahun: jumlah artis aktif turun drastis setelah 2030
    # (3.766 di 2030 -> 36 di 2040), sehingga persentil per tahun tidak sebanding antar tahun.
    score = np.zeros(len(out))
    for k, wgt in WEIGHTS.items():
        out[f"pct_{k}"] = out[k].rank(pct=True, method="average") * 100
        score += wgt * out[f"pct_{k}"].to_numpy()
    out["rising_star"] = score
    out["rank_in_year"] = out.groupby("year")["rising_star"].rank(ascending=False, method="min").astype(int)

    debut = dim_artist.set_index("artist_id")["first_year"]
    out["career_age"] = out["year"] - out["artist_id"].map(debut)
    for c in ["works", "notable", "charted", "influence", "works_5y", "notable_5y", "charted_5y",
              "influence_5y", "collab_5y", "labels_5y", "growth", "cum_works", "cum_notable", "cum_influence"]:
        out[c] = out[c].astype(int)
    return out


def predictions(artist_year: pd.DataFrame, dim_artist: pd.DataFrame, bridge: pd.DataFrame) -> pd.DataFrame:
    """Peringkat kandidat bintang Oceanus Folk 2041–2045.

    pred_score = rata-rata skor rising star 2036–2040 (tahun tanpa aktivitas = 0), sehingga
    yang diunggulkan adalah momentum yang konsisten di lima tahun terakhir.
    """
    aw = bridge.drop_duplicates(["artist_id", "work_id"])
    of_share = aw.assign(of=aw["genre"].eq("Oceanus Folk")).groupby("artist_id")["of"].mean()
    recent = artist_year[artist_year["year"].isin(PRED_YEARS)]
    pivot = recent.pivot_table(index="artist_id", columns="year", values="rising_star").reindex(columns=list(PRED_YEARS))
    pred = pd.DataFrame({"pred_score": pivot.fillna(0).mean(axis=1),
                         "trend": pivot.ffill(axis=1).iloc[:, -1].fillna(0) - pivot.bfill(axis=1).iloc[:, 0].fillna(0)})
    last = artist_year.sort_values("year").groupby("artist_id").last()
    pred = pred.join(last[["works_5y", "notable_5y", "charted_5y", "influence_5y", "collab_5y", "labels_5y"]])
    pred = pred.join(dim_artist.set_index("artist_id")[["display_name", "artist_type", "first_year", "last_year",
                                                        "n_works", "dominant_genre"]])
    pred["of_share"] = of_share
    pred["eligible"] = ((pred["of_share"] >= PRED_MIN_OF_SHARE) & (pred["first_year"] >= PRED_MIN_DEBUT)
                        & (pred.index != SAILOR_ID))
    pred = pred.sort_values(["pred_score", "n_works"], ascending=False).reset_index()

    # Anggota yang seluruh karyanya sudah tercakup oleh act yang peringkatnya lebih tinggi
    # (mis. anggota The Brine Choir) digabung ke act tersebut agar tidak muncul berulang.
    works = aw.groupby("artist_id")["work_id"].agg(frozenset)
    accepted: list[int] = []
    covered_by, rank, k = [], [], 0
    for aid, ok in zip(pred["artist_id"], pred["eligible"]):
        cov = next((a for a in accepted if works.get(aid, frozenset()) <= works[a]), None) if ok else None
        covered_by.append(cov)
        if ok and cov is None:
            k += 1
            accepted.append(aid)
            rank.append(k)
        else:
            rank.append(np.nan)
    pred["covered_by"] = pd.array(covered_by, dtype="Int64")
    pred["pred_rank"] = rank
    return pred
