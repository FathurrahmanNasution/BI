"""Tahap 1 — Ekstraksi: baca MC1_graph.json menjadi DataFrame node dan edge mentah."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "MC1_graph.json"

EXPECTED_NODES = 17_412
EXPECTED_EDGES = 37_857


def _to_year(v) -> "int | None":
    if v is None or (isinstance(v, float) and pd.isna(v)) or v == "":
        return None
    return int(str(v)[:4])


def extract(path: Path = RAW_PATH) -> tuple[pd.DataFrame, pd.DataFrame]:
    with open(path, encoding="utf-8") as f:
        g = json.load(f)

    nodes = pd.DataFrame(g["nodes"]).rename(
        columns={"Node Type": "node_type", "release_date": "release_year",
                 "written_date": "written_year", "notoriety_date": "notoriety_year"}
    )
    for col in ["release_year", "written_year", "notoriety_year"]:
        nodes[col] = nodes[col].map(_to_year).astype("Int64")
    nodes["notable"] = nodes["notable"].astype("boolean")
    nodes["single"] = nodes["single"].astype("boolean")
    nodes = nodes[["id", "node_type", "name", "stage_name", "genre", "release_year",
                   "written_year", "notoriety_year", "notable", "single"]]

    edges = pd.DataFrame(g["links"]).rename(columns={"Edge Type": "edge_type"})
    edges = edges[["source", "target", "edge_type"]]

    assert len(nodes) == EXPECTED_NODES, f"node count {len(nodes)} != {EXPECTED_NODES}"
    assert len(edges) == EXPECTED_EDGES, f"edge count {len(edges)} != {EXPECTED_EDGES}"
    return nodes, edges


if __name__ == "__main__":
    n, e = extract()
    print(n["node_type"].value_counts(), e["edge_type"].value_counts(), sep="\n\n")
