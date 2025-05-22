from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import random # Keep for minor variations if needed, but primary data is structured
import json # For handling JSON-like structures

# Assuming agent_interfaces.py is in the parent directory of 'scripts' or accessible in PYTHONPATH
# Adjust the import path as necessary based on your project structure.
# If 'scripts' is a package, and 'agent_interfaces.py' is at the root:
from agent_interfaces import OptionsContractData, OptionsChainData

def fetch_btc_options_data(api_key: str, symbol: str, expiries: List[str]) -> List[OptionsChainData]:
    """
    MOCK IMPLEMENTATION: Simulates fetching BTC options data from a Refinitiv-like API.

    Args:
        api_key (str): The API key for the options data provider. (Not used in mock)
        symbol (str): The underlying symbol (e.g., "BTC").
        expiries (List[str]): List of expiries to fetch (e.g., ["1D", "7D", "30D"]).

    Returns:
        List[OptionsChainData]: A list of OptionsChainData objects, one for each requested expiry.
    """
    print(f"Mock Refinitiv API fetch for {symbol} options with API key: {api_key[:4]}... for expiries: {expiries}")
    
    all_chains_data = []
    base_spot_price = 62500.75  # Consistent base spot price

    for i, expiry_duration_str in enumerate(expiries):
        # Calculate expiry_date based on duration string (e.g., "1D", "7D", "30D")
        try:
            days_to_expiry = int(expiry_duration_str[:-1])
            if expiry_duration_str[-1].upper() == 'D':
                pass # days_to_expiry is correct
            elif expiry_duration_str[-1].upper() == 'M':
                days_to_expiry *= 30 # Approximate months
            elif expiry_duration_str[-1].upper() == 'Y':
                days_to_expiry *= 365 # Approximate years
            else: # Default to weeks if unit is unknown
                days_to_expiry = (i + 1) * 7 
        except ValueError:
            days_to_expiry = (i + 1) * 7 # Fallback for malformed string
            
        expiry_date = datetime.now() + timedelta(days=days_to_expiry)
        expiry_date_str = expiry_date.strftime("%Y-%m-%d")

        # Simulate the plausible Refinitiv API JSON Response for this expiry
        mock_api_response = {
            "underlyingSymbol": symbol, # Should be BTC-USD based on typical usage
            "spotPrice": base_spot_price + random.uniform(-100, 100), # Slight variation around base
            "expiryDate": expiry_date_str,
            "lastUpdated": (datetime.now() - timedelta(minutes=random.randint(1,5))).isoformat() + "Z",
            "optionChain": [] # This will be populated
        }

        # Populate the optionChain with some sample strikes around the spot price
        strike_multipliers = [-0.10, -0.05, 0, 0.05, 0.10] # % deviation from spot
        for mult in strike_multipliers:
            strike = round(base_spot_price * (1 + mult) / 500) * 500 # Rounded to nearest 500

            # Add a call contract
            mock_api_response["optionChain"].append({
                "strikePrice": strike,
                "optionType": "call",
                "impliedVolatility": random.uniform(0.55, 0.85),
                "volume": random.randint(50, 250),
                "openInterest": random.randint(200, 1500),
                "delta": random.uniform(0.3, 0.7) if strike < base_spot_price else random.uniform(0.1, 0.4),
                "gamma": random.uniform(0.0003, 0.0006),
                "theta": random.uniform(-8.0, -4.0),
                "vega": random.uniform(30.0, 60.0),
                "lastTrade": { "price": round(max(0, (base_spot_price - strike if strike < base_spot_price else 0) + random.uniform(50,500)),2), "timestamp": (datetime.now() - timedelta(minutes=random.randint(1,10))).isoformat()+"Z"}
            })
            # Add a put contract
            mock_api_response["optionChain"].append({
                "strikePrice": strike,
                "optionType": "put",
                "impliedVolatility": random.uniform(0.60, 0.90), # Puts might have higher IV in some skews
                "volume": random.randint(40, 200),
                "openInterest": random.randint(180, 1400),
                "delta": random.uniform(-0.7, -0.3) if strike > base_spot_price else random.uniform(-0.4, -0.1),
                "gamma": random.uniform(0.0003, 0.0006),
                "theta": random.uniform(-8.0, -4.0),
                "vega": random.uniform(30.0, 60.0),
                "lastTrade": { "price": round(max(0, (strike - base_spot_price if strike > base_spot_price else 0) + random.uniform(50,500)),2), "timestamp": (datetime.now() - timedelta(minutes=random.randint(1,10))).isoformat()+"Z"}
            })
        
        # Now, parse this mock_api_response into Pydantic models
        parsed_contracts = []
        for contract_data in mock_api_response["optionChain"]:
            parsed_contracts.append(
                OptionsContractData(
                    strike_price=contract_data["strikePrice"],
                    contract_type=contract_data["optionType"],
                    implied_volatility=contract_data["impliedVolatility"],
                    volume=contract_data["volume"],
                    open_interest=contract_data["openInterest"],
                    delta=contract_data["delta"],
                    gamma=contract_data["gamma"],
                    theta=contract_data["theta"],
                    vega=contract_data["vega"],
                    last_traded_price=contract_data["lastTrade"]["price"]
                )
            )
        
        # Ensure underlying_symbol in OptionsChainData matches the input 'symbol' argument (e.g. "BTC")
        # The mock_api_response uses "underlyingSymbol": symbol, which is fine.
        # However, the Pydantic model OptionsChainData has `underlying_symbol`, so we should use that.
        # The API response might have "BTC-USD", while our internal symbol might be "BTC".
        # For now, let's assume `symbol` is what we want in `OptionsChainData.underlying_symbol`.
        
        chain_for_expiry = OptionsChainData(
            underlying_symbol=symbol, # Use the function argument 'symbol'
            spot_price=mock_api_response["spotPrice"],
            expiry_date=datetime.strptime(mock_api_response["expiryDate"], "%Y-%m-%d"),
            contracts=parsed_contracts
        )
        all_chains_data.append(chain_for_expiry)
        
    return all_chains_data

