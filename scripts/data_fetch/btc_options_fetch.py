from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import random
# Assuming agent_interfaces.py is in the parent directory of 'scripts' or accessible in PYTHONPATH
# Adjust the import path as necessary based on your project structure.
# If 'scripts' is a package, and 'agent_interfaces.py' is at the root:
from agent_interfaces import OptionsContractData, OptionsChainData

def fetch_btc_options_data(api_key: str, symbol: str, expiries: List[str]) -> List[OptionsChainData]:
    """
    MOCK IMPLEMENTATION: Fetches BTC options data.
    In a real scenario, this function would connect to a live options data API.

    Args:
        api_key (str): The API key for the options data provider.
        symbol (str): The underlying symbol (e.g., "BTC").
        expiries (List[str]): List of expiries to fetch (e.g., ["1D", "7D"]). Not used in mock.

    Returns:
        List[OptionsChainData]: A list of OptionsChainData objects, one for each requested expiry.
    """
    print(f"Mock fetch for {symbol} options with API key: {api_key[:4]}... for expiries: {expiries}")
    
    options_chains = []
    base_spot_price = 60000.0  # Example spot price for BTC

    for i, expiry_str in enumerate(expiries): # Using monitored_expiries from config
        # Mocking expiry date calculation (e.g., 1D, 7D, 30D from now)
        # This is a simplified way to get days from strings like "1D", "7D"
        days_to_expiry = int(expiry_str[:-1]) if expiry_str[:-1].isdigit() and expiry_str.endswith('D') else (i + 1) * 7 
        expiry_date = datetime.now() + timedelta(days=days_to_expiry)
        
        mock_contracts = []
        num_strikes = 20  # Generate 10 calls and 10 puts
        
        for j in range(num_strikes):
            strike_price_call = base_spot_price * (1 + (j - num_strikes // 2 + 1) * 0.02) # Vary around spot
            strike_price_put = base_spot_price * (1 + (j - num_strikes // 2 + 1) * 0.02) # Vary around spot

            mock_contracts.append(
                OptionsContractData(
                    strike_price=round(strike_price_call, 2),
                    contract_type="call",
                    implied_volatility=random.uniform(0.5, 0.9), # IV between 50% and 90%
                    volume=random.randint(10, 500),
                    open_interest=random.randint(100, 2000),
                    delta=random.uniform(0.4, 0.6) if strike_price_call < base_spot_price else random.uniform(0.1, 0.4),
                    gamma=random.uniform(0.01, 0.05),
                    theta=random.uniform(-0.1, -0.05),
                    vega=random.uniform(0.1, 0.5),
                    last_traded_price=round(strike_price_call * 0.1 * random.uniform(0.5, 1.5), 2) # Mock price
                )
            )
            mock_contracts.append(
                OptionsContractData(
                    strike_price=round(strike_price_put, 2),
                    contract_type="put",
                    implied_volatility=random.uniform(0.5, 0.9),
                    volume=random.randint(10, 500),
                    open_interest=random.randint(100, 2000),
                    delta=random.uniform(-0.6, -0.4) if strike_price_put > base_spot_price else random.uniform(-0.4, -0.1),
                    gamma=random.uniform(0.01, 0.05),
                    theta=random.uniform(-0.1, -0.05),
                    vega=random.uniform(0.1, 0.5),
                    last_traded_price=round(strike_price_put * 0.1 * random.uniform(0.5, 1.5), 2)
                )
            )

        options_chains.append(
            OptionsChainData(
                underlying_symbol=symbol,
                spot_price=base_spot_price + random.uniform(-500, 500), # Add some variation
                expiry_date=expiry_date,
                contracts=mock_contracts,
            )
        )
    
    return options_chains

# Example usage (optional, for testing the script directly)
if __name__ == "__main__":
    mock_api_key = "test_key_123"
    btc_symbol = "BTC"
    example_expiries = ["1D", "7D", "30D"] # Example expiries
    
    options_data_list = fetch_btc_options_data(mock_api_key, btc_symbol, example_expiries)
    
    for options_data in options_data_list:
        print(f"\nFetched for {options_data.underlying_symbol} (Spot: ${options_data.spot_price:.2f}) for expiry {options_data.expiry_date.strftime('%Y-%m-%d')}:")
        print(f"  Number of contracts: {len(options_data.contracts)}")
        if options_data.contracts:
            sample_contract = options_data.contracts[0]
            print(f"  Sample contract (Call): Strike ${sample_contract.strike_price:.2f}, IV {sample_contract.implied_volatility:.2f}")
