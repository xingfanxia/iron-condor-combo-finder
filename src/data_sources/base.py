"""Base class for options data sources"""

import requests
import os


class DataSourceBase:
    """Base class for options data sources"""
    
    def __init__(self, symbol, min_dte, max_dte, min_liquidity):
        """Initialize the data source"""
        self.symbol = symbol
        self.min_dte = min_dte
        self.max_dte = max_dte
        self.min_liquidity = min_liquidity
        self.current_price = None
    
    def get_current_price(self):
        """Get current price of the underlying asset"""
        # Base implementation using Yahoo with retry logic
        try:
            # First attempt with Yahoo Finance
            for attempt in range(3):  # Try up to 3 times
                try:
                    if attempt > 0:
                        import time
                        time.sleep(2 * attempt)  # Exponential backoff: 0, 2, 4 seconds
                        
                    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{self.symbol}?interval=1d"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    response = requests.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        price = data['chart']['result'][0]['meta']['regularMarketPrice']
                        self.current_price = price
                        return price
                    elif response.status_code == 429:
                        print(f"Rate limited by Yahoo (attempt {attempt+1}/3), waiting before retry...")
                        continue
                    else:
                        print(f"Yahoo API request failed with status code {response.status_code}")
                        break  # Try alternative source
                except Exception as e:
                    print(f"Error in Yahoo price fetch attempt {attempt+1}: {e}")
            
            # Fall back to Alpha Vantage API if Yahoo fails
            try:
                print("Trying Alpha Vantage API as fallback...")
                # Note: You might need an API key from https://www.alphavantage.co/
                alpha_key = os.getenv('ALPHA_VANTAGE_KEY', 'demo')
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={self.symbol}&apikey={alpha_key}"
                response = requests.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'Global Quote' in data and '05. price' in data['Global Quote']:
                        price = float(data['Global Quote']['05. price'])
                        self.current_price = price
                        return price
                    else:
                        print(f"Unexpected Alpha Vantage response format: {data}")
            except Exception as e:
                print(f"Error with Alpha Vantage fallback: {e}")
            
            print("All price data sources failed")
            return None
            
        except Exception as e:
            print(f"Error getting current price: {e}")
            return None
    
    def get_option_chain(self):
        """Get options chain data - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement get_option_chain()") 