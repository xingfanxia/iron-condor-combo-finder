"""Yahoo Finance data source for options chains"""

import datetime
import math
import requests

from .base import DataSourceBase


class YahooDataSource(DataSourceBase):
    """Yahoo Finance data source for options chains"""
    
    def __init__(self, symbol, min_dte, max_dte, min_liquidity):
        super().__init__(symbol, min_dte, max_dte, min_liquidity)
    
    def get_option_chain(self):
        """Get options data from Yahoo Finance API"""
        try:
            import yfinance as yf
            
            stock = yf.Ticker(self.symbol)
            expirations = stock.options
            
            if not expirations:
                print(f"No options expirations found for {self.symbol}")
                return None
                
            # Get current price if not set
            if not self.current_price:
                self.current_price = self.get_current_price()
                
            # Process all expiration dates that fall within our DTE criteria
            calls_data = {}
            puts_data = {}
            
            for expiration in expirations:
                # Convert to datetime to calculate DTE
                exp_date = datetime.datetime.strptime(expiration, "%Y-%m-%d").date()
                today = datetime.datetime.now().date()
                dte = (exp_date - today).days
                
                # Check if this expiration is within our min/max DTE range
                if (self.min_dte is not None and dte < self.min_dte) or \
                   (self.max_dte is not None and dte > self.max_dte):
                    continue
                
                # Fetch option chain for this expiration
                try:
                    chain = stock.option_chain(expiration)
                    
                    if not hasattr(chain, 'calls') or not hasattr(chain, 'puts'):
                        continue
                        
                    # Process calls
                    for i, option in chain.calls.iterrows():
                        strike = option.strike
                        
                        # Format in the TDA API style for compatibility
                        option_key = f"{expiration}:{dte}"
                        
                        if option_key not in calls_data:
                            calls_data[option_key] = {}
                        
                        if str(strike) not in calls_data[option_key]:
                            calls_data[option_key][str(strike)] = []
                        
                        option_data = {
                            'putCall': 'CALL',
                            'symbol': f"{self.symbol}_{expiration}_C_{strike}",
                            'description': f"{self.symbol} {expiration} CALL {strike}",
                            'bid': option.bid,
                            'ask': option.ask,
                            'last': option.lastPrice,
                            'mark': (option.bid + option.ask) / 2 if option.bid and option.ask else option.lastPrice,
                            'delta': option.delta if hasattr(option, 'delta') else None,
                            'gamma': option.gamma if hasattr(option, 'gamma') else None,
                            'theta': option.theta if hasattr(option, 'theta') else None,
                            'vega': option.vega if hasattr(option, 'vega') else None,
                            'openInterest': option.openInterest,
                            'totalVolume': option.volume,
                            'inTheMoney': option.inTheMoney if hasattr(option, 'inTheMoney') else (self.current_price > strike)
                        }
                        
                        calls_data[option_key][str(strike)].append(option_data)
                    
                    # Process puts
                    for i, option in chain.puts.iterrows():
                        strike = option.strike
                        
                        # Format in the TDA API style for compatibility
                        option_key = f"{expiration}:{dte}"
                        
                        if option_key not in puts_data:
                            puts_data[option_key] = {}
                        
                        if str(strike) not in puts_data[option_key]:
                            puts_data[option_key][str(strike)] = []
                        
                        option_data = {
                            'putCall': 'PUT',
                            'symbol': f"{self.symbol}_{expiration}_P_{strike}",
                            'description': f"{self.symbol} {expiration} PUT {strike}",
                            'bid': option.bid,
                            'ask': option.ask,
                            'last': option.lastPrice,
                            'mark': (option.bid + option.ask) / 2 if option.bid and option.ask else option.lastPrice,
                            'delta': option.delta if hasattr(option, 'delta') else None,
                            'gamma': option.gamma if hasattr(option, 'gamma') else None,
                            'theta': option.theta if hasattr(option, 'theta') else None,
                            'vega': option.vega if hasattr(option, 'vega') else None,
                            'openInterest': option.openInterest,
                            'totalVolume': option.volume,
                            'inTheMoney': option.inTheMoney if hasattr(option, 'inTheMoney') else (self.current_price < strike)
                        }
                        
                        puts_data[option_key][str(strike)].append(option_data)
                        
                except Exception as e:
                    print(f"Error processing expiration {expiration}: {e}")
                    continue
            
            return {
                'callExpDateMap': calls_data,
                'putExpDateMap': puts_data,
                'underlying': self.current_price
            }
            
        except ImportError:
            print("yfinance not installed. Please install with: pip install yfinance")
            return None
        except Exception as e:
            print(f"Error fetching options data from Yahoo Finance: {e}")
            return None 