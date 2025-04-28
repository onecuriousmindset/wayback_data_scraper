"""HTML table helpers: find the Spaargids rates table & save it for debugging."""
from pathlib import Path
from bs4 import BeautifulSoup

import config
from log_setup import debug, info, warning

TABLE_HEADER_KEYWORDS = {
    "aanbieder",
    "basisrente",
    "getrouwheid",
    "getrouwheidspremie",
    "totale",
}

__all__ = [
    "find_rates_table",
    "save_table_html",
]

def find_rates_table(html: str):
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    debug(f"Found {len(tables)} tables; scanning headers")

    for tbl in tables:
        head = tbl.find("thead") or tbl.find("tr")
        headers = [th.get_text(strip=True).lower() for th in head.find_all(["th", "td"])] if head else []
        if len(TABLE_HEADER_KEYWORDS.intersection(headers)) >= 2:
            return tbl
    return None


def save_table_html(timestamp: str, html: str):
    if not html:
        return

    Path(config.HTML_TABLE_DIR).mkdir(exist_ok=True)
    single_path = config.HTML_TABLE_DIR / f"{timestamp}.html"

    try:
        single_path.write_text(html, "utf-8")
        debug(f"Saved table markup to {single_path}")
    except Exception as exc:
        warning(f"Cannot write table file {single_path}: {exc}")
