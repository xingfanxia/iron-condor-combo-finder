"""Base class for options data sources"""

import requests


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
        # Base implementation using Yahoo
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{self.symbol}?interval=1d"
            response = requests.get(url)
            
            if response.status_code != 200:
                print(f"Error fetching price data: {response.status_code}")
                return None
                
            data = response.json()
            self.current_price = data['chart']['result'][0]['meta']['regularMarketPrice']
            return self.current_price
        except Exception as e:
            print(f"Error getting current price: {e}")
            return None
    
    def get_options_chain(self):
        """Get options chain data - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement get_options_chain()") 