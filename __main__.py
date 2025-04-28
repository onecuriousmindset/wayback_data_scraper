"""Main entry point for the Spaargids scraper."""
import time
from pathlib import Path
from utils import wayback, table_utils, gemini_utils, storage
from log_setup import logger
import config

def ensure_directories():
    """Create necessary data directories if they don't exist."""
    config.HTML_TABLE_DIR.mkdir(parents=True, exist_ok=True)
    # Ensure parent directory of output files exists
    Path(config.OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(config.CSV_OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
    logger.debug("Ensured necessary data directories exist.")

def main():
    """Run the complete scraping pipeline."""
    start_time = time.time() # Start timer
    logger.info(f"--- Starting Spaargids Scraper ({time.strftime('%Y-%m-%d %H:%M:%S')}) ---")

    # Create necessary directories
    ensure_directories()

    # --- Load existing results to avoid reprocessing ---
    logger.info(f"Loading existing results from {config.OUTPUT_FILE}...")
    existing_results = storage.load_json(config.OUTPUT_FILE)
    processed_timestamps = set(item["timestamp"] for item in existing_results if "timestamp" in item)
    logger.info(f"Found {len(existing_results)} existing results. {len(processed_timestamps)} unique timestamps already processed.")
    # Initialize results with existing data
    results = existing_results
    # ----------------------------------------------------

    # Get all potential snapshots from Wayback
    logger.info("Fetching snapshot list from Wayback Machine...")
    all_snapshots = wayback.get_snapshots(config.TARGET_URL, config.START_DATE)
    if not all_snapshots:
         logger.warning("No snapshots returned from Wayback Machine. Exiting.")
         return # Exit if no snapshots found

    # --- Filter out already processed snapshots ---
    snapshots_to_process = [
        snap for snap in all_snapshots if snap[0] not in processed_timestamps
    ]
    total_to_process = len(snapshots_to_process)
    logger.info(f"Found {total_to_process} new snapshots to process.")
    # ---------------------------------------------

    if not snapshots_to_process:
        logger.info("No new snapshots require processing.")
        return

    processed_count_this_run = 0
    # Process each NEW snapshot
    for idx, snapshot_data in enumerate(snapshots_to_process, 1):
        # Ensure snapshot_data has at least timestamp and url
        if len(snapshot_data) < 2:
            logger.warning(f"Skipping invalid snapshot data entry: {snapshot_data}")
            continue
        timestamp, url = snapshot_data[0], snapshot_data[1]

        logger.info("")
        logger.info("=" * 60)
        logger.info(f"Processing snapshot {idx}/{total_to_process}: Timestamp {timestamp}")
        logger.info("=" * 60)
        snapshot_start_time = time.time()
        snapshot_success = False

        try:
            # Fetch HTML
            html = wayback.fetch_raw_html(timestamp, config.TARGET_URL) # Use config.TARGET_URL for consistency
            if not html:
                logger.warning(f"Failed to fetch HTML for {timestamp}. Skipping.")
                results.append({
                    "timestamp": timestamp,
                    "formatted_date": storage.format_date(timestamp),
                    "wayback_url": f"https://web.archive.org/web/{timestamp}/{config.TARGET_URL}",
                    "extracted_rates": [{"error": "Failed to fetch HTML"}]
                })
                continue # Move to the next snapshot

            # Find table
            table = table_utils.find_rates_table(html)
            if not table:
                logger.warning(f"No valid rates table found in snapshot {timestamp}. Skipping.")
                results.append({
                    "timestamp": timestamp,
                    "formatted_date": storage.format_date(timestamp),
                    "wayback_url": f"https://web.archive.org/web/{timestamp}/{config.TARGET_URL}",
                    "extracted_rates": [{"error": "No suitable table found"}]
                })
                continue # Move to the next snapshot

            # Save table HTML for debugging
            table_html_str = str(table)
            table_utils.save_table_html(timestamp, table_html_str)

            # Extract data with Gemini
            logger.info(f"Extracting data with Gemini for {timestamp}...")
            extracted_data = gemini_utils.extract_data_with_gemini(table_html_str)

            # Create result structure
            new_result = {
                "timestamp": timestamp,
                "formatted_date": storage.format_date(timestamp), # Use formatter from storage
                "wayback_url": f"https://web.archive.org/web/{timestamp}/{config.TARGET_URL}",
                "extracted_rates": extracted_data if extracted_data else [{"error": "Gemini extraction returned empty or failed"}]
            }
            results.append(new_result) # Append the new result

            # Check if Gemini actually returned data (not just an empty list or error placeholder)
            if extracted_data and not any("error" in item for item in extracted_data):
                snapshot_success = True
                processed_count_this_run += 1
                logger.success(f"Successfully processed snapshot {timestamp} ({idx}/{total_to_process})")
            else:
                 logger.warning(f"Gemini extraction may have failed or returned no data for {timestamp}. Check logs and output file.")

            # Save progress after each snapshot attempt (success or failure)
            storage.save_json(results, config.OUTPUT_FILE)
            logger.debug(f"Saved progress. Total results: {len(results)}")

        except KeyboardInterrupt:
             logger.warning("\nProcess interrupted by user. Saving final progress...")
             storage.save_json(results, config.OUTPUT_FILE)
             storage.update_csv(results, config.CSV_OUTPUT_FILE)
             logger.info("Progress saved. Exiting.")
             sys.exit(0) # Use sys.exit for clean exit
        except Exception as e:
             logger.error(f"!! Unexpected critical error processing snapshot {timestamp}: {e}", exc_info=True) # Add traceback
             # Add error entry if not already added
             if not any(r.get("timestamp") == timestamp for r in results[-1:]): # Avoid duplicates
                 results.append({
                    "timestamp": timestamp,
                    "formatted_date": storage.format_date(timestamp),
                    "wayback_url": f"https://web.archive.org/web/{timestamp}/{config.TARGET_URL}",
                    "extracted_rates": [{"error": f"Unexpected critical processing error: {str(e)}"}]
                 })
             storage.save_json(results, config.OUTPUT_FILE) # Save error state

        snapshot_duration = time.time() - snapshot_start_time
        logger.debug(f"Snapshot {timestamp} processing took {snapshot_duration:.2f} seconds.")
        # Add delay between snapshots
        if idx < total_to_process:
            logger.debug(f"Waiting {config.REQUEST_DELAY} seconds before next snapshot...")
            time.sleep(config.REQUEST_DELAY)


    # --- Final Summary and Save ---
    logger.info("")
    logger.info(f"--- Scraping Run Completed ({time.strftime('%Y-%m-%d %H:%M:%S')}) ---")
    logger.info(f"Attempted to process {total_to_process} new snapshots.")
    logger.success(f"Successfully extracted data for {processed_count_this_run} snapshots in this run.")
    logger.info(f"Total results in dataset: {len(results)}")

    # Final save of JSON and update CSV
    logger.info("Saving final JSON results...")
    storage.save_json(results, config.OUTPUT_FILE)
    logger.info("Updating final CSV file...")
    storage.update_csv(results, config.CSV_OUTPUT_FILE)

    total_duration = time.time() - start_time
    logger.info(f"Total execution time: {total_duration:.2f} seconds.")
    logger.info("--- Scraper Finished ---")


if __name__ == "__main__":
    import sys
    main()