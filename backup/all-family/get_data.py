#!/usr/bin/env python3
"""Download and extract Federal Reserve SCF public summary CSVs.

The summary extract is available for every triennial SCF wave from 1989
through 2025. The Fed's summary extract dollar values are already adjusted
to 2025 dollars. Files are saved under data/raw/ as both the downloaded ZIP
and the extracted CSV.
"""

from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile
import io


BASE = "https://www.federalreserve.gov"
YEARS = range(1989, 2026, 3)
OUT_DIR = Path(__file__).resolve().parent / "data" / "raw"


class Links(HTMLParser):
    """Collect anchor text and href pairs from a Fed survey page."""

    def __init__(self):
        super().__init__()
        self._href = None
        self._text = []
        self.items = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href:
            label = " ".join(" ".join(self._text).split())
            self.items.append((label, self._href))
            self._href = None
            self._text = []


def fetch(url):
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (SCF research downloader)"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def summary_csv_url(year):
    page = (f"{BASE}/econres/scfindex.htm" if year == 2025
            else f"{BASE}/econres/scf_{year}.htm")
    parser = Links()
    parser.feed(fetch(page).decode("utf-8", errors="replace"))
    for label, href in parser.items:
        if "csv extract data" in label.lower():
            return href if href.startswith("http") else BASE + href
    raise RuntimeError(f"Could not find the CSV summary-extract link on {page}")


def download_and_extract(year):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = OUT_DIR / f"scf_{year}_summary_extract_csv.zip"
    csv_path = OUT_DIR / f"scf_{year}_summary_extract.csv"

    if not zip_path.exists() or zip_path.stat().st_size == 0:
        url = summary_csv_url(year)
        payload = fetch(url)
        if not payload.startswith(b"PK\x03\x04"):
            raise RuntimeError(f"Expected a ZIP from {url}; received {len(payload)} bytes")
        zip_path.write_bytes(payload)
        print(f"Downloaded {zip_path.name} ({len(payload):,} bytes)")
    else:
        print(f"Already downloaded: {zip_path.name}")

    with ZipFile(zip_path) as archive:
        csv_names = [name for name in archive.namelist()
                     if name.lower().endswith(".csv")]
        if len(csv_names) != 1:
            raise RuntimeError(f"Expected one CSV in {zip_path.name}; found {csv_names}")
        csv_path.write_bytes(archive.read(csv_names[0]))
    print(f"Extracted {csv_path.name}")


def main():
    for year in YEARS:
        print(f"Processing {year}...", flush=True)
        download_and_extract(year)


if __name__ == "__main__":
    main()
