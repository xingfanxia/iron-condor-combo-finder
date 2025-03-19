#!/usr/bin/env python3
"""
Test script for Interactive Brokers Data Source
"""

from src.data_sources import IBDataSource

def main():
    # Create IBDataSource for SPX
    ib_source = IBDataSource(
        symbol='SPX',
        min_dte=1,
        max_dte=5,
        min_liquidity=10
    )
    
    try:
        # Get current price
        price = ib_source.get_current_price()
        print(f"Current price for SPX: ${price:.2f}")
        
        # Get options chain
        print("Fetching options chain...")
        options_data = ib_source.get_options_chain()
        
        # Print summary of options data
        if options_data:
            call_expirations = options_data['callExpDateMap'].keys()
            put_expirations = options_data['putExpDateMap'].keys()
            
            print(f"Found {len(call_expirations)} call expirations:")
            for exp in call_expirations:
                strikes = options_data['callExpDateMap'][exp]
                print(f"  - {exp}: {len(strikes)} strikes")
            
            print(f"Found {len(put_expirations)} put expirations:")
            for exp in put_expirations:
                strikes = options_data['putExpDateMap'][exp]
                print(f"  - {exp}: {len(strikes)} strikes")
            
            # Sample some data for analysis
            if call_expirations:
                first_exp = list(call_expirations)[0]
                first_strikes = list(options_data['callExpDateMap'][first_exp].keys())
                
                if first_strikes:
                    sample_strike = first_strikes[0]
                    sample_call = options_data['callExpDateMap'][first_exp][sample_strike][0]
                    
                    print("\nSample call option:")
                    print(f"Expiration: {first_exp}")
                    print(f"Strike: {sample_strike}")
                    print(f"Bid/Ask: ${sample_call['bid']:.2f}/${sample_call['ask']:.2f}")
                    print(f"Delta: {sample_call['delta']:.4f}")
                    print(f"Gamma: {sample_call['gamma']:.4f}")
                    print(f"Theta: {sample_call['theta']:.4f}")
                    print(f"Vega: {sample_call['vega']:.4f}")
                    print(f"Implied Volatility: {sample_call['volatility']:.4f}")
        else:
            print("No options data returned")
            
    except Exception as e:
        print(f"Error testing IBDataSource: {e}")

if __name__ == "__main__":
    main() 