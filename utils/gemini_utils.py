"""Google Gemini helper to pull structured data out of the Spaargids HTML table."""
import json
import re
import google.generativeai as genai

import config
from log_setup import debug, info, warning, error, success

__all__ = ["extract_data_with_gemini"]

def extract_data_with_gemini(table_html: str):
    if not table_html:
        warning("Cannot extract data, table HTML string is empty.")
        return []

    if not config.GEMINI_API_KEY:
        warning("GEMINI_API_KEY missing — skipping extraction")
        return []

    debug("Configuring Gemini API...")
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        debug(f"Using Gemini model: '{config.GEMINI_MODEL}'")
    except Exception as e:
        error(f"Error configuring Gemini or creating model: {e}")
        return []

    prompt = f"""Analyze the following HTML table content from a Spaargids.be snapshot.
Extract the savings account data.

For each row representing a savings account, extract the following information:
- account_name: The name of the savings account (SPAARREKENING), often found in the first column or identified by 'Aanbieder'. Clean the name.
- basis: The basis rate (Basisrente), as a numeric value (float). Use '.' as the decimal separator. If missing or not applicable, use null.
- aangroei: The growth bonus (Aangroeipremie), if available, as a numeric value (float). Use '.' as the decimal separator. If missing or not applicable, use null.
- getrouw: The loyalty bonus (Getrouwheidspremie), as a numeric value (float). Use '.' as the decimal separator. If missing or not applicable, use null.
- total: The total rate (Totale rente), if available, as a numeric value (float). Use '.' as the decimal separator. If missing or not applicable, use null.

Ensure all rates are converted to numeric types (float). Handle percentage signs (%) and comma (,) decimal separators appropriately during conversion.

Return ONLY a valid JSON array of objects, where each object represents one savings account. Do not include any introductory text, explanations, or markdown formatting like ```json or ```.

Example object format:
{{
  "account_name": "Example Account",
  "basis": 0.05,
  "aangroei": null,
  "getrouw": 0.15,
  "total": 0.20
}}

HTML TABLE CONTENT:
{table_html}"""

    debug("Sending table HTML to Gemini API for extraction...")
    extracted_data = [] # Initialize default return value
    response = None # Initialize response variable

    try:
        generation_config = genai.types.GenerationConfig(
            temperature=0.1,  # Lower temperature for more deterministic output
            candidate_count=1,
            max_output_tokens=4096,
        )
        safety_settings = [
            {"category":"HARM_CATEGORY_HARASSMENT","threshold":"BLOCK_NONE"},
            {"category":"HARM_CATEGORY_HATE_SPEECH","threshold":"BLOCK_NONE"},
            {"category":"HARM_CATEGORY_SEXUALLY_EXPLICIT","threshold":"BLOCK_NONE"},
            {"category":"HARM_CATEGORY_DANGEROUS_CONTENT","threshold":"BLOCK_NONE"},
        ]
        response = model.generate_content(
            prompt,
            safety_settings=safety_settings,
            generation_config=generation_config
        )

        debug("Received response from Gemini.")
        debug(f"Gemini Raw Response Text (first 500 chars): {response.text[:500]}...")

        try:
            extracted_data = json.loads(response.text)
            debug("Successfully parsed JSON directly from response text.")

        except json.JSONDecodeError as e_direct:
            warning(f"Direct JSON parsing failed: {e_direct}. Attempting regex fallback...")
            json_match = re.search(r'\[\s*{.*}\s*\]', response.text, re.DOTALL | re.MULTILINE)
            if json_match:
                json_str = json_match.group(0)
                debug(f"Regex fallback found potential JSON string: {json_str[:200]}...")
                try:
                    extracted_data = json.loads(json_str)
                    if not isinstance(extracted_data, list):
                        error("Regex fallback extracted content is not a list.")
                        return [] # Return empty on type error
                    success("Successfully parsed JSON array using regex fallback.") # Use success log level
                except json.JSONDecodeError as e_regex:
                    error(f"Error parsing JSON from regex fallback: {e_regex}")
                    error(f"Regex extracted string preview: {json_str[:500]}...")
                    return [] # Return empty on error
            else:
                error("No JSON array found using regex fallback either.")
                error(f"Full Gemini response text that failed parsing: {response.text}")
                return [] # Return empty on error

        if not isinstance(extracted_data, list):
            error(f"Final extracted data is not a JSON list after all attempts. Type: {type(extracted_data)}")
            return [] # Return empty if it's not a list

        success(f"Extracted {len(extracted_data)} records using Gemini.") # Use success log level
        return extracted_data

    except Exception as e: # General catch for other API errors or unexpected issues
        error(f"Error processing with Gemini: {e}")
        try:
            if response and response.prompt_feedback:
                warning(f"Gemini Prompt Feedback: {response.prompt_feedback}")
            if response and response.candidates and response.candidates[0].safety_ratings:
                warning(f"Gemini Safety Ratings: {response.candidates[0].safety_ratings}")
        except (NameError, AttributeError, IndexError):
            pass
        return [] # Return empty list on error