# Spaargids Wayback Scraper

This Python tool scrapes historical savings account interest rate data for Belgian banks from [Spaargids.be](https://www.spaargids.be/sparen/spaartarieven.html) using snapshots captured by the [Wayback Machine](https://web.archive.org/). It leverages Google's Gemini API for data extraction from HTML tables.

## Features

-   **Historical Data:** Fetches historical versions of the Spaargids interest rate page via the Wayback Machine.
-   **AI-Powered Extraction:** Uses the Google Gemini API to accurately parse the HTML table and extract structured data (account name, basis rate, loyalty premium, etc.).
-   **Data Persistence:** Saves the extracted data incrementally in both JSON and CSV formats.
-   **Debugging Support:** Stores the raw HTML of each processed table for easier debugging.
-   **Resilience:** Implements retries for fetching data from the Wayback Machine.
-   **Configurable:** Settings like target URL, start date, API keys, and request delays are managed in `config.py`.
-   **Detailed Logging:** Provides color-coded console logging and detailed file logging for monitoring and troubleshooting.

## Project Structure

```
wayback_data/
├── config.py           # Central configuration (URLs, API keys, settings)
├── log_setup.py        # Configures logging (console and file)
├── requirements.txt    # Project dependencies
├── README.md           
├── __main__.py         # Main execution script
│
├── data/               # Created automatically for output files
│   ├── html_tables/    # Stores raw HTML tables per snapshot (for debugging)
│   ├── spaargids_rates_gemini.json # Extracted data in JSON format
│   └── spaargids_rates_gemini.csv  # Extracted data in CSV format
│
├── log/                # Created automatically for log files
│   └── spaargids_extractor.log # Detailed execution log
│
└── utils/              # Utility modules
    ├── gemini_utils.py # Handles interaction with Google Gemini API
    ├── storage.py      # Handles saving data to JSON and CSV
    ├── table_utils.py  # Finds and saves the relevant HTML table
    └── wayback.py      # Interacts with the Wayback Machine API
```

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/onecuriousmindset/wayback_data_scraper
    cd wayback_data
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Google Gemini API Key:**
    *   Obtain an API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
    *   The script expects the API key to be available in the environment variable `GEMINI_API_KEY`. You can set it in your shell before running the script:
        ```bash
        export GEMINI_API_KEY='YOUR_API_KEY_HERE'
        ```
        Or, add it to a `.env` file (ensure `.env` is in your `.gitignore`) and use a library like `python-dotenv` if you prefer (though this is not included by default).
    *   Alternatively, you can modify `config.py` to directly assign the key, but using environment variables is strongly recommended for security.

2.  **Other Settings (Optional):**
    *   Review `config.py` to adjust the `TARGET_URL`, `START_DATE`, output filenames, request delays (`REQUEST_DELAY`), or the Gemini model (`GEMINI_MODEL`) if needed.

## Usage

Run the scraper from the project's root directory (`wayback_data`):

```bash
python -m wayback_data
```

Or, if you are inside the `wayback_data` directory:

```bash
python __main__.py
```

The script will:
1.  Create the `data/` and `log/` directories if they don't exist.
2.  Fetch the list of available snapshots from the Wayback Machine CDX API starting from `START_DATE`.
3.  Iterate through each snapshot:
    *   Fetch the raw HTML content.
    *   Attempt to find the specific interest rates table.
    *   Save the raw HTML of the found table to `data/html_tables/`.
    *   Send the table HTML to the Gemini API for data extraction.
    *   Append the extracted data to a list.
    *   Save the *cumulative* results to `spaargids_rates_gemini.json` after *each* successful snapshot processing and to `spaargids_rates_gemini.csv` after the script has completed.
4.  Log progress and potential errors to both the console and the log file.

## Output

-   **`data/html_tables/`**: Contains `.html` files, one for each processed snapshot's table (e.g., `20230115103000.html`). Useful for debugging parsing issues.
-   **`data/spaargids_rates_gemini.json`**: A JSON file containing a list of objects. Each object represents a snapshot and holds the `timestamp` and the `extracted_rates` (a list of dictionaries, one per account found in that snapshot).
-   **`data/spaargids_rates_gemini.csv`**: A CSV file containing the flattened data, with columns like `date`, `account_name`, `basis`, `aangroei`, `getrouw`, `total`.
-   **`log/spaargids_extractor.log`**: A text file containing detailed logs of the entire scraping process, including DEBUG level information.

## Logging

The scraper provides comprehensive logging:

-   **Console Output:** Shows messages from DEBUG level and above with color coding for different levels (DEBUG: White, INFO: Cyan, SUCCESS: Green, WARNING: Yellow, ERROR: Red, CRITICAL: Bright Red). Provides a real-time overview of the process.
-   **File Output:** Saves all log messages (DEBUG and above) to `log/spaargids_extractor.log` for detailed analysis and troubleshooting.