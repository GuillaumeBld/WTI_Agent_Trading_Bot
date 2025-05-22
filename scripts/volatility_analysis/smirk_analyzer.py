from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import numpy as np # For safe calculation of mean, handles empty lists by returning NaN

# Adjust import path based on project structure.
# If 'scripts' is a package and 'agent_interfaces.py' is at the root:
from agent_interfaces import OptionsChainData, VolatilitySmirkResult, OptionsContractData

# If the above import fails, it might need to be:
# from ..agent_interfaces import OptionsChainData, VolatilitySmirkResult, OptionsContractData
# Or sys.path manipulation if scripts/volatility_analysis is run as a standalone script context.

class SmirkAnalyzer:
    def analyze_smirk(self, options_data: OptionsChainData, config: Optional[Dict[str, Any]] = None) -> VolatilitySmirkResult:
        """
        Analyzes volatility smirk from options chain data using a basic calculation.

        Args:
            options_data (OptionsChainData): The input options chain data.
            config (Optional[Dict[str, Any]]): Configuration for smirk analysis 
                                               (e.g., thresholds from volatility_analysis section).

        Returns:
            VolatilitySmirkResult: The result of the smirk analysis.
        """
        logger_msg_prefix = f"Smirk analysis for {options_data.underlying_symbol} expiry {options_data.expiry_date.strftime('%Y-%m-%d')}:"
        print(f"{logger_msg_prefix} Starting analysis.")

        otm_call_ivs = []
        otm_put_ivs = []
        atm_threshold_percent = 0.02 # Consider contracts within 2% of spot as ATM
        
        spot_price = options_data.spot_price

        for contract in options_data.contracts:
            if contract.implied_volatility is None or contract.implied_volatility <= 0:
                continue # Skip contracts with no valid IV

            # Determine moneyness
            # OTM Call: strike > spot * (1 + atm_threshold_percent)
            if contract.contract_type == "call" and contract.strike_price > spot_price * (1 + atm_threshold_percent):
                otm_call_ivs.append(contract.implied_volatility)
            # OTM Put: strike < spot * (1 - atm_threshold_percent)
            elif contract.contract_type == "put" and contract.strike_price < spot_price * (1 - atm_threshold_percent):
                otm_put_ivs.append(contract.implied_volatility)

        avg_otm_call_iv = np.mean(otm_call_ivs) if otm_call_ivs else np.nan
        avg_otm_put_iv = np.mean(otm_put_ivs) if otm_put_ivs else np.nan

        skew_metric = np.nan
        if not np.isnan(avg_otm_call_iv) and not np.isnan(avg_otm_put_iv):
            skew_metric = avg_otm_call_iv - avg_otm_put_iv # Simple difference
        elif not np.isnan(avg_otm_call_iv): # Only calls have valid IVs
            skew_metric = 0.1 # Default to slightly positive if only OTM calls are significant (arbitrary)
        elif not np.isnan(avg_otm_put_iv): # Only puts have valid IVs
            skew_metric = -0.1 # Default to slightly negative if only OTM puts are significant (arbitrary)


        # Default sentiment and confidence
        sentiment_label = "neutral"
        calculated_confidence = 0.5 # Base confidence for neutral

        # Use thresholds from config if available
        if config:
            thresholds = config.get('volatility_analysis', {}).get('smirk_interpretation_thresholds', {})
            bullish_threshold = thresholds.get('bullish_skew_diff', 0.02) # e.g. OTM Call IVs 2% > OTM Put IVs
            bearish_threshold = thresholds.get('bearish_skew_diff', -0.02) # e.g. OTM Put IVs 2% > OTM Call IVs
            min_confidence_threshold = thresholds.get('min_confidence', 0.6)
            
            if not np.isnan(skew_metric):
                if skew_metric > bullish_threshold:
                    sentiment_label = "bullish"
                    # Scale confidence by how much it exceeds threshold, up to 0.95
                    calculated_confidence = min(0.95, min_confidence_threshold + (skew_metric - bullish_threshold) * 2) 
                elif skew_metric < bearish_threshold:
                    sentiment_label = "bearish"
                    # Scale confidence similarly for bearish
                    calculated_confidence = min(0.95, min_confidence_threshold + abs(skew_metric - bearish_threshold) * 2)
                else: # Between bullish and bearish thresholds
                    sentiment_label = "neutral"
                    calculated_confidence = min_confidence_threshold - 0.1 # Slightly less than min_confidence for clear signals
            else: # Skew metric is NaN (e.g. no OTM options on one or both sides)
                sentiment_label = "neutral"
                calculated_confidence = 0.4 # Lower confidence if data is insufficient
        else: # No config provided, use some defaults (though config should always be passed from AgentManager)
            if not np.isnan(skew_metric):
                if skew_metric > 0.02: sentiment_label = "bullish"; calculated_confidence = 0.65
                elif skew_metric < -0.02: sentiment_label = "bearish"; calculated_confidence = 0.65
        
        print(f"{logger_msg_prefix} OTM Call IVs ({len(otm_call_ivs)}): {avg_otm_call_iv:.4f if not np.isnan(avg_otm_call_iv) else 'N/A'}. " +
              f"OTM Put IVs ({len(otm_put_ivs)}): {avg_otm_put_iv:.4f if not np.isnan(avg_otm_put_iv) else 'N/A'}. " +
              f"Skew: {skew_metric:.4f if not np.isnan(skew_metric) else 'N/A'}. Sentiment: {sentiment_label} ({calculated_confidence:.2f})")

        return VolatilitySmirkResult(
            date=datetime.now(),
            underlying_symbol=options_data.underlying_symbol,
            expiry_date=options_data.expiry_date,
            skewness_metric=skew_metric if not np.isnan(skew_metric) else None, # Store None if NaN
            sentiment_label=sentiment_label,
            confidence=round(calculated_confidence, 2),
            details={
                "message": "Smirk analysis complete.",
                "spot_price_at_analysis": spot_price,
                "avg_otm_call_iv": avg_otm_call_iv if not np.isnan(avg_otm_call_iv) else None,
                "avg_otm_put_iv": avg_otm_put_iv if not np.isnan(avg_otm_put_iv) else None,
                "num_otm_calls": len(otm_call_ivs),
                "num_otm_puts": len(otm_put_ivs)
            }
        )

