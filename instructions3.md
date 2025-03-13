# Step 3: Integration of Satellite Data ✅

This step focuses on incorporating alternative data from satellite imagery to enhance the trading signals. Satellite data (such as oil storage levels and tanker counts) can provide additional fundamental insights to help adjust risk parameters and signal confidence.

---

## 3.1. Develop the Satellite Data Module ✅

1. **Create the Module:** ✅
   - Create a new folder called `satellite` within the `agents/` directory.
   - Inside this folder, create a file named `satellite_data.py`.

2. **Install Required Packages:** ✅
   - Ensure you have the `requests` package installed (if not, add it to `requirements.txt`):
     ```bash
     pip install requests
     ```

3. **Define Data Fetching Functions:** ✅
   - In `satellite_data.py`, write functions that call your chosen satellite data provider's API and process the response.
   - **Example Code:**
     ```python
     import requests
     import logging

     # Configure logging
     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
     logger = logging.getLogger(__name__)

     def fetch_storage_levels(api_url="https://api.example.com/oil_storage"):
         """
         Fetches oil storage levels from a satellite data provider.
         
         Args:
             api_url (str): The API endpoint to fetch oil storage data.
         
         Returns:
             float: The current storage level as a percentage (or None if data is unavailable).
         """
         try:
             response = requests.get(api_url, timeout=10)
             response.raise_for_status()
             data = response.json()
             # Assume the API returns a JSON with a key 'storage_level'
             storage_level = data.get("storage_level")
             if storage_level is None:
                 logger.warning("Storage level not found in API response.")
             else:
                 logger.info(f"Fetched storage level: {storage_level}")
             return storage_level
         except Exception as e:
             logger.error(f"Error fetching storage levels: {e}")
             return None

     def fetch_tanker_counts(api_url="https://api.example.com/tanker_counts"):
         """
         Fetches the current number of oil tankers from a satellite data provider.
         
         Args:
             api_url (str): The API endpoint to fetch tanker counts.
         
         Returns:
             int: The number of tankers (or None if data is unavailable).
         """
         try:
             response = requests.get(api_url, timeout=10)
             response.raise_for_status()
             data = response.json()
             tanker_count = data.get("tanker_count")
             if tanker_count is None:
                 logger.warning("Tanker count not found in API response.")
             else:
                 logger.info(f"Fetched tanker count: {tanker_count}")
             return tanker_count
         except Exception as e:
             logger.error(f"Error fetching tanker counts: {e}")
             return None
     ```
4. **Document the Module:** ✅
   - At the top of `satellite_data.py`, include a header that explains:
     - The purpose of the module.
     - How the functions are intended to be used.
     - Any API keys or authentication that might be needed (ensure these are stored in the `.env` file).

---

## 3.2. Integrate Satellite Data into the Trading Strategy ✅

1. **Modify the Strategy Module:** ✅
   - Open `agents/strategy/strategy.py`.
   - Import the satellite data functions:
     ```python
     from agents.satellite.satellite_data import fetch_storage_levels, fetch_tanker_counts
     ```

2. **Enhance Signal Generation:** ✅
   - Within your `generate_signals` function, call the satellite data functions to retrieve current metrics.
   - Use the retrieved values to adjust the signal's confidence or risk parameters.
   - **Example Code Snippet:**
     ```python
     def generate_signals(data):
         signals = []
         # Fetch satellite metrics
         storage_level = fetch_storage_levels()
         tanker_count = fetch_tanker_counts()
         
         # Define thresholds (adjust based on your research)
         storage_threshold = 0.8  # For example, storage level > 80% may indicate oversupply
         
         for record in data:
             # Process each record to create a signal (using your existing logic)
             current_price = float(record.get("Close", 70.0))
             signal_type = "BUY"  # Simplified example; use your logic here
             
             # Calculate limit price
             if signal_type == "BUY":
                 limit_price = current_price * 0.995
             elif signal_type == "SELL":
                 limit_price = current_price * 1.005
             else:
                 limit_price = current_price
             
             # Adjust confidence based on satellite data
             base_confidence = 0.75
             if storage_level is not None and storage_level > storage_threshold:
                 adjusted_confidence = max(0, base_confidence - 0.1)
             else:
                 adjusted_confidence = base_confidence
             
             # Create the signal using your TradingSignal interface (example shown in Step 1)
             signal = {
                 'Date': record.get("Date"),
                 'Price': round(current_price, 2),
                 'Signal': 1 if signal_type == "BUY" else -1 if signal_type == "SELL" else 0,
                 'Confidence': adjusted_confidence,
                 'limit_price': round(limit_price, 2),
                 'satellite': {
                     'storage_level': storage_level,
                     'tanker_count': tanker_count
                 }
             }
             signals.append(signal)
         return signals
     ```
3. **Test and Validate:** ✅
   - Run your updated strategy module and verify that:
     - Satellite data is correctly fetched and logged.
     - Signals now include a `"satellite"` field with the corresponding metrics.
     - Confidence levels adjust appropriately based on the storage level.
   - Log outputs and inspect the generated signals to ensure correctness.

---

## 3.3. Testing and Documentation ✅

1. **Unit Tests:** ✅
   - Write unit tests for the functions in `satellite_data.py` to simulate API responses and error conditions.
   - Create test cases for `generate_signals` in `strategy.py` that include mocked satellite data.

2. **Documentation:** ✅
   - Update your project documentation (e.g., in `docs/` or `README.md`) to describe:
     - How satellite data is integrated.
     - The thresholds and logic used to adjust signals.
     - How to configure the satellite data API endpoints (e.g., in `config.json` or `.env`).

---

## Summary ✅

Step 3 aims to enrich your trading signals with alternative data from satellite sources. By creating a dedicated `satellite_data.py` module and integrating its outputs into your trading strategy, you gain an additional layer of insight into market fundamentals (like oil storage levels and tanker counts). This should ultimately improve the risk-adjusted return of your trading bot by providing early signals on supply-demand shifts.

Next, proceed to test these integrations thoroughly before moving on to the next step in our upgrade plan.

---

## Additional Enhancements Implemented: ✅

1. Created a comprehensive SatelliteData interface in agent_interfaces.py to standardize satellite data representation. ✅
2. Implemented a SatelliteDataAgent class in satellite_data.py that handles fetching and processing satellite imagery. ✅
3. Added support for multiple satellite data providers (Sentinel Hub, Planet Labs, Maxar) with fallback mechanisms. ✅
4. Implemented image processing functions to extract oil storage levels and count oil tankers from satellite imagery. ✅
5. Added configuration options in config.example.json for satellite data sources and API keys. ✅
6. Integrated satellite data into the agent_manager.py to coordinate with other agents. ✅
7. Created a database schema for storing historical satellite data for trend analysis. ✅
8. Added comprehensive logging for satellite data operations. ✅
9. Implemented error handling and retry mechanisms for API calls. ✅
10. Added unit tests for the satellite data module to ensure reliability. ✅
