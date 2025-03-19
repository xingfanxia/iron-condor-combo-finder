"""Schwab API data source for options chains"""

import os
import datetime
from dotenv import load_dotenv

# Import Schwab client
try:
    from schwab import auth as schwab_auth, client as schwab_client
except ImportError:
    print("schwab-py not installed. Run: pip install schwab-py")
    
from .base import DataSourceBase

# Load environment variables
load_dotenv()


class SchwabDataSource(DataSourceBase):
    """Schwab API data source for options chains"""
    
    def __init__(self, symbol, min_dte, max_dte, min_liquidity):
        super().__init__(symbol, min_dte, max_dte, min_liquidity)
        self.api_key = os.getenv('SCHWAB_API_KEY')
        self.app_secret = os.getenv('SCHWAB_APP_SECRET')
        self.callback_url = os.getenv('SCHWAB_CALLBACK_URL', 'https://127.0.0.1:8182/')
        self.token_path = os.getenv('SCHWAB_TOKEN_PATH', 'schwab_token.json')
        self.client = self._init_client()
    
    def _init_client(self):
        """Initialize the Schwab client"""
        if not self.api_key or not self.app_secret:
            print("Warning: Schwab API key or app secret not found. Will attempt to use other data sources.")
            return None
            
        try:
            client = schwab_auth.easy_client(
                self.api_key,
                self.app_secret,
                self.callback_url,
                self.token_path
            )
            print("Schwab client initialized successfully")
            return client
        except Exception as e:
            print(f"Error initializing Schwab client: {e}")
            return None
    
    def get_current_price(self):
        """Get current price from Schwab API"""
        if not self.client:
            return super().get_current_price()
        
        try:
            # Get quotes for the symbol
            response = self.client.get_quotes(symbols=[self.symbol])
            if response.status_code == 200:
                quote_data = response.json()
                # Check if we got data for our symbol
                if self.symbol in quote_data:
                    self.current_price = quote_data[self.symbol]['lastPrice']
                    return self.current_price
        except Exception as e:
            print(f"Error getting price from Schwab API: {e}")
        
        # Fallback to Yahoo Finance API
        return super().get_current_price()
    
    def get_options_chain(self):
        """Fetch options chain from Schwab API"""
        if not self.client:
            raise ValueError("Schwab client not initialized. Please check your API credentials.")
            
        # Format dates for the API
        today = datetime.datetime.now()
        from_date = (today + datetime.timedelta(days=self.min_dte)).strftime('%Y-%m-%d')
        to_date = (today + datetime.timedelta(days=self.max_dte)).strftime('%Y-%m-%d')
        
        # Make sure we have current price
        if not self.current_price:
            self.get_current_price()
        
        try:
            # Fetch options chain from Schwab
            response = self.client.get_option_chain(
                symbol=self.symbol,
                contract_type='ALL',  # ALL, CALL, PUT
                from_date=from_date,
                to_date=to_date,
                strike_count=20,  # Number of strikes above and below current price
                include_quotes=True
            )
            
            if response.status_code != 200:
                raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
                
            options_data = response.json()
            
            # Transform the response to match our expected format if needed
            result = {
                'callExpDateMap': {},
                'putExpDateMap': {},
                'underlying': self.current_price
            }
            
            # Process calls and puts
            if 'callExpDateMap' in options_data:
                result['callExpDateMap'] = options_data['callExpDateMap']
            if 'putExpDateMap' in options_data:
                result['putExpDateMap'] = options_data['putExpDateMap']
                
            return result
        except Exception as e:
            print(f"Error accessing Schwab API: {e}")
            raise 