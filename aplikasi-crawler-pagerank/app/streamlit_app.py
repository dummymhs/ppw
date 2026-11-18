from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR.parent) not in sys.path:
    sys.path.insert(0, str(APP_DIR.parent))

from app.crawler import crawl
from app.graph_analysis import (
    bangun_graph,
    matriks_adjacency,
    peringkat_pagerank,
    statistik_graph,
)
from app.graph_interaktif import html_graph

st.set_page_config(page_title="Crawler + PageRank", layout="wide")

st.title("Web Crawler + PageRank")
st.caption(
    "Crawl website kampus, bentuk graph keterhubungan antarwebsite, "
    "lalu hitung PageRank buat nyari halaman paling penting."
)

with st.sidebar:
    st.header("Pengaturan Crawling")
    with st.form("form_crawl"):
        start_url = st.text_input("URL awal", value="https://trunojoyo.ac.id")
        max_pages = st.slider("Maksimal halaman", 5, 300, 25, 5)
        max_depth = st.slider("Kedalaman crawl", 1, 3, 2)
        same_site = st.checkbox("Cuma ikuti domain yang sama", value=True)
        abaikan_navigasi = st.checkbox(
            "Abaikan menu header/footer",
            value=True,
            help=(
                "Menu navigasi muncul di semua halaman, jadi kalau ikut dihitung "
                "semua halaman saling terhubung ke halaman menu yang sama dan "
                "skor PageRank-nya jadi seri."
            ),
        )
        delay = st.slider("Jeda antar request (detik)", 0.0, 1.5, 0.2, 0.1)
        alpha = st.slider("Faktor damping alpha", 0.50, 0.95, 0.85, 0.05)
        mulai = st.form_submit_button("Mulai Crawling", type="primary", width="stretch")

    st.divider()
    st.caption(
        "Buat skala besar (sampai ratusan ribu node), jalanin lewat terminal: "
        "python run_crawl.py --max-pages 100000"
    )

if mulai:
    if not start_url.lower().startswith(("http://", "https://")):
        st.error("URL harus diawali http:// atau https://")
    else:
        progress = st.progress(0.0, text="Mulai crawl...")
        status = st.empty()

        def lapor(jumlah: int, url: str) -> None:
            progress.progress(
                min(jumlah / max_pages, 1.0),
                text=f"{jumlah} halaman diambil (target {max_pages})",
            )
            status.caption(f"Terakhir: {url}")

        try:
            hasil = crawl(
                start_url,
                max_pages=max_pages,
                max_depth=max_depth,
                same_site_only=same_site,
                delay=delay,
                abaikan_navigasi=abaikan_navigasi,
                on_progress=lapor,
            )
        except Exception as error:  # biar app gak mati kalau ada yang aneh
            st.exception(error)
            st.stop()

        progress.progress(1.0, text="Crawl selesai")
        status.empty()
        st.session_state["hasil"] = hasil
        st.session_state["alpha"] = alpha

hasil = st.session_state.get("hasil")

if hasil is None:
    st.info("Atur parameter di sidebar, lalu klik **Mulai Crawling**.")
    st.stop()

graph = bangun_graph(hasil)
tabel = peringkat_pagerank(graph, alpha=st.session_state.get("alpha", 0.85))
stat = statistik_graph(graph)

if graph.number_of_nodes() == 0:
    st.error("Gak ada halaman HTML yang berhasil diambil. Coba ganti URL atau naikkan timeout.")
    st.stop()

kolom = st.columns(5)
kolom[0].metric("Halaman", f"{stat['simpul']:,}")
kolom[1].metric("Busur (link)", f"{stat['busur']:,}")
kolom[2].metric("Density", f"{stat['density']:.4f}")
kolom[3].metric("Rata-rata out-degree", f"{stat['rata2_out']:.2f}")
kolom[4].metric("Waktu crawl", f"{hasil.duration:.1f} s")

tab_hasil, tab_graph, tab_matriks, tab_data, tab_catatan = st.tabs(
    ["Ranking PageRank", "Graph", "Matriks Adjacency", "Unduh Data", "Catatan"]
)

with tab_hasil:
    st.subheader("Semua halaman, urut dari PageRank tertinggi")
    daftar = tabel[["peringkat", "url", "pagerank", "in_degree", "out_degree", "judul"]]
    st.dataframe(
        daftar,
        hide_index=True,
        width="stretch",
        height=520,
        column_config={
            "peringkat": st.column_config.NumberColumn("Peringkat", width="small"),
            "url": st.column_config.LinkColumn("URL", width="large"),
            "pagerank": st.column_config.NumberColumn("PageRank", format="%.6f"),
            "in_degree": st.column_config.NumberColumn("In-degree", width="small"),
            "out_degree": st.column_config.NumberColumn("Out-degree", width="small"),
            "judul": st.column_config.TextColumn("Judul halaman"),
        },
    )
    st.caption(
        f"Menampilkan seluruh {len(tabel)} halaman hasil crawl, "
        f"total PageRank = {tabel['pagerank'].sum():.6f}. "
        "Tabelnya bisa diurutkan atau dicari lewat menu di tiap kolom."
    )