# Example usage (optional, for testing the script directly)
if __name__ == "__main__":
    analyzer = SmirkAnalyzer()

    # Create mock OptionsChainData for testing
    mock_contracts = [
        OptionsContractData(strike_price=60000, contract_type="call", implied_volatility=0.7, volume=100, open_interest=500, delta=0.5, gamma=0.02, theta=-0.05, vega=0.2, last_traded_price=3000),
        OptionsContractData(strike_price=61000, contract_type="call", implied_volatility=0.68, volume=120, open_interest=550, delta=0.4, gamma=0.02, theta=-0.05, vega=0.2, last_traded_price=2500),
        OptionsContractData(strike_price=59000, contract_type="put", implied_volatility=0.72, volume=90, open_interest=450, delta=-0.5, gamma=0.02, theta=-0.05, vega=0.2, last_traded_price=2800),
        OptionsContractData(strike_price=58000, contract_type="put", implied_volatility=0.75, volume=110, open_interest=480, delta=-0.6, gamma=0.02, theta=-0.05, vega=0.2, last_traded_price=3200),
    ]
    
    mock_options_chain = OptionsChainData(
        underlying_symbol="BTC",
        spot_price=60500.00,
        expiry_date=datetime.now() + timedelta(days=7),
        contracts=mock_contracts
    )
    
    # Mock config for testing thresholds
    mock_config_params = {
        "smirk_interpretation_thresholds": {
            "bullish_skew_diff": 0.05, 
            "bearish_skew_diff": -0.05,
            "min_confidence": 0.65
        }
    }

    result = analyzer.analyze_smirk(mock_options_chain, config=mock_config_params)
    
    print(f"Volatility Smirk Analysis Result for {result.underlying_symbol} (Expiry: {result.expiry_date.strftime('%Y-%m-%d')}):")
    print(f"  Sentiment: {result.sentiment_label} (Confidence: {result.confidence:.2f})")
    print(f"  Skewness Metric: {result.skewness_metric:.4f}")
    print(f"  Details: {result.details}")

    # Test with no config
    result_no_config = analyzer.analyze_smirk(mock_options_chain)
    print(f"\nResult without config for {result_no_config.underlying_symbol}:")
    print(f"  Sentiment: {result_no_config.sentiment_label} (Confidence: {result_no_config.confidence:.2f})")
