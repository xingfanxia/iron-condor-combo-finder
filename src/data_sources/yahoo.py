"""Yahoo Finance data source for options chains"""

import datetime
import math
import requests

from .base import DataSourceBase


class YahooDataSource(DataSourceBase):
    """Yahoo Finance data source for options chains"""
    
    def __init__(self, symbol, min_dte, max_dte, min_liquidity):
        super().__init__(symbol, min_dte, max_dte, min_liquidity)
    
    def get_options_chain(self):
        """Get options data from Yahoo Finance API"""
        # Make sure we have current price
        if not self.current_price:
            self.get_current_price()
        
        if not self.current_price:
            raise ValueError("Could not determine current price")
        
        # First, get available expiration dates
        try:
            url = f"https://query1.finance.yahoo.com/v7/finance/options/{self.symbol}"
            response = requests.get(url)
            
            if response.status_code != 200:
                raise Exception(f"Yahoo API request failed with status code {response.status_code}")
                
            data = response.json()
            
            if 'optionChain' not in data or not data['optionChain']['result']:
                raise Exception("No options data returned from Yahoo Finance")
                
            expirations = data['optionChain']['result'][0]['expirationDates']
        except Exception as e:
            print(f"Error getting Yahoo options expiration data: {e}")
            return {'callExpDateMap': {}, 'putExpDateMap': {}, 'underlying': self.current_price}
        
        options_data = {
            'callExpDateMap': {},
            'putExpDateMap': {},
            'underlying': self.current_price
        }
        
        # Today's date
        today = datetime.datetime.now().date()
        
        # Filter for expirations within our DTE range
        valid_expirations = []
        for timestamp in expirations:
            exp_date = datetime.datetime.fromtimestamp(timestamp).date()
            dte = (exp_date - today).days
            
            if self.min_dte <= dte <= self.max_dte:
                valid_expirations.append(timestamp)
                
        # Get options data for each valid expiration
        for exp_timestamp in valid_expirations[:2]:  # Limit to first 2 expirations for demo
            try:
                exp_date = datetime.datetime.fromtimestamp(exp_timestamp).date()
                exp_str = exp_date.strftime('%Y-%m-%d')
                dte = (exp_date - today).days
                
                url = f"https://query1.finance.yahoo.com/v7/finance/options/{self.symbol}?date={exp_timestamp}"
                response = requests.get(url)
                
                if response.status_code != 200:
                    print(f"Error fetching Yahoo data for expiration {exp_str}: {response.status_code}")
                    continue
                    
                exp_data = response.json()
                
                if not exp_data.get('optionChain', {}).get('result', [{}])[0].get('options', [{}])[0]:
                    print(f"No options data available for expiration {exp_str}")
                    continue
                
                calls = exp_data['optionChain']['result'][0]['options'][0].get('calls', [])
                puts = exp_data['optionChain']['result'][0]['options'][0].get('puts', [])
                
                # Process calls
                options_data['callExpDateMap'][f"{exp_str}:"] = {}
                for call in calls:
                    strike = str(call['strike'])
                    
                    # Calculate estimated Greeks (Yahoo doesn't provide them)
                    # These are rough approximations
                    iv = call.get('impliedVolatility', 0.2)
                    strike_price = float(strike)
                    
                    # Calculate estimated delta (rough approximation)
                    moneyness = self.current_price / strike_price
                    estimated_delta = min(max(moneyness - 0.9, 0) * 5, 1)  # Very rough estimate
                    
                    # Estimate gamma (peak near ATM)
                    d1 = abs(self.current_price - strike_price) / (self.current_price * 0.2 * math.sqrt(dte/365))
                    estimated_gamma = math.exp(-0.5 * d1**2) * 0.02  # Very rough estimate
                    
                    # Estimate theta (roughly proportional to gamma * IV)
                    estimated_theta = -estimated_gamma * iv * 30  # Very rough estimate
                    
                    # Estimate vega (peak near ATM, proportional to days remaining)
                    estimated_vega = math.exp(-0.5 * d1**2) * math.sqrt(dte/365) * 10  # Very rough estimate
                    
                    # Create the same structure as Schwab API
                    option_data = [{
                        'bid': call.get('bid', 0),
                        'ask': call.get('ask', 0),
                        'delta': estimated_delta,
                        'gamma': estimated_gamma,
                        'theta': estimated_theta,
                        'vega': estimated_vega,
                        'totalVolume': call.get('volume', 0),
                        'openInterest': call.get('openInterest', 0),
                        'volatility': iv
                    }]
                    
                    options_data['callExpDateMap'][f"{exp_str}:"][strike] = option_data
                
                # Process puts
                options_data['putExpDateMap'][f"{exp_str}:"] = {}
                for put in puts:
                    strike = str(put['strike'])
                    
                    # Calculate estimated Greeks
                    iv = put.get('impliedVolatility', 0.2)
                    strike_price = float(strike)
                    
                    # Calculate estimated delta for puts (rough approximation)
                    moneyness = strike_price / self.current_price
                    estimated_delta = -min(max(moneyness - 0.9, 0) * 5, 1)  # Negative for puts
                    
                    # Estimate gamma (peak near ATM)
                    d1 = abs(self.current_price - strike_price) / (self.current_price * 0.2 * math.sqrt(dte/365))
                    estimated_gamma = math.exp(-0.5 * d1**2) * 0.02  # Very rough estimate
                    
                    # Estimate theta (roughly proportional to gamma * IV)
                    estimated_theta = -estimated_gamma * iv * 30  # Very rough estimate
                    
                    # Estimate vega (peak near ATM, proportional to days remaining)
                    estimated_vega = math.exp(-0.5 * d1**2) * math.sqrt(dte/365) * 10  # Very rough estimate
                    
                    # Create the same structure as Schwab API
                    option_data = [{
                        'bid': put.get('bid', 0),
                        'ask': put.get('ask', 0),
                        'delta': estimated_delta,
                        'gamma': estimated_gamma,
                        'theta': estimated_theta,
                        'vega': estimated_vega,
                        'totalVolume': put.get('volume', 0),
                        'openInterest': put.get('openInterest', 0),
                        'volatility': iv
                    }]
                    
                    options_data['putExpDateMap'][f"{exp_str}:"][strike] = option_data
            
            except Exception as e:
                print(f"Error processing Yahoo options data for expiration {exp_timestamp}: {e}")
                continue
        
        return options_data 