with tab_graph:
    st.subheader("Graph keterhubungan antarwebsite (interaktif)")
    kiri, kanan = st.columns(2)
    fisika = kiri.toggle(
        "Animasi fisika",
        value=False,
        help=(
            "Nyalain kalau mau simpulnya saling tarik-menarik. Buat graph besar "
            "mending dimatikan biar ringan, posisi awalnya udah dihitung rapi."
        ),
    )
    label_semua = kanan.toggle(
        "Label semua simpul",
        value=len(tabel) <= 60,
        help="Kalau simpulnya banyak, label bikin tampilan penuh. Default cuma 15 teratas.",
    )

    grafik = html_graph(graph, tabel, tinggi=640, fisika=fisika, label_semua=label_semua)
    st.iframe(grafik, height=640)

    st.caption(
        "Scroll buat zoom, tarik latar buat geser, seret simpulnya buat mindahin, "
        "dan hover buat lihat judul, URL, PageRank, serta in/out-degree. "
        "Ukuran simpul dan gelapnya warna ngikutin skor PageRank, label default "
        f"cuma {min(15, len(tabel))} halaman teratas."
    )
    st.download_button(
        "Unduh graph interaktif (HTML)",
        data=grafik.encode("utf-8"),
        file_name="graph_pagerank.html",
        mime="text/html",
        width="stretch",
    )

with tab_matriks:
    st.subheader("Matriks adjacency 15 halaman teratas")
    matriks = matriks_adjacency(graph, tabel, batas=15)
    st.dataframe(matriks, width="stretch")
    st.caption(
        "Baris = halaman asal, kolom = halaman tujuan. Angka 1 artinya ada tautan. "
        "Matriks ini yang jadi dasar perhitungan PageRank, karna PageRank nyari "
        "eigenvector kiri dari matriks transisinya."
    )

with tab_data:
    st.subheader("Unduh hasil crawl")
    kiri, kanan = st.columns(2)

    csv_rank = tabel.to_csv(index=False).encode("utf-8")
    kiri.download_button(
        "Unduh ranking PageRank (CSV)",
        data=csv_rank,
        file_name="pagerank.csv",
        mime="text/csv",
        width="stretch",
    )

    busur = pd.DataFrame(sorted(hasil.edges), columns=["sumber", "tujuan"])
    busur = busur[
        busur["sumber"].isin(graph.nodes) & busur["tujuan"].isin(graph.nodes)
    ]
    csv_busur = busur.to_csv(index=False).encode("utf-8")
    kanan.download_button(
        "Unduh daftar busur (CSV)",
        data=csv_busur,
        file_name="busur.csv",
        mime="text/csv",
        width="stretch",
    )

    st.write("Semua halaman hasil crawl:")
    st.dataframe(
        tabel[["url", "pagerank", "in_degree", "out_degree", "judul"]],
        hide_index=True,
        width="stretch",
        column_config={
            "url": st.column_config.LinkColumn("URL", width="large"),
            "pagerank": st.column_config.NumberColumn("PageRank", format="%.6f"),
        },
    )

with tab_catatan:
    st.subheader("Halaman yang gagal diambil")
    if hasil.errors:
        df_error = pd.DataFrame(hasil.errors)
        st.dataframe(df_error, hide_index=True, width="stretch")
    else:
        st.success("Semua halaman yang dikunjungi berhasil diambil.")

    st.divider()
    st.markdown(
        "**Cara kerja singkat.** Crawler jalan BFS dari URL awal. Tiap halaman diambil, "
        "semua tag tautan diekstrak, lalu tautan yang masih satu domain dimasukkan ke antrean. "
        "Pasangan halaman asal dan tujuan disimpan sebagai busur graph. Setelah crawl selesai, "
        "PageRank dihitung dengan alpha 0.85, lalu hasilnya diurutkan."
    )
    st.markdown(
        "**Buat skala besar.** Versi web ini dibatasi 300 halaman biar browser gak nunggu kelamaan. "
        "Buat target puluhan sampai ratusan ribu node, pakai `run_crawl.py` di terminal, "
        "hasilnya disimpan jadi CSV dan GraphML."
    )
