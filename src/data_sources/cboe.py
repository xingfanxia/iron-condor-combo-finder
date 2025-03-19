"""CBOE data source for options chains"""

import os
import datetime
import requests
from dotenv import load_dotenv

from .base import DataSourceBase

# Load environment variables
load_dotenv()


class CBOEDataSource(DataSourceBase):
    """CBOE data source for options chains"""
    
    def __init__(self, symbol, min_dte, max_dte, min_liquidity):
        super().__init__(symbol, min_dte, max_dte, min_liquidity)
        self.api_key = os.getenv('CBOE_API_KEY')
    
    def get_options_chain(self):
        """Fetch options chain from CBOE Options Data API"""
        if not self.api_key:
            raise ValueError("CBOE API key not found. Please set it in your .env file.")
            
        # CBOE API endpoint for options
        url = "https://www.cboe.com/options-data/api/quotedata"
        
        # Today's date
        today = datetime.datetime.now().date()
        
        # Filter for valid expiration dates within our DTE range
        valid_expirations = []
        for days in range(self.min_dte, self.max_dte + 1):
            exp_date = today + datetime.timedelta(days=days)
            valid_expirations.append(exp_date.strftime('%Y-%m-%d'))
        
        # Make sure we have current price
        if not self.current_price:
            self.get_current_price()
            
        if not self.current_price:
            raise ValueError("Could not determine current price for strike range")
            
        # Range for strikes (e.g., 10% around current price)
        lower_bound = self.current_price * 0.9
        upper_bound = self.current_price * 1.1
        
        options_data = {
            'callExpDateMap': {},
            'putExpDateMap': {},
            'underlying': self.current_price
        }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # For each expiration, get call and put data
        for exp_date in valid_expirations:
            exp_key = f"{exp_date}:"
            options_data['callExpDateMap'][exp_key] = {}
            options_data['putExpDateMap'][exp_key] = {}
            
            try:
                # Fetch calls
                call_params = {
                    'symbol': self.symbol,
                    'optionType': 'C',
                    'expirationDate': exp_date,
                }
                
                call_response = requests.get(url, headers=headers, params=call_params)
                if call_response.status_code == 200:
                    calls = call_response.json()
                    for call in calls:
                        if lower_bound <= call['strike'] <= upper_bound:
                            strike_key = str(call['strike'])
                            option_data = [{
                                'bid': call.get('bid', 0),
                                'ask': call.get('ask', 0),
                                'delta': call.get('delta', 0.5),
                                'gamma': call.get('gamma', 0.01),
                                'theta': call.get('theta', -0.01),
                                'vega': call.get('vega', 0.1),
                                'totalVolume': call.get('volume', 0),
                                'openInterest': call.get('openInterest', 0),
                                'volatility': call.get('impliedVolatility', 0.2)
                            }]
                            options_data['callExpDateMap'][exp_key][strike_key] = option_data
                
                # Fetch puts
                put_params = {
                    'symbol': self.symbol,
                    'optionType': 'P',
                    'expirationDate': exp_date,
                }
                
                put_response = requests.get(url, headers=headers, params=put_params)
                if put_response.status_code == 200:
                    puts = put_response.json()
                    for put in puts:
                        if lower_bound <= put['strike'] <= upper_bound:
                            strike_key = str(put['strike'])
                            option_data = [{
                                'bid': put.get('bid', 0),
                                'ask': put.get('ask', 0),
                                'delta': -put.get('delta', 0.5),  # Negative for puts
                                'gamma': put.get('gamma', 0.01),
                                'theta': put.get('theta', -0.01),
                                'vega': put.get('vega', 0.1),
                                'totalVolume': put.get('volume', 0),
                                'openInterest': put.get('openInterest', 0),
                                'volatility': put.get('impliedVolatility', 0.2)
                            }]
                            options_data['putExpDateMap'][exp_key][strike_key] = option_data
            
            except Exception as e:
                print(f"Error fetching CBOE data for {exp_date}: {e}")
                # Continue with next expiration
        
        return options_data 