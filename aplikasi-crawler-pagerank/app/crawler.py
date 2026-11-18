from __future__ import annotations

import re
import time
from collections import deque
from dataclasses import dataclass, field
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# berkas yang jelas bukan halaman web, jadi gak perlu dikunjungi
SKIP_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".rar", ".7z", ".tar", ".gz",
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico",
    ".mp3", ".mp4", ".avi", ".mkv", ".mov", ".wav",
    ".css", ".js", ".json", ".xml", ".rss", ".woff", ".woff2", ".ttf",
}


@dataclass
class CrawlResult:
    start_url: str
    pages: dict = field(default_factory=dict)
    edges: set = field(default_factory=set)
    errors: list = field(default_factory=list)
    duration: float = 0.0

    @property
    def jumlah_halaman(self) -> int:
        return len(self.pages)

    @property
    def jumlah_edge(self) -> int:
        return len(self.edges)


def normalize_url(url: str) -> str:
    """Rapikan URL: buang fragment, samakan huruf host, buang port default."""
    url, _ = urldefrag(url.strip())
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    if scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]
    path = parsed.path or "/"
    path = re.sub(r"/{2,}", "/", path)
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{scheme}://{netloc}{path}{query}"


def site_key(url: str) -> str:
    """Kunci situs, dipakai buat nentuin satu domain atau bukan."""
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def bisa_dikunjungi(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if not parsed.netloc:
        return False
    path = parsed.path.lower()
    return not any(path.endswith(ext) for ext in SKIP_EXTENSIONS)


def ambil_tautan(
    soup: BeautifulSoup, base_url: str, abaikan_navigasi: bool = False
) -> list[str]:
    """Ambil semua href di satu halaman, ubah jadi URL absolut, buang duplikat.

    Kalau abaikan_navigasi=True, tautan yang cuma ada di header, nav, footer,
    atau sidebar dibuang. Tautan kayak gitu biasanya menu yang nongol di semua
    halaman, jadi bikin graph jadi hampir lengkap dan PageRank semua seri.
    """
    hasil = []
    terlihat = set()
    for tag in soup.find_all("a", href=True):
        if abaikan_navigasi and tag.find_parent(["header", "nav", "footer", "aside"]):
            continue
        href = tag["href"].strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
            continue
        url = normalize_url(urljoin(base_url, href))
        if not bisa_dikunjungi(url):
            continue
        if url in terlihat:
            continue
        terlihat.add(url)
        hasil.append(url)
    return hasil


def crawl(
    start_url: str,
    max_pages: int = 30,
    max_depth: int = 2,
    same_site_only: bool = True,
    delay: float = 0.2,
    timeout: int = 15,
    abaikan_navigasi: bool = False,
    on_progress=None,
) -> CrawlResult:
    """Crawl BFS dari start_url, catat semua busur halaman -> tautan.

    on_progress dipanggil tiap halaman selesai dengan (jumlah_halaman, url).
    """
    awal = normalize_url(start_url)
    mulai = time.time()

    sesi = requests.Session()
    sesi.headers.update({
        "User-Agent": USER_AGENT,
        "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml",
    })

    antre = deque([(awal, 0)])
    sudah_masuk = {awal}
    hasil = CrawlResult(start_url=awal)
    kunci_situs = None

    while antre and len(hasil.pages) < max_pages:
        url, kedalaman = antre.popleft()

        try:
            respon = sesi.get(url, timeout=timeout, allow_redirects=True)
            respon.raise_for_status()
        except requests.RequestException as error:
            hasil.errors.append({"url": url, "alasan": f"gagal diambil: {error}"})
            continue

        tipe = respon.headers.get("content-type", "").lower()
        if "html" not in tipe:
            hasil.errors.append({"url": url, "alasan": f"bukan HTML ({tipe or 'tanpa content-type'})"})
            continue

        url_akhir = normalize_url(respon.url)
        if kunci_situs is None:
            kunci_situs = site_key(url_akhir)

        soup = BeautifulSoup(respon.content, "lxml")
        judul = soup.title.get_text(" ", strip=True) if soup.title else ""
        tautan = ambil_tautan(soup, url_akhir, abaikan_navigasi=abaikan_navigasi)

        hasil.pages[url_akhir] = {
            "judul": judul,
            "kedalaman": kedalaman,
            "jumlah_tautan": len(tautan),
        }

        for target in tautan:
            if same_site_only and site_key(target) != kunci_situs:
                continue
            if target == url_akhir:
                continue
            hasil.edges.add((url_akhir, target))
            if target not in sudah_masuk and kedalaman + 1 <= max_depth:
                sudah_masuk.add(target)
                antre.append((target, kedalaman + 1))

        if delay > 0:
            time.sleep(delay)
        if on_progress is not None:
            on_progress(len(hasil.pages), url_akhir)

    hasil.duration = time.time() - mulai
    return hasil
