#!/usr/bin/env python

"""
Minimal test for Yahoo price fetching.
"""

import requests
import time

def get_current_price(symbol):
    """Get current price of the underlying asset with retry logic"""
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
            return None
    
    print(f"Failed after {max_retries} attempts")
    return None

def main():
    """Test Yahoo Finance price fetching"""
    print("Testing Yahoo Finance price fetching...")
    
    symbols = ['SPX', 'SPY', 'AAPL', 'MSFT', 'GOOG']
    
    for symbol in symbols:
        # Add a sleep between symbols to avoid rate limiting
        if symbol != symbols[0]:
            print(f"Waiting 1 second before fetching {symbol}...")
            time.sleep(1)
            
        price = get_current_price(symbol)
        if price:
            print(f"{symbol} price: ${price:.2f}")
        else:
            print(f"Error: Failed to get {symbol} price")
    
    print("\nTest completed!")

if __name__ == "__main__":
    main() 