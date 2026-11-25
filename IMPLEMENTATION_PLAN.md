# Implementation Plan — Oceanus Folk BI Dashboard (Kelompok 23)

Dataset: `MC1_graph.json`, VAST Challenge 2025 MC1 (directed multigraph, 17.412 node, 37.857 edge)
Sumber rencana: PPT *VAST Challenge 2025 MC1 – Kelompok 23* + Data Description + Answer Sheet resmi

> **Status (2026-11-18): selesai diimplementasikan.** Lihat `README.md` untuk cara menjalankan dan `docs/Jawaban_VAST_MC1.md` untuk jawaban Q1–Q3.

---

## 0. Ringkasan

Kita membangun pipeline **JSON graf → ETL Python → star schema → dashboard web 4 halaman**. Setiap halaman memetakan langsung ke pertanyaan resmi VAST MC1 dan ke satu kelompok pengguna di slide 9:

| Halaman dashboard (slide 11) | Pertanyaan VAST | Pengguna utama |
|---|---|---|
| 1. Ringkasan Eksekutif | (konteks untuk semua) | Pemerintah/pariwisata |
| 2. Profil Sailor Shift | Q1a, Q1b, Q1c | Jurnalis (Silas Reed) |
| 3. Sebaran Oceanus Folk | Q2a, Q2b, Q2c | Pemerintah, label |
| 4. Radar Rising Star | Q3a, Q3b | Label, produser/manajer |

**Stack yang direkomendasikan:** Python 3.11 + `pandas` + `networkx` untuk ETL, file Parquet/CSV sebagai star schema, dan **Streamlit + Plotly** untuk dashboard (filter interaktif cepat dibuat, sesuai "dashboard web yang kami bangun sendiri"). Jaringan digambar dengan `pyvis` atau `streamlit-agraph`.
*Alternatif:* jika dosen meminta Power BI/Tableau, star schema di tahap 2 bisa langsung di-import. ETL-nya tetap sama.

---

## 1. Temuan profiling data (sudah dicek)

Angka di PPT **cocok** dengan data:
- Node: Person 11.361, Song 3.615, Album 996, RecordLabel 1.217, MusicalGroup 223 ✅
- 26 genre, rentang rilis 1975–2040, 4.611 karya ✅
- Slide 7 (arah pengaruh, Desert Rock 50, Indie Folk 100, dst.) ✅ persis
- Slide 6 "60% rilis Oceanus Folk di era Sailor": 183/305 = 60% **jika era dihitung mulai 2023** (bergabung dengan Ivy Echoes). Kalau mulai 2028 (viral), hasilnya hanya 31%. → **Tulis definisi era di slide/dashboard.**

Masalah kualitas data yang **wajib ditangani di ETL**:

| # | Masalah | Jumlah | Penanganan |
|---|---|---|---|
| 1 | Nama orang duplikat (nama sama, id beda) | 1.584 nama (4.899 node) | Selalu join pakai `id`, jangan pakai `name`. Tampilkan `name (#id)` bila ambigu |
| 2 | `notable = True` di 93% karya (4.297/4.611) | — | KPI "% notable" hampir tidak membedakan. Tambahkan KPI **`notoriety_date` ada** (649 karya = benar-benar masuk chart) dan **waktu menuju notable** |
| 3 | Tahun disimpan sebagai string | 4.611 | Cast ke `int` |
| 4 | `notoriety_date` hanya ada di 649 karya, `written_date` di 1.455 | — | Simpan sebagai nullable, jangan diimputasi |
| 5 | Edge di luar skema: `RecordedBy` terbalik (Label→Song/Album) | 103 | Normalisasi arah: karya selalu menjadi source |
| 6 | Edge pengaruh antar Person/MusicalGroup (bukan karya) | ±70 | Simpan dengan flag `level = 'artist'`. Penting untuk Sailor: 7 artis ditautkan langsung sebagai *dipengaruhi oleh* Sailor, dan Sailor ditautkan ke 4 artis sumber pengaruhnya |
| 7 | Edge duplikat / self-loop | 3 / 1 | Buang |
| 8 | Ejaan grup: **"Ivy Echos"** (bukan "Ivy Echoes" seperti di PPT) | — | Samakan label di PPT/dashboard |
| 9 | Komponen terpisah | 18 | Abaikan untuk KPI, tapi catat di analisis jaringan |

---

## 2. Tahapan implementasi

