"""Persistence helpers: JSON + CSV."""
import csv
import json
from datetime import datetime
from pathlib import Path

import config
from log_setup import error, warning

__all__ = [
    "format_date",
    "load_json",
    "save_json",
    "update_csv",
]

def format_date(ts: str):
    try:
        return datetime.strptime(ts, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return ts


def load_json(path: str = config.OUTPUT_FILE):
    try:
        return json.loads(Path(path).read_text("utf-8"))
    except FileNotFoundError:
        return []
    except Exception as exc:
        warning(f"Cannot read {path}: {exc}")
        return []


def save_json(data, path: str = config.OUTPUT_FILE):
    try:
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), "utf-8")
        return True
    except Exception as exc:
        error(f"Cannot write {path}: {exc}")
        return False


def update_csv(results, path: str = config.CSV_OUTPUT_FILE):
    rows = []
    for r in results:
        date = format_date(r["timestamp"]).split()[0]
        for acc in r.get("extracted_rates", []):
            if "error" in acc:
                continue
            rows.append(
                {
                    "date": date,
                    "account_name": acc.get("account_name"),
                    "basis": acc.get("basis"),
                    "aangroei": acc.get("aangroei"),
                    "getrouw": acc.get("getrouw"),
                    "total": acc.get("total"),
                }
            )
    if not rows:
        return False

    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        return True
    except Exception as exc:
        error(f"Cannot write CSV {path}: {exc}")
        return False
