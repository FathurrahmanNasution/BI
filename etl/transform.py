"""Tahap 2 — Transformasi: cleaning edge dan pembentukan star schema."""
from __future__ import annotations

import numpy as np
import pandas as pd

WORK_TYPES = {"Song", "Album"}
ARTIST_TYPES = {"Person", "MusicalGroup"}

CREATION = ["PerformerOf", "ComposerOf", "LyricistOf", "ProducerOf"]
INFLUENCE = ["InStyleOf", "InterpolatesFrom", "LyricalReferenceTo", "CoverOf", "DirectlySamples"]
INDUSTRY = ["RecordedBy", "DistributedBy", "MemberOf"]
LAYER = {**{t: "Kreasi" for t in CREATION}, **{t: "Pengaruh" for t in INFLUENCE},
         **{t: "Industri" for t in INDUSTRY}}
ROLE = {"PerformerOf": "Performer", "ComposerOf": "Composer",
        "LyricistOf": "Lyricist", "ProducerOf": "Producer"}

# Era didefinisikan eksplisit agar angka "era Sailor" konsisten di seluruh dashboard.
ERA_BINS = [(1975, 2022, "Pra-Sailor (≤2022)"),
            (2023, 2027, "Era Ivy Echos (2023–2027)"),
            (2028, 2040, "Era Solo Sailor (2028–2040)")]

GENRE_FAMILY = {
    "Oceanus Folk": "Folk", "Indie Folk": "Folk", "Americana": "Folk", "Sea Shanties": "Folk",
    "Acoustic Folk": "Folk", "Celtic Folk": "Folk", "Post-Apocalyptic Folk": "Folk",
    "Avant-Garde Folk": "Folk",
    "Alternative Rock": "Rock", "Southern Gothic Rock": "Rock", "Indie Rock": "Rock",
    "Psychedelic Rock": "Rock", "Jazz Surf Rock": "Rock", "Desert Rock": "Rock",
    "Space Rock": "Rock", "Blues Rock": "Rock",
    "Doom Metal": "Metal", "Speed Metal": "Metal", "Symphonic Metal": "Metal",
    "Dream Pop": "Pop", "Indie Pop": "Pop", "Synthpop": "Pop", "Emo/Pop Punk": "Pop",
    "Synthwave": "Electronic", "Lo-Fi Electronica": "Electronic", "Darkwave": "Electronic",
}


def era_of(year) -> "str | None":
    if pd.isna(year):
        return None
    for lo, hi, label in ERA_BINS:
        if lo <= year <= hi:
            return label
    return None


