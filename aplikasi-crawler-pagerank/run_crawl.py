from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import networkx as nx
import pandas as pd

from app.crawler import crawl
from app.graph_analysis import bangun_graph, peringkat_pagerank, statistik_graph


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Crawl website lalu hitung PageRank tiap halaman."
    )
    parser.add_argument("--start", default="https://trunojoyo.ac.id", help="URL awal")
    parser.add_argument("--max-pages", type=int, default=100, help="batas halaman")
    parser.add_argument("--max-depth", type=int, default=2, help="kedalaman crawl")
    parser.add_argument("--delay", type=float, default=0.2, help="jeda antar request")
    parser.add_argument("--alpha", type=float, default=0.85, help="faktor damping")
    parser.add_argument(
        "--semua-domain",
        action="store_true",
        help="ikut tautan ke domain lain juga (default cuma domain yang sama)",
    )
    parser.add_argument(
        "--abaikan-navigasi",
        action="store_true",
        help="buang tautan menu di header, nav, footer, dan sidebar",
    )
    parser.add_argument("--out", default="output", help="folder hasil")
    args = parser.parse_args()

    def lapor(jumlah: int, url: str) -> None:
        if jumlah % 10 == 0 or jumlah <= 3:
            print(f"[{jumlah}] {url}", flush=True)

    hasil = crawl(
        args.start,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        same_site_only=not args.semua_domain,
        delay=args.delay,
        abaikan_navigasi=args.abaikan_navigasi,
        on_progress=lapor,
    )

    graph = bangun_graph(hasil)
    tabel = peringkat_pagerank(graph, alpha=args.alpha)
    stat = statistik_graph(graph)

    folder = Path(args.out)
    folder.mkdir(parents=True, exist_ok=True)
    cap = datetime.now().strftime("%Y%m%d_%H%M%S")

    path_rank = folder / f"pagerank_{cap}.csv"
    path_busur = folder / f"busur_{cap}.csv"
    path_graph = folder / f"graph_{cap}.graphml"

    tabel.to_csv(path_rank, index=False)
    busur = pd.DataFrame(
        [(a, b) for a, b in graph.edges], columns=["sumber", "tujuan"]
    )
    busur.to_csv(path_busur, index=False)
    nx.write_graphml(graph, path_graph)

    print()
    print("===== RINGKASAN =====")
    print("Halaman        :", stat["simpul"])
    print("Busur          :", stat["busur"])
    print("Density        :", round(stat["density"], 4))
    print("Rata2 out-deg  :", round(stat["rata2_out"], 2))
    print("Waktu crawl    :", round(hasil.duration, 1), "detik")
    print("Gagal diambil  :", len(hasil.errors), "halaman")
    print()
    print("===== TOP 10 PAGERANK =====")
    for _, baris in tabel.head(10).iterrows():
        print(
            f"{baris['peringkat']:2d}. {baris['pagerank']:.6f}  "
            f"in={baris['in_degree']:3d} out={baris['out_degree']:3d}  {baris['url']}"
        )
    print()
    print("Hasil disimpan di:")
    print(" ", path_rank)
    print(" ", path_busur)
    print(" ", path_graph)


if __name__ == "__main__":
    main()