### Tahap 1 — Setup & Ekstraksi (Minggu 1)
- Struktur repo:
  ```
  BI/
  ├─ data/raw/MC1_graph.json
  ├─ data/processed/         # output star schema (parquet + csv)
  ├─ etl/extract.py          # load JSON → df_nodes, df_edges
  ├─ etl/transform.py        # cleaning + derivasi
  ├─ etl/metrics.py          # KPI, skor pengaruh, rising star
  ├─ etl/build_schema.py     # tulis dim_* dan fact_*
  ├─ app/Home.py             # Streamlit
  ├─ app/pages/1_Ringkasan.py ... 4_Rising_Star.py
  ├─ notebooks/eda.ipynb
  └─ requirements.txt
  ```
- `extract.py`: `json.load` → `nx.node_link_graph(data, edges="links")` + dua DataFrame mentah.
- Unit check: jumlah node/edge = 17.412 / 37.857.

### Tahap 2 — Transformasi & Star Schema (Minggu 1–2)
Sesuai slide 12, ditambah beberapa kolom yang dibutuhkan untuk pertanyaan VAST:

**Dimensi**
| Tabel | Kunci | Kolom |
|---|---|---|
| `dim_person` | person_id | name, stage_name, dominant_genre, first_year, last_year, n_works |
| `dim_group` | group_id | name, n_members, dominant_genre, active_years |
| `dim_label` | label_id | name, n_recorded, n_distributed, dominant_genre |
| `dim_genre` | genre_id | genre, is_oceanus_folk, genre_family (Folk/Rock/Electronic/Metal/Pop) |
| `dim_time` | year | year, era (`pre_sailor` <2023, `ivy_echos` 2023–2027, `solo_rise` 2028+), decade |

**Fakta**
| Tabel | Grain | Kolom |
|---|---|---|
| `fact_release` | 1 karya | work_id, type (Song/Album), genre_id, release_year, written_year, notoriety_year, notable, single, years_to_notable, n_creators, n_influences_out, n_influenced_by |
| `fact_relation` | 1 edge | source_id, source_type, target_id, target_type, edge_type, layer (Kreasi/Pengaruh/Industri), level (work/artist), source_year, target_year, source_genre, target_genre |
| `bridge_artist_work` | artist × karya × peran | artist_id, artist_type, work_id, role (Performer/Composer/Lyricist/Producer) |

Kunci derivasi:
- **Tahun relasi** = tahun rilis karya source (karya yang meminjam/terinspirasi).
- **Pengaruh antar artis** = proyeksi: artis A → karya X —(InStyleOf dsb.)→ karya Y ← artis B ⇒ "A dipengaruhi B pada tahun X".
- **Kolaborasi** = dua artis punya peran pada karya yang sama (bridge self-join).

### Tahap 3 — Metrik & Analitik (Minggu 2–3)
`metrics.py` menghasilkan tabel agregat yang dibaca dashboard:

| KPI (slide 12) | Definisi operasional |
|---|---|
| Rilis per tahun & genre | count `fact_release` group by year, genre |
| % notable | notable / total *(tampilkan bersama "% masuk chart" = notoriety_year not null)* |
| Waktu menuju notable | median(notoriety_year − release_year) |
| Kolaborator unik | jumlah artis berbeda yang berbagi karya |
| Skor pengaruh | in-degree pengaruh pada karya artis (berapa kali karyanya dirujuk), opsional PageRank pada subgraf pengaruh |
| Dominasi label | share karya per label (RecordedBy+DistributedBy), HHI per genre |
| Skor rising star | lihat di bawah |

**Skor Rising Star (Q3)**: dihitung per artis per tahun, lalu dinormalisasi (z-score/min-max) dalam genre:
```
rising_star = 0.30·notable_works_last5y
            + 0.20·growth_works (YoY)
            + 0.20·influence_received_last5y   (karyanya dirujuk orang lain)
            + 0.15·unique_collaborators_last5y
            + 0.15·label_reach (jumlah label berbeda)
```
- **Validasi bobot**: backtest pada Sailor Shift. Skor di 2023–2026 seharusnya sudah tinggi sebelum ia viral di 2028. Kalau tidak, sesuaikan bobotnya.
- **Prediksi 5 tahun (Q3b)**: ambil artis Oceanus Folk yang aktif ≥ 2035, karier ≤ 10 tahun, belum mencapai puncak, skor tertinggi dan tren naik → pilih **top 3** + alasan berbasis data.
- **3 artis pembanding (Q3a)**: Sailor Shift + 2 artis dengan pola berbeda (misalnya lonjakan cepat vs naik perlahan) yang dipilih dari distribusi skor.

### Tahap 4 — Dashboard (Minggu 3–4)
Filter global di sidebar: rentang tahun, genre, tipe karya, era.

**Halaman 1 — Ringkasan Eksekutif**
- KPI cards: total karya, % masuk chart, genre teratas, jumlah artis aktif (tahun terpilih), YoY growth Oceanus Folk
- Line/area chart rilis per tahun per genre (Oceanus Folk di-highlight, garis vertikal 2023/2026/2028/2040)
- Bar dominasi label teratas

