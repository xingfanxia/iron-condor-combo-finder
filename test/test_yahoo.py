#!/usr/bin/env python

"""
Simple test script for Yahoo Finance data source.
"""

import datetime
import pandas as pd
import time
import requests
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_sources.yahoo import YahooDataSource

# Add a patched version of get_current_price with retry logic
def get_current_price_with_retry(symbol):
    """Get current price with retry logic for rate limiting"""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d"
            response = requests.get(url)
            
            if response.status_code == 429:
                print(f"Rate limited (attempt {attempt+1}/{max_retries}), waiting {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
                
            if response.status_code != 200:
                print(f"Error fetching price data: {response.status_code}")
                return None
                
            data = response.json()
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            return price
        except Exception as e:
            print(f"Error getting current price: {e}")
            
    print(f"Failed after {max_retries} attempts")
    return None

# Patch the YahooDataSource class to use our retry method
# This is a bit of a hack, but it's just for testing
YahooDataSource.get_current_price = lambda self: get_current_price_with_retry(self.symbol)

def main():
    """Test Yahoo Finance data source"""
    print("Testing Yahoo Finance data source...")
    
    # Create Yahoo data source for SPX
    datasource = YahooDataSource(
        symbol='SPX', 
        min_dte=1,  
        max_dte=30, 
        min_liquidity=10
    )
    
    # Get current price
    price = datasource.get_current_price()
    if price:
        print(f"Current SPX price: ${price:.2f}")
    else:
        print("Error: Failed to get current price")
        return
    
    # Get options chain - wait a moment to avoid rate limiting
    print("\nWaiting 2 seconds before fetching options data...")
    time.sleep(2)
    
    print("Fetching options data...")
    options_data = datasource.get_options_chain()
    
    # Check if options data was returned
    if not options_data or not options_data.get('callExpDateMap') or not options_data.get('putExpDateMap'):
        print("Error: No options data returned")
        return
    
    # Print summary of expiry dates
    print("\nAvailable expirations:")
    call_expiries = options_data['callExpDateMap'].keys()
    for i, expiry in enumerate(call_expiries):
        print(f"  {i+1}. {expiry.split(':')[0]}")
    
    # Select first expiration for detailed analysis
    if call_expiries:
        first_expiry = list(call_expiries)[0]
        print(f"\nDetailed analysis for {first_expiry.split(':')[0]}:")
        
        # Count calls and puts
        call_strikes = options_data['callExpDateMap'][first_expiry].keys()
        put_strikes = options_data['putExpDateMap'][first_expiry].keys()
        print(f"  Calls: {len(call_strikes)} strikes")
        print(f"  Puts: {len(put_strikes)} strikes")
        
        # Show some sample calls
        print("\nSample calls:")
        for i, strike in enumerate(list(call_strikes)[:3]):
            call = options_data['callExpDateMap'][first_expiry][strike][0]
            print(f"  Strike ${strike}: Bid ${call.get('bid', 0):.2f}, Ask ${call.get('ask', 0):.2f}, Volume {call.get('totalVolume', 0)}")
        
        # Show some sample puts
        print("\nSample puts:")
        for i, strike in enumerate(list(put_strikes)[:3]):
            put = options_data['putExpDateMap'][first_expiry][strike][0]
            print(f"  Strike ${strike}: Bid ${put.get('bid', 0):.2f}, Ask ${put.get('ask', 0):.2f}, Volume {put.get('totalVolume', 0)}")
    
    print("\nYahoo Finance data source test completed successfully!")

if __name__ == "__main__":
    main() 