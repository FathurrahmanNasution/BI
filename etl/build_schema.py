"""Orkestrator ETL: JSON graf -> star schema + tabel metrik di data/processed/.

Jalankan:  python etl/build_schema.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from extract import ROOT, extract  # noqa: E402
from metrics import (artist_year_metrics, collaboration_pairs, genre_flows, predictions,  # noqa: E402
                     influence_projection, release_year_genre)
from transform import (build_bridge, build_dim_artist, build_dimensions,  # noqa: E402
                       build_fact_relation, build_fact_release, clean_edges)

OUT = ROOT / "data" / "processed"


def main() -> None:
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)

    nodes, edges = extract()
    print(f"[extract] {len(nodes):,} node, {len(edges):,} edge")

    e, log = clean_edges(nodes, edges)
    print(f"[clean] {log}")

    rel = build_fact_relation(nodes, e)
    bridge = build_bridge(nodes, rel)
    release = build_fact_release(nodes, rel, bridge)
    dims = build_dimensions(nodes, rel, bridge)
    artist = build_dim_artist(dims)

    proj = influence_projection(rel, bridge)
    pairs = collaboration_pairs(bridge)
    ay = artist_year_metrics(artist, bridge, release, rel, proj, pairs)

    tables = {
        **dims,
        "dim_artist": artist,
        "fact_release": release,
        "fact_relation": rel,
        "bridge_artist_work": bridge,
        "agg_release_year_genre": release_year_genre(release),
        "agg_genre_flows": genre_flows(rel),
        "artist_influence": proj,
        "artist_collab": pairs,
        "artist_year": ay,
        "rising_star_predictions": predictions(ay, artist, bridge),
    }
    for name, df in tables.items():
        df.to_parquet(OUT / f"{name}.parquet", index=False)
        if not name.startswith("artist_") or name == "artist_year":
            df.to_csv(OUT / f"{name}.csv", index=False)
        print(f"[write] {name:<24} {len(df):>8,} baris")

    (OUT / "etl_log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"selesai dalam {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
