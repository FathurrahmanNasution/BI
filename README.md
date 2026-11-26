# Oceanus Folk BI Dashboard — Kelompok 23

Dashboard BI untuk dataset **VAST Challenge 2025 Mini-Challenge 1** (knowledge graph industri musik Oceanus).
Pipeline: `MC1_graph.json` → ETL Python → star schema (Parquet/CSV) → dashboard Streamlit 4 halaman.

## Menjalankan

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt        # macOS/Linux: .venv/bin/pip
.venv/Scripts/python etl/build_schema.py             # bangun star schema ke data/processed/
.venv/Scripts/streamlit run app/Home.py              # buka http://localhost:8501
```

Folder `data/processed/` **tidak disimpan di repo** (ada di `.gitignore`) karena seluruh isinya dapat dibangun
ulang dari `data/raw/MC1_graph.json` dalam sekitar 2 detik. Langkah ETL di atas opsional: bila folder itu belum ada,
dashboard menjalankan ETL sendiri saat pertama kali dibuka (begitu juga di Streamlit Community Cloud).

## Struktur

```
data/raw/MC1_graph.json          dataset asli
data/processed/                  (dibuat oleh ETL, tidak di repo) star schema, tabel metrik, etl_log.json
etl/extract.py                   load JSON -> DataFrame node & edge
etl/transform.py                 cleaning edge, dim_*, fact_*, bridge
etl/metrics.py                   proyeksi pengaruh, kolaborasi, skor rising star, prediksi
etl/build_schema.py              orkestrator ETL
app/Home.py                      Halaman 1 — Ringkasan Eksekutif
app/pages/1_Profil_Sailor_Shift  Halaman 2 — Q1
app/pages/2_Sebaran_Oceanus_Folk Halaman 3 — Q2
app/pages/3_Radar_Rising_Star    Halaman 4 — Q3
docs/Jawaban_VAST_MC1.md         jawaban tertulis Q1–Q3
IMPLEMENTATION_PLAN.md           rencana implementasi
```

## Star schema

| Tabel | Baris | Isi |
|---|---|---|
| `dim_person` / `dim_group` / `dim_label` | 11.361 / 223 / 1.217 | atribut turunan relasi (genre dominan, tahun aktif, jumlah karya) |
| `dim_genre` / `dim_time` | 26 / 66 | keluarga genre, era (Pra-Sailor ≤2022, Ivy Echos 2023–27, Solo 2028–40) |
| `fact_release` | 4.611 | satu baris per lagu/album: genre, tahun, notable, charted, jumlah kreator & pengaruh |
| `fact_relation` | 37.853 | satu baris per edge bersih: jenis, lapisan (Kreasi/Pengaruh/Industri), tahun & genre kedua sisi |
| `bridge_artist_work` | 23.025 | artis × karya × peran |
| `artist_year` | 75.739 | KPI per artis per tahun + skor rising star |
| `rising_star_predictions` | 133 | kandidat bintang OF 2041–2045 |

## Pembersihan data
Ringkasan di bawah juga ditulis ETL ke `data/processed/etl_log.json` setiap kali dijalankan:

```json
{"raw": 37857, "self_loops_removed": 1, "duplicates_removed": 3,
 "recordedby_flipped": 103, "duplicates_after_flip": 0, "clean": 37853}
```

- 1 self-loop dan 3 edge duplikat dibuang; 103 edge `RecordedBy` yang terbalik (Label→Karya) dibalik menjadi Karya→Label (tidak dibuang), sehingga relasi bersih = 37.853.
- 1.584 nama orang dipakai lebih dari satu orang (4.899 node Person), sehingga semua join memakai `id`. Nama tampilan ditambah `(#id)` bila ambigu.
- `notable` bernilai True di 93% karya, jadi popularitas utama diukur dengan **masuk chart** (`notoriety_date` ada).

## Skor Rising Star
Komponen dalam jendela 5 tahun, masing-masing diubah menjadi persentil (pooled) lalu dibobot:
notable 20% · masuk chart 15% · pertumbuhan rilis 20% · pengaruh diterima 15% · kolaborator unik 15% · jangkauan label 15%.
Bobot bisa diubah dari sidebar halaman Radar Rising Star.