def clean_edges(nodes: pd.DataFrame, edges: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Bersihkan edge dan kembalikan log jumlah perubahan."""
    log = {"raw": len(edges)}
    ntype = nodes.set_index("id")["node_type"]

    e = edges[edges["source"] != edges["target"]].copy()
    log["self_loops_removed"] = log["raw"] - len(e)

    before = len(e)
    e = e.drop_duplicates(["source", "target", "edge_type"])
    log["duplicates_removed"] = before - len(e)

    # RecordedBy seharusnya Karya -> Label. Ada sebagian yang terbalik (Label -> Karya).
    flip = (e["edge_type"] == "RecordedBy") & e["source"].map(ntype).eq("RecordLabel")
    e.loc[flip, ["source", "target"]] = e.loc[flip, ["target", "source"]].to_numpy()
    log["recordedby_flipped"] = int(flip.sum())
    before = len(e)
    e = e.drop_duplicates(["source", "target", "edge_type"])
    log["duplicates_after_flip"] = before - len(e)
    log["clean"] = len(e)
    return e.reset_index(drop=True), log


def build_fact_relation(nodes: pd.DataFrame, e: pd.DataFrame) -> pd.DataFrame:
    n = nodes.set_index("id")
    f = e.copy()
    f["source_type"] = f["source"].map(n["node_type"])
    f["target_type"] = f["target"].map(n["node_type"])
    f["layer"] = f["edge_type"].map(LAYER)
    both_work = f["source_type"].isin(WORK_TYPES) & f["target_type"].isin(WORK_TYPES)
    f["level"] = np.where(f["layer"] != "Pengaruh", "n/a", np.where(both_work, "work", "artist"))
    f["source_year"] = f["source"].map(n["release_year"]).astype("Int64")
    f["target_year"] = f["target"].map(n["release_year"]).astype("Int64")
    f["source_genre"] = f["source"].map(n["genre"])
    f["target_genre"] = f["target"].map(n["genre"])
    f.insert(0, "relation_id", np.arange(len(f)))
    return f


def build_bridge(nodes: pd.DataFrame, rel: pd.DataFrame) -> pd.DataFrame:
    """Artis (Person/MusicalGroup) × karya × peran."""
    b = rel[rel["edge_type"].isin(CREATION) & rel["source_type"].isin(ARTIST_TYPES)
            & rel["target_type"].isin(WORK_TYPES)]
    b = b.rename(columns={"source": "artist_id", "source_type": "artist_type", "target": "work_id",
                          "target_year": "release_year", "target_genre": "genre"})
    b["role"] = b["edge_type"].map(ROLE)
    return b[["artist_id", "artist_type", "work_id", "role", "release_year", "genre"]].reset_index(drop=True)


def build_fact_release(nodes: pd.DataFrame, rel: pd.DataFrame, bridge: pd.DataFrame) -> pd.DataFrame:
    w = nodes[nodes["node_type"].isin(WORK_TYPES)].copy()
    w = w.rename(columns={"id": "work_id", "node_type": "work_type"})
    w["charted"] = w["notoriety_year"].notna()
    w["years_to_notable"] = (w["notoriety_year"] - w["release_year"]).astype("Int64")
    w["era"] = w["release_year"].map(era_of)
    w["n_creators"] = w["work_id"].map(bridge.groupby("work_id")["artist_id"].nunique()).fillna(0).astype(int)
    infl = rel[rel["layer"] == "Pengaruh"]
    w["n_influences_out"] = w["work_id"].map(infl.groupby("source").size()).fillna(0).astype(int)
    w["n_influenced_by"] = w["work_id"].map(infl.groupby("target").size()).fillna(0).astype(int)
    return w[["work_id", "work_type", "name", "genre", "release_year", "written_year", "notoriety_year",
              "notable", "charted", "single", "years_to_notable", "era", "n_creators",
              "n_influences_out", "n_influenced_by"]].reset_index(drop=True)


def _artist_profile(bridge: pd.DataFrame) -> pd.DataFrame:
    g = bridge.groupby("artist_id")
    prof = pd.DataFrame({
        "n_works": g["work_id"].nunique(),
        "first_year": g["release_year"].min(),
        "last_year": g["release_year"].max(),
    })
    dom = (bridge.drop_duplicates(["artist_id", "work_id"]).groupby(["artist_id", "genre"]).size()
           .reset_index(name="c").sort_values(["artist_id", "c"], ascending=[True, False])
           .drop_duplicates("artist_id").set_index("artist_id")["genre"])
    prof["dominant_genre"] = dom
    return prof


def build_dimensions(nodes: pd.DataFrame, rel: pd.DataFrame, bridge: pd.DataFrame) -> dict[str, pd.DataFrame]:
    prof = _artist_profile(bridge)

    person = nodes[nodes["node_type"] == "Person"][["id", "name", "stage_name"]].rename(columns={"id": "person_id"})
    person = person.join(prof, on="person_id")
    person["n_works"] = person["n_works"].fillna(0).astype(int)
    # 1.584 nama orang dipakai >1 orang (4.899 node): label tampilan menyertakan id agar tidak ambigu.
    dup = person["name"].duplicated(keep=False)
    person["display_name"] = np.where(dup, person["name"] + " (#" + person["person_id"].astype(str) + ")", person["name"])

    group = nodes[nodes["node_type"] == "MusicalGroup"][["id", "name"]].rename(columns={"id": "group_id"})
    group = group.join(prof, on="group_id")
    group["n_works"] = group["n_works"].fillna(0).astype(int)
    group["n_members"] = group["group_id"].map(
        rel[rel["edge_type"] == "MemberOf"].groupby("target")["source"].nunique()).fillna(0).astype(int)
    group["display_name"] = group["name"]

    lab_rel = rel[rel["edge_type"].isin(["RecordedBy", "DistributedBy"])]
    label = nodes[nodes["node_type"] == "RecordLabel"][["id", "name"]].rename(columns={"id": "label_id"})
    for t, col in [("RecordedBy", "n_recorded"), ("DistributedBy", "n_distributed")]:
        label[col] = label["label_id"].map(lab_rel[lab_rel["edge_type"] == t].groupby("target").size()).fillna(0).astype(int)
    dom = (lab_rel.groupby(["target", "source_genre"]).size().reset_index(name="c")
           .sort_values(["target", "c"], ascending=[True, False]).drop_duplicates("target")
           .set_index("target")["source_genre"])
    label["dominant_genre"] = label["label_id"].map(dom)

    genres = sorted(nodes["genre"].dropna().unique())
    genre = pd.DataFrame({"genre_id": range(1, len(genres) + 1), "genre": genres})
    genre["is_oceanus_folk"] = genre["genre"].eq("Oceanus Folk")
    genre["genre_family"] = genre["genre"].map(GENRE_FAMILY).fillna("Other")

    years = range(int(nodes["release_year"].min()), int(nodes["release_year"].max()) + 1)
    time = pd.DataFrame({"year": list(years)})
    time["era"] = time["year"].map(era_of)
    time["decade"] = (time["year"] // 10 * 10).astype(str) + "s"

    return {"dim_person": person.reset_index(drop=True), "dim_group": group.reset_index(drop=True),
            "dim_label": label.reset_index(drop=True), "dim_genre": genre, "dim_time": time}


def build_dim_artist(dims: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Gabungan Person + MusicalGroup, dipakai halaman dashboard untuk pencarian artis."""
    p = dims["dim_person"].rename(columns={"person_id": "artist_id"}).assign(artist_type="Person")
    g = dims["dim_group"].rename(columns={"group_id": "artist_id"}).assign(artist_type="MusicalGroup")
    cols = ["artist_id", "artist_type", "name", "display_name", "n_works", "first_year", "last_year", "dominant_genre"]
    return pd.concat([p[cols], g[cols]], ignore_index=True)
