from __future__ import annotations

import html
import json
from urllib.parse import urlparse

import networkx as nx
import pandas as pd
from pyvis.network import Network


def label_pendek(url: str, maksimal: int = 34) -> str:
    """Label simpel buat ditampilin di graph, biar gak kepanjangan."""
    parsed = urlparse(url)
    teks = parsed.netloc + (parsed.path if parsed.path != "/" else "")
    teks = teks.rstrip("/")
    if len(teks) > maksimal:
        teks = teks[: maksimal - 3] + "..."
    return teks


def _warna_skor(skor: float, maks: float) -> str:
    """Campur warna dari biru muda ke biru tua sesuai besar PageRank."""
    rasio = 0.0 if maks <= 0 else max(0.0, min(1.0, skor / maks)) ** 0.6
    awal = (207, 227, 243)  # #cfe3f3
    akhir = (29, 78, 137)  # #1d4e89
    r, g, b = (round(a + (z - a) * rasio) for a, z in zip(awal, akhir))
    return f"#{r:02x}{g:02x}{b:02x}"


def _tooltip(url: str, baris: pd.Series) -> str:
    judul = html.escape(str(baris.get("judul") or "(tanpa judul)"))
    url_aman = html.escape(str(url))
    return (
        f"<b>{judul}</b><br>"
        f"<span style='font-size:11px;color:#8aa0b8'>{url_aman}</span><br><br>"
        f"PageRank <b>{baris['pagerank']:.6f}</b><br>"
        f"in-degree {int(baris['in_degree'])} &middot; "
        f"out-degree {int(baris['out_degree'])}"
    )


def html_graph(
    graph: nx.DiGraph,
    tabel: pd.DataFrame,
    tinggi: int = 620,
    fisika: bool = False,
    label_semua: bool = False,
) -> str:
    """Bikin HTML graph interaktif: scroll buat zoom, geser buat pan, hover buat detail.

    Posisi simpul dihitung dulu pakai spring layout, jadi pas dibuka graphnya
    langsung rapi tanpa perlu nunggu animasi fisika.
    """
    if graph.number_of_nodes() == 0:
        return ""

    net = Network(
        height=f"{tinggi}px",
        width="100%",
        directed=True,
        bgcolor="#ffffff",
        font_color="#243b53",
        cdn_resources="in_line",  # JS-nya ikut di dalam HTML, gak butuh internet
    )

    posisi = nx.spring_layout(graph, seed=42, k=0.9, iterations=120)
    skor = dict(zip(tabel["url"], tabel["pagerank"]))
    maks = max(skor.values()) if skor else 0.0
    info = tabel.set_index("url")

    batas_label = graph.number_of_nodes() if label_semua else min(15, graph.number_of_nodes())
    url_berlabel = set(tabel.head(batas_label)["url"])

    for url in graph.nodes:
        nilai = skor.get(url, 0.0)
        baris = info.loc[url]
        net.add_node(
            url,
            label=label_pendek(url) if url in url_berlabel else "",
            title=_tooltip(url, baris),
            x=float(posisi[url][0]) * 1000,
            y=float(posisi[url][1]) * 650,
            size=10 + 44 * (0.0 if maks <= 0 else (nilai / maks) ** 0.5),
            color={
                "background": _warna_skor(nilai, maks),
                "border": "#13355e",
                "highlight": {"background": "#e76f51", "border": "#7f2b17"},
            },
        )

    for sumber, tujuan in graph.edges:
        net.add_edge(
            sumber,
            tujuan,
            arrows="to",
            title=f"{label_pendek(sumber, 40)} -> {label_pendek(tujuan, 40)}",
        )

    opsi = {
        "autoResize": True,
        "interaction": {
            "hover": True,
            "tooltipDelay": 90,
            "hideEdgesOnDrag": True,
            "navigationButtons": False,
            "keyboard": {"enabled": False},
            "multiselect": True,
            "dragNodes": True,
            "dragView": True,
            "zoomView": True,
        },
        "nodes": {
            "shape": "dot",
            "borderWidth": 1,
            "borderWidthSelected": 2,
            "font": {"size": 12, "face": "Segoe UI, Arial", "color": "#243b53"},
        },
        "edges": {
            "arrows": {"to": {"enabled": True, "scaleFactor": 0.45}},
            "color": {
                "color": "rgba(120,144,170,0.5)",
                "highlight": "#e76f51",
                "hover": "#5c7fa3",
            },
            "width": 0.7,
            "smooth": False,
            "selectionWidth": 1.2,
        },
        "physics": {
            "enabled": fisika,
            "barnesHut": {
                "gravitationalConstant": -8000,
                "centralGravity": 0.6,
                "springLength": 130,
                "springConstant": 0.03,
                "damping": 0.4,
                "avoidOverlap": 0.2,
            },
            "stabilization": {"enabled": True, "iterations": 150, "fit": True},
        },
        "layout": {"improvedLayout": False},
    }
    net.set_options(json.dumps(opsi))

    hasil = net.generate_html()
    # tanpa fisika, vis kadang gak otomatis muat semua simpul di layar
    sisipan = (
        "<script>"
        "if (window.network) { network.fit({ animation: false }); }"
        "</script>"
    )
    return hasil.replace("</body>", sisipan + "</body>")
