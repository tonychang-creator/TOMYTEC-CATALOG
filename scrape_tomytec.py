#!/usr/bin/env python3
"""Export Tomica Limited Vintage / NEO product data to tomytec_data.json.

The script visits only the two supplied lineup pages and the product-detail pages
linked from them.  It deliberately makes requests sequentially and sleeps between
every request.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://minicar.tomytec.co.jp"
SERIES = {
    # The supplied lineup pages declare these series IDs. Product cards are
    # subsequently loaded from the official product-search API via JavaScript.
    "TLV": {"id": "1", "lineupUrl": f"{BASE_URL}/lineup/tlv/"},
    "TLV NEO": {"id": "2", "lineupUrl": f"{BASE_URL}/lineup/tlvneo/"},
}
SEARCH_API_URL = f"{BASE_URL}/product/api/search.php"
# Most products use LV-198a / LV-N285d.  Some official TLV releases are
# explicitly branded only "LV", so retain that legitimate model number too.
# The lookarounds avoid matching the "LV" suffix inside a word such as "TLV".
MODEL_RE = re.compile(r"(?<![A-Z0-9-])(LV(?:-N\d+[a-z]?|-\d+[a-z]?)?)(?![A-Z0-9-])", re.IGNORECASE)
RELEASE_RE = re.compile(r"発売時期\s*[：:]\s*([0-9０-９]{4}年\s*[0-9０-９]{1,2}月)")


class PoliteClient:
    def __init__(self, delay: float) -> None:
        self.delay = delay
        self.last_request = 0.0
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "TomytecCatalogExporter/1.0 (+personal static-site data export)",
                "Accept-Language": "ja,en;q=0.8",
            }
        )

    def get(self, url: str) -> requests.Response:
        return self.request("GET", url)

    def post(self, url: str, data: dict, headers: dict | None = None) -> requests.Response:
        return self.request("POST", url, data=data, headers=headers)

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        wait = self.delay - (time.monotonic() - self.last_request)
        if wait > 0:
            time.sleep(wait)
        response = self.session.request(method, url, timeout=30, **kwargs)
        self.last_request = time.monotonic()
        response.raise_for_status()
        return response


def text(node) -> str:
    return node.get_text(" ", strip=True) if node else ""


def product_urls(markup: str, page_url: str) -> set[str]:
    """Return unique official product-detail links from official card markup."""
    soup = BeautifulSoup(markup, "html.parser")
    urls = set()
    for anchor in soup.select("a[href]"):
        url = urljoin(page_url, anchor["href"])
        parsed = urlparse(url)
        if parsed.netloc == urlparse(BASE_URL).netloc and "/product/detail.html" in parsed.path:
            urls.add(url)
    return urls


def first_image_url(soup: BeautifulSoup, page_url: str) -> str:
    # Product pages normally expose the primary image through Open Graph metadata.
    meta = soup.select_one('meta[property="og:image"], meta[name="twitter:image"]')
    if meta and meta.get("content"):
        return urljoin(page_url, meta["content"])

    # Fallback: choose the first content image, skipping common decorative assets.
    for image in soup.select(".productspec .images img, main img, #contents img, .contents img"):
        source = image.get("data-src") or image.get("src")
        if source and not re.search(r"(logo|icon|banner|header|footer)", source, re.I):
            return urljoin(page_url, source)
    return ""


def parse_product(soup: BeautifulSoup, page_url: str, fallback_series: str) -> dict | None:
    # The site logo is also an h1.  Instead of relying on a class that has varied
    # between page versions, choose the heading that actually contains an LV code.
    heading = ""
    model_match = None
    for candidate in (text(node) for node in soup.select("h1, h2")):
        match = MODEL_RE.search(candidate)
        if match:
            heading, model_match = candidate, match
            break

    # The document title is a stable fallback, e.g. "LV-198a ... | 製品をさがす".
    page_title = text(soup.title).split(" | ", 1)[0]
    if not model_match:
        match = MODEL_RE.search(page_title)
        if match:
            heading, model_match = page_title, match

    if model_match:
        model_number = model_match.group(1)
        name = heading[model_match.end() :].strip(" -–—｜|")
        series = "TLV NEO" if model_number.upper().startswith("LV-N") else fallback_series
    else:
        # Official search results also include a small number of related items
        # without an LV / LV-N identifier. Retain them under a distinct group.
        model_number = ""
        name = text(soup.select_one(".productspec h1")) or page_title
        series = "Other"

    page_text = text(soup)
    release_match = RELEASE_RE.search(page_text)
    release_date = re.sub(r"\s+", "", release_match.group(1)) if release_match else ""

    return {
        "series": series,
        "modelNumber": model_number,
        "name": name,
        "releaseDate": release_date,
        "imageUrl": first_image_url(soup, page_url),
        "productUrl": page_url,
    }


def collect(
    client: PoliteClient,
    max_pages_per_series: int | None = None,
    known_product_urls: set[str] | None = None,
) -> list[dict]:
    details: dict[str, str] = {}
    for series, config in SERIES.items():
        print(f"Reading lineup: {config['lineupUrl']}", file=sys.stderr)
        page = 1
        has_more = True
        while has_more and (max_pages_per_series is None or page <= max_pages_per_series):
            print(f"  Reading product page {page}", file=sys.stderr)
            payload = {
                "keyword": "", "yyyy": "", "mm": "", "series": config["id"],
                "scale": "", "release": "", "maker": "", "sorts": "",
                "dataType": "all" if page == 1 else "add", "page": str(page),
            }
            response = client.post(
                SEARCH_API_URL,
                data=payload,
                headers={"Referer": config["lineupUrl"]},
            )
            data = response.json()
            cards = data.get("dblineup_src", "")
            count_before = len(details)
            for detail_url in product_urls(cards, SEARCH_API_URL):
                details.setdefault(detail_url, series)
            # The API normally returns a JSON boolean; accept its common 1 / "1"
            # representations too, but do not treat the string "0" as true.
            has_more = data.get("btn_flg") in (True, 1, "1") and len(details) > count_before
            page += 1

    if not details:
        raise RuntimeError(
            "No product links were returned by the official product-search API. "
            "The API response format may have changed; inspect product/api/search.php."
        )

    unknown_details = {
        detail_url: series
        for detail_url, series in details.items()
        if detail_url not in (known_product_urls or set())
    }
    if known_product_urls is not None:
        print(f"Skipping {len(details) - len(unknown_details)} existing products", file=sys.stderr)

    products = []
    for index, (detail_url, series) in enumerate(sorted(unknown_details.items()), start=1):
        print(f"[{index}/{len(unknown_details)}] Reading product: {detail_url}", file=sys.stderr)
        soup = BeautifulSoup(client.get(detail_url).text, "html.parser")
        product = parse_product(soup, detail_url, series)
        if product:
            products.append(product)

    # A model number is the stable identifier; keep the result deterministic.
    return sorted(products, key=lambda item: (item["series"], item["modelNumber"].lower()))


def product_key(product: dict) -> str:
    """Use the stable official image URL when available to preserve annotations."""
    return product.get("imageUrl") or "|".join(
        (product.get("series", ""), product.get("modelNumber", ""), product.get("name", ""))
    )


def preserve_collection_statuses(products: list[dict], output_path: Path) -> list[dict]:
    """Carry manually added collectionStatus values across a data refresh."""
    if not output_path.exists():
        return products
    try:
        existing = json.loads(output_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return products

    statuses = {
        product_key(item): item["collectionStatus"]
        for item in existing
        if isinstance(item, dict) and item.get("collectionStatus") in {"owned", "planned"}
    }
    for product in products:
        status = statuses.get(product_key(product))
        if status:
            product["collectionStatus"] = status
    return products


def load_existing_products(output_path: Path) -> list[dict]:
    if not output_path.exists():
        return []
    try:
        data = json.loads(output_path.read_text(encoding="utf-8"))
        return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay", type=float, default=1.5, help="seconds between requests (default: 1.5)")
    parser.add_argument("--output", type=Path, default=Path("tomytec_data.json"), help="output JSON path")
    parser.add_argument(
        "--max-pages-per-series", type=int,
        help="test only: limit each series' search-result pages (omit for all pages)",
    )
    parser.add_argument(
        "--incremental", action="store_true",
        help="only fetch products whose productUrl is not already in the output JSON",
    )
    args = parser.parse_args()
    if args.delay < 0.5:
        parser.error("--delay must be at least 0.5 seconds")
    if args.max_pages_per_series is not None and args.max_pages_per_series < 1:
        parser.error("--max-pages-per-series must be at least 1")

    existing_products = load_existing_products(args.output)
    known_product_urls = {item.get("productUrl") for item in existing_products if item.get("productUrl")}
    if args.incremental and existing_products and not known_product_urls:
        parser.error("--incremental needs a prior full crawl that includes productUrl; run once without --incremental first")

    new_products = collect(
        PoliteClient(args.delay),
        args.max_pages_per_series,
        known_product_urls if args.incremental else None,
    )
    products = existing_products + new_products if args.incremental else new_products
    products = preserve_collection_statuses(products, args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(products)} products to {args.output}")


if __name__ == "__main__":
    main()
