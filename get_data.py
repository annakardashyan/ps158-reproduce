#!/usr/bin/env python3
"""Download Federal Reserve public SCF microdata for each cross-sectional wave.

Files are saved as downloaded from the Board's year-specific SCF pages under
data/raw/. The script uses only Python's standard library.
"""

from html.parser import HTMLParser
from pathlib import Path
import ssl
from urllib.request import Request, urlopen


BASE = "https://www.federalreserve.gov"
YEARS = list(range(1989, 2026, 3))
OUT_DIR = Path(__file__).resolve().parent / "data" / "raw"
SSL_CONTEXT = ssl.create_default_context(cafile="/etc/ssl/cert.pem")


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None
        self.items = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")

    def handle_data(self, data):
        if self.href and data.strip():
            self.items.append((data.strip(), self.href))

    def handle_endtag(self, tag):
        if tag == "a":
            self.href = None


def fetch(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (SCF research downloader)"})
    with urlopen(req, timeout=60, context=SSL_CONTEXT) as response:
        return response.read()


def get_stata_urls(year):
    page = (f"{BASE}/econres/scfindex.htm" if year == 2025
            else f"{BASE}/econres/scf_{year}.htm")
    parser = Links()
    parser.feed(fetch(page).decode("utf-8", errors="replace"))
    main = []
    replicate = []
    for label, href in parser.items:
        text = label.lower()
        path = href.lower()
        if "stata" in text:
            if "replicate" in text or "rw" in path:
                replicate.append(href)
            elif "main survey" in text or "stata version" in text:
                main.append(href)
    if not main:
        raise RuntimeError(f"Could not locate the full public Stata data link on {page}")
    if not replicate:
        raise RuntimeError(f"Could not locate the Stata replicate-weight link on {page}")

    def absolute(href):
        return href if href.startswith("http") else BASE + href

    return absolute(main[0]), absolute(replicate[0])


def get_summary_stata_url(year):
    page = (f"{BASE}/econres/scfindex.htm" if year == 2025
            else f"{BASE}/econres/scf_{year}.htm")
    parser = Links()
    parser.feed(fetch(page).decode("utf-8", errors="replace"))
    for label, href in parser.items:
        text = label.lower()
        if "stata" in text and "extract data" in text:
            return href if href.startswith("http") else BASE + href
    raise RuntimeError(f"Could not locate the Stata summary-extract link on {page}")


def get_summary_csv_url(year):
    page = (f"{BASE}/econres/scfindex.htm" if year == 2025
            else f"{BASE}/econres/scf_{year}.htm")
    parser = Links()
    parser.feed(fetch(page).decode("utf-8", errors="replace"))
    for label, href in parser.items:
        text = label.lower()
        if "csv extract data" in text:
            return href if href.startswith("http") else BASE + href
    raise RuntimeError(f"Could not locate the CSV summary-extract link on {page}")


def download_zip(url, path):
    if path.exists() and path.stat().st_size:
        print(f"Already present: {path}")
        return
    payload = fetch(url)
    if not payload.startswith(b"PK\x03\x04"):
        raise RuntimeError(f"Expected a ZIP file from {url}; received {len(payload)} bytes")
    path.write_bytes(payload)
    print(f"Downloaded {path.name} ({len(payload):,} bytes)")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for year in YEARS:
        main_url, replicate_url = get_stata_urls(year)
        download_zip(main_url, OUT_DIR / f"scf_{year}_stata.zip")
        download_zip(replicate_url, OUT_DIR / f"scf_{year}_replicate_weights_stata.zip")
        summary_url = get_summary_stata_url(year)
        download_zip(summary_url, OUT_DIR / f"scf_{year}_summary_extract_stata.zip")
        csv_url = get_summary_csv_url(year)
        download_zip(csv_url, OUT_DIR / f"scf_{year}_summary_extract_csv.zip")


if __name__ == "__main__":
    main()