**Halaman 2 — Profil Sailor Shift (Q1)**
- *Q1a* Timeline "dipengaruhi oleh": sumbu x tahun, baris = artis/karya sumber pengaruh, warna = jenis edge (InStyleOf, Interpolates, …). Termasuk pengaruh langsung tingkat artis: Ivy Echos, The Saltwater Weavers, Drowned Harbor, The Fiddle & The Fjord. (Koreksi: Cassette Future, Silver Veil, dkk. adalah artis yang *dipengaruhi oleh* Sailor, sehingga masuk Q1b.)
- *Q1b* Ego-network 2-hop: kolaborator (lewat karya bersama dan Ivy Echos) + yang ia pengaruhi langsung/tidak langsung. Slider kedalaman 1–2 hop
- *Q1c* Sankey: Sailor → karya → karya yang merujuk → artis Oceanus Folk lain
- Tabel diskografi (song/album, tahun, notable, peran: performer/lyricist)

**Halaman 3 — Sebaran Oceanus Folk (Q2)**
- *Q2a* Line kumulatif jumlah karya genre lain yang dipengaruhi Oceanus Folk per tahun + bar per tahun → menjawab "intermittent atau gradual". Tandai tahun-tahun lonjakan
- *Q2b* Bar/treemap genre terpengaruh (Desert Rock, Indie Folk, Dream Pop, …) + top artis terpengaruh
- *Q2c* Diverging bar "OF → genre lain" vs "genre lain → OF" (slide 7), dibelah sebelum vs sesudah Sailor (toggle era)
- Chord diagram antar-genre (opsional, nilai tambah "visual baru" yang diminta VAST)

**Halaman 4 — Radar Rising Star (Q3)**
- Radar chart 5 komponen skor untuk 3 artis terpilih
- Small multiples: karya kumulatif, notable kumulatif, pengaruh diterima per tahun (sumbu x = "tahun sejak debut" agar bisa dibandingkan)
- Tabel leaderboard prediksi + penjelasan
- Pemilih artis (search by name/id)

### Tahap 5 — Validasi, Insight & Laporan (Minggu 4–5)
- Cross-check angka dashboard dengan query manual di notebook (minimal 1 cek per KPI)
- Tulis jawaban per pertanyaan VAST (±250 kata + gambar) sesuai Answer Sheet
- Update PPT: tambah slide hasil (screenshot dashboard), definisi era, ejaan "Ivy Echos"
- Deploy: Streamlit Community Cloud (gratis) atau demo lokal

---

## 3. Pembagian tugas (5 anggota)

| Peran | Tanggung jawab utama |
|---|---|
| Anggota 1 | ETL: extract, cleaning, star schema (Tahap 1–2) |
| Anggota 2 | Metrik & skor rising star, backtest (Tahap 3) |
| Anggota 3 | Integrasi Streamlit, Halaman 1 & 2, deploy |
| Anggota 4 | Halaman 3 (sebaran OF, chord/diverging) |
| Anggota 5 | Halaman 4, validasi angka, laporan & PPT akhir |

## 4. Timeline

| Minggu | Deliverable |
|---|---|
| 1 | Repo + extract + EDA notebook, daftar issue data |
| 2 | Star schema final (parquet), tabel metrik dasar |
| 3 | Skor rising star + backtest Sailor, Halaman 1–2 |
| 4 | Halaman 3–4, filter global, polishing |
| 5 | Validasi, jawaban Q1–Q3, PPT final, demo |

## 5. Risiko & mitigasi tambahan (melengkapi slide 14)

| Risiko | Mitigasi |
|---|---|
| Graf penuh (17k node) terlalu berat dirender | Tampilkan ego-network/subgraf saja, batasi ≤ 300 node, pre-compute di ETL |
| `notable` tidak diskriminatif (93%) | Pakai notoriety_date + pengaruh sebagai proksi utama popularitas |
| Bobot skor rising star subjektif | Backtest pada Sailor, tampilkan bobot di UI (slider) agar transparan |
| Nama duplikat menyesatkan | Join pakai id; sertakan id di tooltip |
| Data mencapai 2040 ("masa depan") | Anggap 2040 sebagai "tahun sekarang" dalam skenario, prediksi untuk 2041–2045 |

## 6. Definition of Done
- [ ] `python etl/build_schema.py` menghasilkan semua tabel dim/fact tanpa error, jumlah baris sesuai slide 12
- [ ] 4 halaman dashboard berjalan dengan filter tahun & genre
- [ ] Setiap sub-pertanyaan Q1a–Q3b punya minimal satu visual + jawaban tertulis
- [ ] 3 prediksi rising star beserta alasannya
- [ ] PPT final diperbarui dengan hasil dan definisi
