from __future__ import annotations

from urllib.parse import urlparse

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd


def bangun_graph(hasil_crawl) -> nx.DiGraph:
    """Ubah hasil crawl jadi digraph yang cuma berisi halaman yang berhasil diambil."""
    graph = nx.DiGraph()
    for url, info in hasil_crawl.pages.items():
        graph.add_node(url, judul=info.get("judul", ""), kedalaman=info.get("kedalaman", 0))

    for sumber, target in hasil_crawl.edges:
        if sumber in graph and target in graph:
            graph.add_edge(sumber, target)

    return graph


def label_pendek(url: str, maksimal: int = 42) -> str:
    parsed = urlparse(url)
    teks = parsed.netloc + (parsed.path if parsed.path != "/" else "")
    teks = teks.rstrip("/")
    if len(teks) > maksimal:
        teks = teks[: maksimal - 3] + "..."
    return teks


def peringkat_pagerank(graph: nx.DiGraph, alpha: float = 0.85) -> pd.DataFrame:
    """Hitung PageRank lalu balikin tabel terurut dari skor paling besar."""
    skor = nx.pagerank(graph, alpha=alpha) if graph.number_of_nodes() else {}

    baris = []
    for url in graph.nodes:
        baris.append({
            "url": url,
            "judul": graph.nodes[url].get("judul", ""),
            "pagerank": skor.get(url, 0.0),
            "in_degree": graph.in_degree(url),
            "out_degree": graph.out_degree(url),
        })

    tabel = pd.DataFrame(baris)
    if tabel.empty:
        return tabel
    tabel = tabel.sort_values("pagerank", ascending=False).reset_index(drop=True)
    tabel.insert(0, "peringkat", tabel.index + 1)
    return tabel


def statistik_graph(graph: nx.DiGraph) -> dict:
    n = graph.number_of_nodes()
    l = graph.number_of_edges()
    if n == 0:
        return {"simpul": 0, "busur": 0, "density": 0.0,
                "rata2_out": 0.0, "rata2_in": 0.0, "maks_in": 0}
    return {
        "simpul": n,
        "busur": l,
        "density": nx.density(graph),
        "rata2_out": l / n,
        "rata2_in": l / n,
        "maks_in": max(dict(graph.in_degree()).values()),
    }


def gambar_graph(graph: nx.DiGraph, tabel: pd.DataFrame, maks_label: int = 12):
    """Gambar graph, ukuran simpul mengikuti PageRank, label cuma yang teratas."""
    fig, ax = plt.subplots(figsize=(11, 7))
    if graph.number_of_nodes() == 0:
        ax.text(0.5, 0.5, "Belum ada halaman yang berhasil di-crawl",
                ha="center", va="center")
        ax.axis("off")
        return fig

    pos = nx.spring_layout(graph, seed=42, k=0.9, iterations=120)
    skor = dict(zip(tabel["url"], tabel["pagerank"]))
    ukuran = [400 + 9000 * skor.get(node, 0.0) for node in graph.nodes]

    nx.draw_networkx_edges(
        graph, pos, ax=ax, edge_color="#b8c4d0", arrows=True,
        arrowsize=8, width=0.7, connectionstyle="arc3,rad=0.08",
    )
    nx.draw_networkx_nodes(
        graph, pos, ax=ax, node_size=ukuran, node_color="#8ecae6",
        edgecolors="#1f3b73", linewidths=0.6,
    )

    teratas = list(tabel.head(maks_label)["url"]) if not tabel.empty else []
    label = {url: label_pendek(url, 30) for url in teratas}
    nx.draw_networkx_labels(graph, pos, labels=label, ax=ax, font_size=7)

    ax.set_title("Graph keterhubungan antarwebsite (ukuran simpul = PageRank)", fontsize=11)
    ax.axis("off")
    fig.tight_layout()
    return fig


def matriks_adjacency(graph: nx.DiGraph, tabel: pd.DataFrame, batas: int = 15) -> pd.DataFrame:
    """Matriks adjacency untuk simpul paling penting, biar gak kebesaran."""
    if tabel.empty:
        return pd.DataFrame()

    simpul = list(tabel.head(batas)["url"])
    subgraph = graph.subgraph(simpul)
    matriks = nx.to_pandas_adjacency(subgraph, nodelist=simpul, dtype=int)

    # label pendek bisa aja sama buat dua URL beda, jadi harus dibikin unik
    label = []
    terpakai = {}
    for url in simpul:
        dasar = label_pendek(url, 28)
        terpakai[dasar] = terpakai.get(dasar, 0) + 1
        label.append(dasar if terpakai[dasar] == 1 else f"{dasar} #{terpakai[dasar]}")

    matriks.index = label
    matriks.columns = label
    return matriks
