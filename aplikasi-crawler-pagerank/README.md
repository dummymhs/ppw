# Aplikasi Crawler + PageRank

Aplikasi Web Mining buat memetakan hubungan antarwebsite dari hasil crawling,
lalu menghitung tingkat kepentingan tiap halaman pakai PageRank.

Pipeline: URL awal -> crawl BFS -> ekstraksi tautan `<a href>` -> graph berarah
(halaman asal -> halaman tujuan) -> PageRank `alpha=0.85` -> tabel seluruh
halaman urut dari skor PageRank tertinggi.

## Struktur folder

```
aplikasi-crawler-pagerank/
├─ app/
│  ├─ crawler.py          # crawler BFS + ekstraksi tautan
│  ├─ graph_analysis.py   # bangun graph, PageRank, statistik, gambar statis
│  ├─ graph_interaktif.py # graph interaktif (pyvis/vis-network)
│  └─ streamlit_app.py    # antarmuka Streamlit
├─ output/                # contoh hasil crawl (CSV + GraphML)
├─ run_crawl.py           # crawler versi terminal, buat skala besar
├─ requirements.txt
└─ README.md
```

Logikanya sengaja dipisah dari Streamlit, jadi crawler bisa dites dan dipakai
buat crawl besar lewat terminal tanpa buka browser.

## Cara cepat (sekali klik)

Double-click **`jalankan_app.bat`** di folder ini. Browser langsung kebuka di
`http://localhost:8501`. Kalau Streamlit belum terpasang, launcher otomatis
menginstall dari `requirements.txt` dulu.

Jendela hitam yang muncul itu console-nya. Biarkan terbuka selama aplikasi
dipakai, dan tutup jendela itu kalau mau mematikan aplikasinya.

Kalau mau lebih praktis lagi, buat shortcut ke `jalankan_app.bat` (klik kanan
file, pilih **Send to > Desktop (create shortcut)**), lalu jalankan dari
Desktop.

## Menjalankan lewat terminal (kalau perlu)

Pakai environment Python yang sama dengan notebook (`enwebmining`). Dari folder
`aplikasi-crawler-pagerank`:

```powershell
& "..\enwebmining\Scripts\python.exe" -m pip install -r requirements.txt
& "..\enwebmining\Scripts\python.exe" -m streamlit run app\streamlit_app.py
```

Browser otomatis kebuka di `http://localhost:8501`. Isi URL awal
(`https://trunojoyo.ac.id`), atur jumlah halaman dan kedalaman, lalu klik
**Mulai Crawling**.

## Crawl skala besar lewat terminal

```powershell
& "..\enwebmining\Scripts\python.exe" run_crawl.py `
    --max-pages 100000 --max-depth 5 --delay 0.1 --abaikan-navigasi
```

Hasilnya disimpan di `output/`:

- `pagerank_<waktu>.csv` — semua halaman, skor PageRank, in/out-degree, judul
- `busur_<waktu>.csv` — daftar busur sumber -> tujuan
- `graph_<waktu>.graphml` — graph lengkap, bisa dibuka di Gephi

Parameter yang tersedia:

- `--start` URL awal (default `https://trunojoyo.ac.id`)
- `--max-pages` batas jumlah halaman (default 100)
- `--max-depth` kedalaman crawl (default 2)
- `--delay` jeda antar request dalam detik (default 0.2)
- `--alpha` faktor damping PageRank (default 0.85)
- `--semua-domain` ikut tautan ke domain lain, bukan cuma domain yang sama
- `--abaikan-navigasi` buang tautan menu di header, nav, footer, sidebar

## Graph interaktif

Tab **Graph** menampilkan graph pakai vis-network (lewat pyvis), bukan gambar
statis lagi. Di situ bisa scroll buat zoom, tarik latar buat geser, seret simpul,
dan hover buat lihat judul, URL, PageRank, serta in/out-degree. Ukuran simpul dan
gelapnya warna ngikutin skor PageRank.

Posisi simpul dihitung dulu pakai spring layout, jadi pas dibuka graphnya udah
rapi tanpa nunggu animasi. Opsi **Animasi fisika** bisa dinyalakan kalau mau
simpulnya saling tarik-menarik, tapi buat graph besar mending dimatikan biar
ringan.

HTML-nya juga bisa diunduh lewat tombol **Unduh graph interaktif (HTML)**. File
itu mandiri, JS-nya ikut di dalam, jadi bisa dibuka di browser mana aja tanpa
internet.

## Kenapa menu navigasi bisa diabaikan

Di situs kampus, header dan footer berisi menu yang sama di semua halaman. Kalau
tautan menu ikut dihitung, semua halaman saling terhubung ke belasan halaman
menu yang sama, graph jadi hampir lengkap, dan PageRank halaman-halaman menu
seri semua. Dengan opsi ini, yang dihitung cuma tautan di isi halaman, jadi
hubungan antarwebsite lebih mencerminkan isi.

Di aplikasi, opsi ini nyala secara default. Di `run_crawl.py` harus ditambah
manual pakai `--abaikan-navigasi`.

## Catatan

- Pakai `--delay` yang wajar dan jangan menembak server kampus terlalu cepat.
  Crawler ini juga sebaiknya dipakai di situs yang mengizinkan crawling.
- Target 100 ribu node butuh waktu, memori, dan penyimpanan besar. Mulai dari
  ratusan halaman dulu, cek hasilnya, baru naikkan batasnya.
- GraphML bisa dibuka di Gephi kalau mau visualisasi yang lebih enak dibaca.

## Deployment

Unggah folder ini ke GitHub, lalu di Streamlit Community Cloud pilih
`app/streamlit_app.py` sebagai entrypoint. Semua dependency sudah ada di
`requirements.txt`.
