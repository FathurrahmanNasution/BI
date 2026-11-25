# Jawaban VAST Challenge 2025 MC1 — Kelompok 23

Semua angka berasal dari `data/processed/` (hasil `python etl/build_schema.py`) dan dapat dilihat di dashboard
(`streamlit run app/Home.py`). Halaman dashboard untuk tiap jawaban disebutkan dalam kurung.

> **Arah edge pengaruh.** `A —InStyleOf→ B` berarti A terinspirasi B. Jadi edge yang *masuk* ke Sailor
> (misalnya `Cassette Future —InStyleOf→ Sailor Shift`) berarti **Sailor memengaruhi** Cassette Future,
> bukan sebaliknya.

---

## Q1 · Profil karier Sailor Shift (halaman *Profil Sailor Shift*)

**Ringkasan:** 38 karya (2024–2040), 95% Oceanus Folk; berperan sebagai performer dan terutama *lyricist*;
48 kolaborator unik; mantan anggota **Ivy Echos** (di data dieja *Ivy Echos*) bersama Maya Jensen,
Lila "Lilly" Hartman, Jade Thompson, dan Sophie Ramirez.

### Q1a · Siapa yang paling memengaruhinya dari waktu ke waktu?
- **Tingkat artis (paling kuat dan personal):** Sailor ditautkan langsung ke **Ivy Echos** (*DirectlySamples*),
  band asalnya, serta tiga grup folk generasi sebelumnya: **The Saltwater Weavers** (Oceanus Folk, 1995–2001,
  *InStyleOf*), **Drowned Harbor** (Oceanus Folk, 2005–2013, *LyricalReferenceTo*), dan
  **The Fiddle & The Fjord** (Celtic Folk, 1980–1982, *InStyleOf*). Ivy Echos sendiri juga meminjam dari
  The Saltwater Weavers dan The Fiddle & The Fjord, jadi garis "tradisi" ini menurun lewat band tersebut.
- **Tingkat karya:** 26 relasi pengaruh dari karya Sailor (10 *InStyleOf*, 6 *CoverOf*, 5 *InterpolatesFrom*, 3 *LyricalReferenceTo*, 2 *DirectlySamples*).
  Rujukannya **menyebar ke banyak genre** (Indie Rock 4, Synthwave 3, Alternative Rock 3, Americana,
  Doom Metal, Dream Pop) dan tidak ada artis yang dirujuk lebih dari sekali.
- **Pola waktu:** awal karier (2024–2026) bersandar pada tradisi folk dan bandnya. Setelah 2028 rujukannya
  melebar ke rock dan synth, sejalan dengan suara "Tidal Pop" yang membuatnya viral.

### Q1b · Dengan siapa ia berkolaborasi, dan siapa yang ia pengaruhi?
- **Kolaborator (48):** paling sering Maya Jensen (4 karya), para anggota Ivy Echos, dan lingkaran
  **The Brine Choir** (Arlo Sterling, Lyra Blaze, Orion Cruz, Elara May, Cassian Rae), lalu Ewan MacCrae,
  Freya Lindholm, Kai Reynolds, Rusty Riggins.
- **Dipengaruhi langsung (7):** Cassette Future, The Hollow Monarchs (*InStyleOf*), The Phantom Operators,
  Claire Holmes (*InterpolatesFrom*), Silver Veil, Cassian Storm (*LyricalReferenceTo*),
  **Copper Canyon Ghosts** (*DirectlySamples*).
- **Dipengaruhi tidak langsung (2 langkah):** 9 artis tambahan yang meminjam dari kolaborator Sailor atau dari
  artis yang ia pengaruhi (lihat mode "2 langkah" di grafik jaringan).
- Catatan: tidak ada karya Sailor yang dirujuk langsung oleh karya lain. Pengaruhnya tercatat pada tingkat
  artis, bukan lagu tertentu.

### Q1c · Bagaimana ia memengaruhi kolaborator di komunitas Oceanus Folk?
- 25 dari 48 kolaborator (52%) **tetap berkarya secara mandiri** setelah pertama kali bekerja dengan Sailor:
  60 karya tanpa Sailor, **9 di antaranya masuk chart**.
