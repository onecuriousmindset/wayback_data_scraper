"""Wayback Machine helpers."""
import time
import requests

import config
from log_setup import debug, info, warning, error, success

__all__ = [
    "get_snapshots",
    "fetch_raw_html",
]

def get_snapshots(target_url: str, start_date: str):
    """Return list of (timestamp, original_url) rows for *200 OK* HTML captures."""
    cdx_api = (
        "https://web.archive.org/cdx/search/cdx?"
        f"url={target_url}&output=json&fl=timestamp,original,mimetype,statuscode&"
        "filter=statuscode:200&filter=mimetype:text/html&from=" + start_date
    )
    debug("Requesting snapshot list from Wayback …")
    info(f"CDX URL: {cdx_api}")
    try:
        resp = requests.get(cdx_api, timeout=60)
        resp.raise_for_status()
        rows = resp.json()
    except Exception as exc:
        error(f"Snapshot request failed: {exc}")
        return []

    if rows and rows[0][0] == "timestamp":
        rows = rows[1:]
    success(f"{len(rows)} snapshots found")
    return rows


def fetch_raw_html(timestamp: str, target_url: str):
    """Return raw HTML for the given capture or *None* on failure."""
    url = f"https://web.archive.org/web/{timestamp}id_/{target_url}"
    debug(f"Fetching HTML for {timestamp}")

    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            resp = requests.get(url, timeout=45)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp.text
        except requests.Timeout:
            warning(f"Timeout {attempt}/{config.MAX_RETRIES}")
        except requests.RequestException as exc:
            warning(f"Error {attempt}/{config.MAX_RETRIES}: {exc}")
        if attempt < config.MAX_RETRIES:
            time.sleep(config.REQUEST_DELAY * attempt)

    error(f"Giving up on {url}")
    return None
