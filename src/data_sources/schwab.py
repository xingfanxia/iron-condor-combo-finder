"""Schwab API data source for options chains"""

import os
import datetime
import json
import pprint
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
            print("Schwab client not initialized, falling back to base implementation")
            return super().get_current_price()
        
        try:
            # Get quotes for the symbol
            try:
                quote_response = self.client.get_quotes(symbols=[self.symbol])
                
                # Check for HTTP errors
                if hasattr(quote_response, 'status_code'):
                    if quote_response.status_code == 429:
                        print(f"⚠️ SCHWAB API RATE LIMIT EXCEEDED (429): Too many requests for quotes")
                        return super().get_current_price()
                    elif quote_response.status_code != 200:
                        print(f"⚠️ SCHWAB API ERROR ({quote_response.status_code}): Failed to get quote for {self.symbol}")
                        return super().get_current_price()
                
                quote_data = quote_response.json()
                
                # Check for API errors in response
                if 'errors' in quote_data:
                    print(f"⚠️ SCHWAB API ERROR: {quote_data['errors']}")
                    return super().get_current_price()
                
                # Check if we got data for our symbol
                if self.symbol in quote_data and 'quote' in quote_data[self.symbol] and 'lastPrice' in quote_data[self.symbol]['quote']:
                    return float(quote_data[self.symbol]['quote']['lastPrice'])
                else:
                    print(f"⚠️ SCHWAB API ERROR: No price data found for {self.symbol}")
                    if self.symbol in quote_data:
                        print(f"Available fields: {list(quote_data[self.symbol].keys())}")
                    return super().get_current_price()
            except Exception as e:
                print(f"⚠️ SCHWAB API ERROR while getting price: {str(e)}")
                return super().get_current_price()
        except Exception as e:
            print(f"⚠️ SCHWAB API ERROR: {str(e)}")
            return super().get_current_price()
    
    def _print_option_summary(self, options_data):
        """Helper to print a summary of the option chain data for debugging"""
        if not options_data:
            print("No options data to summarize")
            return
            
        print("\n🔍 OPTIONS DATA SUMMARY:")
        
        # Check call options
        if 'callExpDateMap' in options_data and options_data['callExpDateMap']:
            call_expirations = list(options_data['callExpDateMap'].keys())
            print(f"- Call options: {len(call_expirations)} expiration dates")
            
            # Show details for the first expiration
            if call_expirations:
                first_exp = call_expirations[0]
                strikes = list(options_data['callExpDateMap'][first_exp].keys())
                print(f"  Sample expiration {first_exp}:")
                print(f"  - {len(strikes)} strikes available: " + 
                      f"{', '.join(strikes[:5])}..." if len(strikes) > 5 else ', '.join(strikes))
                
                # Show details for a sample option
                if strikes:
                    first_strike = strikes[0]
                    option = options_data['callExpDateMap'][first_exp][first_strike][0]
                    print(f"  - Sample option at strike {first_strike}:")
                    self._print_option_details(option)
        else:
            print("- No call options data found")
            
        # Check put options
        if 'putExpDateMap' in options_data and options_data['putExpDateMap']:
            put_expirations = list(options_data['putExpDateMap'].keys())
            print(f"- Put options: {len(put_expirations)} expiration dates")
            
            # Show details for the first expiration
            if put_expirations:
                first_exp = put_expirations[0]
                strikes = list(options_data['putExpDateMap'][first_exp].keys())
                print(f"  Sample expiration {first_exp}:")
                print(f"  - {len(strikes)} strikes available: " + 
                      f"{', '.join(strikes[:5])}..." if len(strikes) > 5 else ', '.join(strikes))
                
                # Show details for a sample option
                if strikes:
                    first_strike = strikes[0]
                    option = options_data['putExpDateMap'][first_exp][first_strike][0]
                    print(f"  - Sample option at strike {first_strike}:")
                    self._print_option_details(option)
        else:
            print("- No put options data found")
            
        print("\n🧩 Checking for suitable iron condor components...")
        
        # Find candidate option pairs for iron condors
        self._check_iron_condor_candidates(options_data)
    
    def _print_option_details(self, option):
        """Print important details of an option contract"""
        # Check what fields are available
        fields = option.keys()
        
        # Print essential fields if they exist
        essential_fields = ['bid', 'ask', 'mark', 'delta', 'gamma', 'theta', 'vega', 
                            'totalVolume', 'openInterest', 'inTheMoney']
        
        for field in essential_fields:
            if field in option:
                print(f"    {field}: {option[field]}")
            else:
                print(f"    {field}: [Not available]")
                
        # Check if any required fields for iron condor analysis are missing
        missing_fields = [f for f in ['bid', 'ask', 'delta'] if f not in fields]
        if missing_fields:
            print(f"    ⚠️ Missing required fields: {', '.join(missing_fields)}")
    
    def _check_iron_condor_candidates(self, options_data):
        """Check if there are potential iron condor candidates in the data"""
        if not options_data or 'callExpDateMap' not in options_data or 'putExpDateMap' not in options_data:
            print("⚠️ Incomplete options data, cannot check for iron condor candidates")
            return
            
        # Get current price
        current_price = options_data.get('underlying', self.current_price)
        if not current_price:
            print("⚠️ Cannot determine current price for checking iron condors")
            return
            
        print(f"Current price: ${current_price}")
        
        # Check a sample of expirations
        call_expirations = list(options_data['callExpDateMap'].keys())
        put_expirations = list(options_data['putExpDateMap'].keys())
        
        # Find common expirations
        common_expirations = set(call_expirations).intersection(set(put_expirations))
        if not common_expirations:
            print("⚠️ No common expirations found between calls and puts")
            return
            
        print(f"Found {len(common_expirations)} common expirations")
        
        # Check a sample expiration
        if common_expirations:
            sample_exp = list(common_expirations)[0]
            print(f"Checking expiration: {sample_exp}")
            
            # Get all strikes
            call_strikes = sorted([float(strike) for strike in options_data['callExpDateMap'][sample_exp].keys()])
            put_strikes = sorted([float(strike) for strike in options_data['putExpDateMap'][sample_exp].keys()])
            
            if not call_strikes or not put_strikes:
                print("⚠️ No strike prices available for this expiration")
                return
                
            print(f"Call strikes range: {min(call_strikes)} to {max(call_strikes)}")
            print(f"Put strikes range: {min(put_strikes)} to {max(put_strikes)}")
            
            # Check for potential iron condor strikes (above and below current price)
            otm_calls = [strike for strike in call_strikes if strike > current_price]
            otm_puts = [strike for strike in put_strikes if strike < current_price]
            
            if not otm_calls or not otm_puts:
                print("⚠️ No suitable OTM options found for iron condor")
                return
                
            print(f"Found {len(otm_calls)} OTM calls and {len(otm_puts)} OTM puts")
            
            # Check for spread possibilities
            if len(otm_calls) >= 2 and len(otm_puts) >= 2:
                # Sample short call
                short_call_strike = otm_calls[0]  # Closest to the money
                short_call = options_data['callExpDateMap'][sample_exp][str(short_call_strike)][0]
                
                # Sample long call
                long_call_strike = otm_calls[min(1, len(otm_calls)-1)]  # Second closest or same if only one
                long_call = options_data['callExpDateMap'][sample_exp][str(long_call_strike)][0]
                
                # Sample short put
                short_put_strike = otm_puts[-1]  # Closest to the money
                short_put = options_data['putExpDateMap'][sample_exp][str(short_put_strike)][0]
                
                # Sample long put
                long_put_strike = otm_puts[-min(2, len(otm_puts))]  # Second closest or same if only one
                long_put = options_data['putExpDateMap'][sample_exp][str(long_put_strike)][0]
                
                print(f"\nPossible iron condor structure:")
                print(f"Long Put @ {long_put_strike} - Short Put @ {short_put_strike} - " +
                      f"Short Call @ {short_call_strike} - Long Call @ {long_call_strike}")
                
                # Check if we have all necessary data
                missing_data = False
                for option_name, option in [("Long Put", long_put), ("Short Put", short_put), 
                                           ("Short Call", short_call), ("Long Call", long_call)]:
                    if 'bid' not in option or 'ask' not in option:
                        print(f"⚠️ Missing bid/ask data for {option_name}")
                        missing_data = True
                    if 'delta' not in option:
                        print(f"⚠️ Missing delta data for {option_name}")
                        missing_data = True
                
                if not missing_data:
                    # Calculate potential credit and deltas
                    credit = (short_call.get('bid', 0) - long_call.get('ask', 0) + 
                              short_put.get('bid', 0) - long_put.get('ask', 0))
                    total_delta = (short_call.get('delta', 0) - long_call.get('delta', 0) + 
                                  short_put.get('delta', 0) - long_put.get('delta', 0))
                    
                    print(f"Potential credit: ${credit:.2f}")
                    print(f"Total delta: {total_delta:.4f}")
                    
                    # Check liquidity
                    print(f"Option volumes:")
                    print(f"Long Put: {long_put.get('totalVolume', 0)}")
                    print(f"Short Put: {short_put.get('totalVolume', 0)}")
                    print(f"Short Call: {short_call.get('totalVolume', 0)}")
                    print(f"Long Call: {long_call.get('totalVolume', 0)}")
            else:
                print("⚠️ Not enough OTM options for a proper iron condor spread")
        
        # Save sample options to file for debugging
        try:
            with open('debug_options_data.json', 'w') as f:
                json.dump({
                    'sample_expiration': sample_exp,
                    'current_price': current_price,
                    'call_sample': options_data['callExpDateMap'][sample_exp],
                    'put_sample': options_data['putExpDateMap'][sample_exp]
                }, f, indent=2)
            print("\nSaved sample options data to debug_options_data.json for further analysis")
        except Exception as e:
            print(f"Could not save debug data: {e}")
    
    def get_option_chain(self):
        """Get options chain from Schwab API"""
        if not self.client:
            print("⚠️ SCHWAB API ERROR: Client not initialized. Please check your API credentials.")
            raise ValueError("Schwab client not initialized. Please check your API credentials.")
            
        # Format dates for the API
        today = datetime.datetime.now().date()
        from_date = today + datetime.timedelta(days=self.min_dte)
        to_date = today + datetime.timedelta(days=self.max_dte)
        
        # Make sure we have current price
        if not self.current_price:
            self.current_price = self.get_current_price()
        
        try:
            # Fetch options chain from Schwab
            try:
                print(f"Fetching options chain from Schwab for {self.symbol} (from {from_date} to {to_date})")
                options_response = self.client.get_option_chain(
                    symbol=self.symbol,
                    contract_type=schwab_client.Client.Options.ContractType.ALL,  # ALL, CALL, PUT
                    from_date=from_date,
                    to_date=to_date,
                    strike_count=50,  # Number of strikes above and below current price
                    strike_range=schwab_client.Client.Options.StrikeRange.ALL,  # Get ALL strike prices
                    include_underlying_quote=True
                )
                
                # Check for HTTP errors
                if hasattr(options_response, 'status_code'):
                    if options_response.status_code == 429:
                        print(f"⚠️ SCHWAB API RATE LIMIT EXCEEDED (429): Too many requests for options data")
                        raise Exception("Rate limit exceeded when fetching options data")
                    elif options_response.status_code != 200:
                        print(f"⚠️ SCHWAB API ERROR ({options_response.status_code}): Failed to get options chain")
                        raise Exception(f"Failed to get options chain: HTTP {options_response.status_code}")
                
                options_data = options_response.json()
                
                # Check for API errors in response
                if 'errors' in options_data:
                    print(f"⚠️ SCHWAB API ERROR: {options_data['errors']}")
                    raise Exception(f"Schwab API returned errors: {options_data['errors']}")
            except Exception as e:
                print(f"⚠️ SCHWAB API ERROR while fetching options chain: {str(e)}")
                raise Exception(f"Error fetching options chain: {str(e)}")
            
            # Transform the response to match our expected format if needed
            result = {
                'callExpDateMap': {},
                'putExpDateMap': {},
                'underlying': self.current_price
            }
            
            # Process calls and puts
            if 'callExpDateMap' in options_data:
                result['callExpDateMap'] = options_data['callExpDateMap']
                print(f"✓ Successfully fetched call options for {len(options_data['callExpDateMap'])} expiration dates")
            else:
                print("⚠️ No call options data found in response")
                
            if 'putExpDateMap' in options_data:
                result['putExpDateMap'] = options_data['putExpDateMap']
                print(f"✓ Successfully fetched put options for {len(options_data['putExpDateMap'])} expiration dates")
            else:
                print("⚠️ No put options data found in response")
            
            # Debug the option chain structure
            self._print_option_summary(result)
                
            return result
        except Exception as e:
            print(f"⚠️ SCHWAB API ERROR: {str(e)}")
            raise 