# Example usage (optional, for testing the script directly)
if __name__ == "__main__":
    mock_api_key = "test_key_123"
    # The 'symbol' argument to fetch_btc_options_data should be the underlying, e.g., "BTC"
    # if your OptionsChainData.underlying_symbol is meant to be "BTC".
    # If it's meant to be "BTC-USD", then use that here.
    # Based on the new function, it seems 'symbol' is directly used for OptionsChainData.underlying_symbol.
    btc_symbol_arg = "BTC" # This will be the underlying_symbol in the returned Pydantic model.
    
    example_expiries = ["1D", "7D", "30D"] 
    
    options_data_list = fetch_btc_options_data(mock_api_key, btc_symbol_arg, example_expiries)
    
    for options_data in options_data_list:
        print(f"\nFetched for {options_data.underlying_symbol} (Spot: ${options_data.spot_price:.2f}) for expiry {options_data.expiry_date.strftime('%Y-%m-%d')}:")
        print(f"  Number of contracts: {len(options_data.contracts)}")
        if options_data.contracts:
            # Print details of the first call and first put contract if available
            first_call = next((c for c in options_data.contracts if c.contract_type == "call"), None)
            first_put = next((c for c in options_data.contracts if c.contract_type == "put"), None)
            
            if first_call:
                print(f"  Sample Call: Strike ${first_call.strike_price:.2f}, IV {first_call.implied_volatility:.2f}, Last Price ${first_call.last_traded_price:.2f}")
            if first_put:
                print(f"  Sample Put: Strike ${first_put.strike_price:.2f}, IV {first_put.implied_volatility:.2f}, Last Price ${first_put.last_traded_price:.2f}")
        else:
            print("  No contracts found in this chain.")
