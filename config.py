"""Central configuration for the Spaargids scraper."""
from pathlib import Path
import os

TARGET_URL = "https://www.spaargids.be/sparen/spaartarieven.html"
START_DATE = "20210227114350" # Format: YYYYMMDDHHMMSS

OUTPUT_FILE = Path("data/spaargids_rates_gemini.json")
CSV_OUTPUT_FILE = Path("data/spaargids_rates_gemini.csv")
HTML_TABLE_DIR = Path("data/html_tables")

REQUEST_DELAY = 2  # seconds between Wayback calls
MAX_RETRIES = 3  # retries for a single Wayback call

# Google Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-flash-latest"