- Polanya: Sailor menjadi *lyricist* di album debut grup-grup OF baru (The Brine Choir 2034,
  Selkie's Hollow 2037, Tidal Reverie 2033), lalu grup tersebut melanjutkan rilis single sendiri. Ia
  berperan sebagai **inkubator** komunitas.
- Rantai pengaruh: di luar lingkaran kolaborasinya, 3 artis OF (Copper Canyon Ghosts, Genevieve Bell,
  Mariner's Refrain) dipengaruhi oleh Sailor atau kolaboratornya.

---

## Q2 · Sebaran pengaruh Oceanus Folk (halaman *Sebaran Oceanus Folk*)

### Q2a · Putus-putus atau naik bertahap?
**Putus-putus hingga 2022, lalu naik tajam.** Pada 2000–2022 ada 12 tahun tanpa satu pun karya genre lain yang
terinspirasi OF. Satu-satunya lonjakan, tahun 2017 (12 relasi), tidak berlanjut. Sejak 2023 (Sailor bergabung
dengan Ivy Echos) jumlahnya konsisten tinggi: 27 (2023), 27 (2026), **39 (2027)**, 27 (2028), 34 (2029).
Setelah 2030 angkanya turun karena volume rilis seluruh genre di data memang menyusut drastis (≤ 40/tahun).

### Q2b · Genre dan artis yang paling terpengaruh
- **Genre:** Desert Rock (50), Indie Folk (42), Dream Pop (42), Space Rock (35), Synthwave (16). Total ada 16
  genre yang terjangkau.
- **Artis:** 512 performer terpengaruh. Yang paling sering adalah Min He (#5038, 10 relasi), disusul grup
  **Cosmic Drift** dan sejumlah performer lain (6 relasi). Pengaruh OF tersebar luas, tidak terkonsentrasi
  pada satu artis.

### Q2c · Bagaimana OF berubah dengan naiknya Sailor?

| Era | Relasi | Sumber inspirasi utama |
|---|---|---|
| Pra-Sailor (≤ 2022) | 63 | **Indie Folk 62%**, Synthwave 16% |
| Ivy Echos (2023–2027) | 84 | Indie Folk 52%, **Synthpop, Doom Metal, Desert Rock** |
| Solo Sailor (2028–2040) | 77 | Indie Folk 22%, **Dream Pop, Indie Rock, Psychedelic Rock, Alternative Rock** |

OF bergeser dari "folk turunan Indie Folk" menjadi genre hibrida yang menyerap rock dan pop. Jeda ke karya
sumber juga memanjang (median 7 → 11–13 tahun): OF modern banyak menggali katalog lama. Inspirasi
kontemporernya kini paling banyak berasal dari **Indie Folk, Dream Pop, dan Indie Rock**.

Arah sebaliknya juga bergeser: OF kini memengaruhi genre rock (Desert Rock, Space Rock), padahal dulu justru
dipengaruhi folk. Indie Folk muncul di kedua sisi (100 karya OF terinspirasi Indie Folk; 42 karya Indie Folk
terinspirasi OF).

---

## Q3 · Profil rising star (halaman *Radar Rising Star*)

**Skor rising star** (0–100) per artis per tahun, dihitung dalam jendela 5 tahun:
20% karya notable + 15% masuk chart + 20% pertumbuhan rilis + 15% pengaruh diterima + 15% kolaborator unik +
15% jangkauan label. Tiap komponen dihitung sebagai persentil terhadap seluruh artis-tahun.
**Validasi:** skor Sailor sudah masuk **top 10% pada 2025** (peringkat 337 dari 3.469 artis aktif), tiga
tahun sebelum single-nya viral, dan menjadi **#1 pada 2034–2035**.

### Q3a · Tiga karier yang dibandingkan

| Artis | Pola | Bukti |
|---|---|---|
| **Sailor Shift** (OF, 2024–) | *Tumbuh stabil + jaringan* | Rilis setiap 1–2 tahun, kolaborator unik naik hingga 27/5 th, puncak skor 89 (2034) |
| **Orla Seabloom** (OF, 2029) | *Meledak sekali* | 8 karya dalam satu tahun, 7 masuk chart (terbanyak di OF), tanpa kolaborasi dan tanpa rilis lanjutan; skor 65 lalu hilang |
| **Jay Walters** (Southern Gothic Rock, 1984–2030) | *Pengaruh naik perlahan* | Sedikit rilis per tahun, tetapi menjadi artis yang paling banyak dirujuk (163 relasi pengaruh); puncak skor 96 (1998) |

**Profil rising star:** sinyal paling awal adalah **pertumbuhan rilis + jaringan kolaborasi yang melebar**.
Masuk chart tanpa jaringan (pola Orla) tidak berkelanjutan, sedangkan pengaruh (pola Jay) datang belakangan.

### Q3b · Tiga prediksi bintang Oceanus Folk 2041–2045
Kandidat: ≥ 50% karya OF, debut ≥ 2020, bukan Sailor. Skor = rata-rata skor rising star 2036–2040.

1. **The Brine Choir** (grup, debut 2034, skor 59,6): tiga album bersama Sailor sebagai lyricist (2034, 2035,
   2038) plus single mandiri. Kelima anggotanya komposer/penulis lirik. Polanya paling mirip lintasan Sailor.
2. **Copper Canyon Ghosts** (grup, debut 2034, skor 50,2): 5 karya masuk chart dalam dua tahun, langsung
   *sample* Sailor, dan berkolaborasi dengan Beatrice Albright dan Daniel O'Connell. Gabungan popularitas
   cepat dan jaringan.
3. **Selkie's Hollow** (grup, debut 2037, skor 50,1): debut termuda. Empat single dan album bersama Sailor dan
   Maya Jensen (eks Ivy Echos). Posisinya mirip Sailor pada 2024.

*Keterbatasan:* data setelah 2030 sangat tipis, sehingga prediksi bersifat indikatif. Bobot dapat diubah di
dashboard untuk menguji ketahanan peringkat.
