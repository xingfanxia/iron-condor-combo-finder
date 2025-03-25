"""Interactive Brokers API data source for options chains"""

import os
import datetime
from dotenv import load_dotenv

# Import Interactive Brokers client
try:
    from ib_async import IB, Contract, Option, util
except ImportError:
    print("ib_async not installed. Run: pip install ib_async")
    
from .base import DataSourceBase

# Load environment variables
load_dotenv()


class IBDataSource(DataSourceBase):
    """Interactive Brokers API data source for options chains"""
    
    def __init__(self, symbol, min_dte, max_dte, min_liquidity):
        super().__init__(symbol, min_dte, max_dte, min_liquidity)
        self.host = os.getenv('IB_HOST', '127.0.0.1')
        self.port = int(os.getenv('IB_PORT', '7497'))  # Default TWS port
        self.client_id = int(os.getenv('IB_CLIENT_ID', '1'))
        self.ib = None
        self._option_chains_cache = {}
        self._last_fetch_time = 0
        self._cache_expiry = 300  # Cache expiry in seconds (5 minutes)
    
    def _init_client(self):
        """Initialize the Interactive Brokers client"""
        if self.ib and self.ib.isConnected():
            return self.ib
            
        try:
            ib = IB()
            ib.connect(self.host, self.port, clientId=self.client_id)
            # Set timeout to 30 seconds for all requests
            ib.reqTimeout = 30
            print(f"Connected to Interactive Brokers at {self.host}:{self.port}")
            return ib
        except Exception as e:
            print(f"Error connecting to Interactive Brokers: {e}")
            return None
    
    def get_current_price(self):
        """Get current price from IB API"""
        self.ib = self._init_client()
        if not self.ib:
            return super().get_current_price()
        
        try:
            # Create a contract for the symbol
            if self.symbol == 'SPX':
                # SPX is a special case as it's an index
                contract = Contract(symbol='SPX', secType='IND', exchange='CBOE', currency='USD')
            else:
                # For stocks and ETFs
                contract = Contract(symbol=self.symbol, secType='STK', exchange='SMART', currency='USD')
            
            # Request market data - try delayed data if real-time not available
            for market_data_type in [1, 3]:  # 1 = Live, 3 = Delayed
                self.ib.reqMarketDataType(market_data_type)
                ticker = self.ib.reqMktData(contract)
                
                # Wait for data to arrive
                timeout = 0
                while timeout < 10 and (not ticker.last and not ticker.close):
                    self.ib.sleep(0.5)
                    timeout += 0.5
                
                # Get the last price
                if ticker.last or ticker.close or ticker.bid or ticker.ask:
                    # Prefer last price, then close, then midpoint of bid/ask
                    if ticker.last:
                        self.current_price = ticker.last
                    elif ticker.close:
                        self.current_price = ticker.close
                    elif ticker.bid and ticker.ask:
                        self.current_price = (ticker.bid + ticker.ask) / 2
                    else:
                        self.current_price = ticker.bid or ticker.ask
                        
                    # Cancel the market data subscription
                    self.ib.cancelMktData(contract)
                    return self.current_price
            
            print("No price data received from IB")
            return super().get_current_price()
                
        except Exception as e:
            print(f"Error getting price from IB API: {e}")
            # Fallback to base implementation
            return super().get_current_price()
        finally:
            # Don't disconnect yet as we'll need the client for options chain
            pass
    
    def get_option_chain(self):
        """Get options chain from Interactive Brokers API"""
        # Check if we have a valid cached version
        current_time = datetime.datetime.now().timestamp()
        cache_key = f"{self.symbol}_{self.min_dte}_{self.max_dte}_{self.min_liquidity}"
        
        if (cache_key in self._option_chains_cache and 
            current_time - self._last_fetch_time < self._cache_expiry):
            print("Using cached options chain data")
            return self._option_chains_cache[cache_key]
        
        if not self.ib:
            self.ib = self._init_client()
            
        if not self.ib:
            raise ValueError("Interactive Brokers client not initialized. Please check your connection settings.")
            
        # Make sure we have current price
        if not self.current_price:
            self.current_price = self.get_current_price()
        
        try:
            # Get today's date and calculate expiration date range
            today = datetime.datetime.now().date()
            min_date = today + datetime.timedelta(days=self.min_dte)
            max_date = today + datetime.timedelta(days=self.max_dte)
            
            # Define the contract for getting option chains
            if self.symbol == 'SPX':
                # SPX is a special case as it's an index
                contract = Contract(symbol='SPX', secType='IND', exchange='CBOE', currency='USD')
            else:
                # For stocks and ETFs
                contract = Contract(symbol=self.symbol, secType='STK', exchange='SMART', currency='USD')
            
            # Request contract details to get available expiration dates
            contracts = self.ib.qualifyContracts(contract)
            if not contracts:
                raise ValueError(f"Could not qualify contract for {self.symbol}")
                
            contract = contracts[0]
            
            # Request option chain parameters
            chains = self.ib.reqSecDefOptParams(
                underlyingSymbol=self.symbol,
                futFopExchange='',
                underlyingSecType=contract.secType,
                underlyingConId=contract.conId
            )
            
            if not chains:
                raise ValueError(f"No option chains found for {self.symbol}")
            
            # Prepare result structure
            result = {
                'callExpDateMap': {},
                'putExpDateMap': {},
                'underlying': self.current_price
            }
            
            # Set market data type (try to use real-time data first, then fall back to delayed)
            for market_data_type in [1, 3]:  # 1 = Live, 3 = Delayed
                self.ib.reqMarketDataType(market_data_type)
                
                # Process each expiration
                for params in chains:
                    exchange = params.exchange
                    
                    for expiry in params.expirations:
                        # Convert to datetime
                        try:
                            exp_date = datetime.datetime.strptime(expiry, '%Y%m%d').date()
                        except ValueError:
                            try:
                                exp_date = datetime.datetime.strptime(expiry, '%Y%m%d%H%M%S').date()
                            except ValueError:
                                print(f"Could not parse expiration date: {expiry}")
                                continue
                        
                        # Skip if outside our date range
                        if exp_date < min_date or exp_date > max_date:
                            continue
                        
                        # Calculate DTE (days to expiration)
                        dte = (exp_date - today).days
                        
                        # Format expiration for our data structure
                        exp_str = exp_date.strftime('%Y-%m-%d')
                        exp_key = f"{exp_str}:{dte}"
                        
                        # Initialize structures for this expiration
                        if exp_key not in result['callExpDateMap']:
                            result['callExpDateMap'][exp_key] = {}
                        if exp_key not in result['putExpDateMap']:
                            result['putExpDateMap'][exp_key] = {}
                        
                        # Get strikes for this expiration
                        # Filter strikes based on current price (within a reasonable range)
                        filtered_strikes = []
                        price_buffer = 0.15  # Consider strikes within 15% of current price
                        for strike in params.strikes:
                            strike_pct_diff = abs(strike - self.current_price) / self.current_price
                            if strike_pct_diff <= price_buffer:
                                filtered_strikes.append(strike)
                        
                        # Create all option contracts at once for this expiration
                        call_contracts = []
                        put_contracts = []
                        
                        for strike in filtered_strikes:
                            call_contract = Option(
                                symbol=self.symbol,
                                lastTradeDateOrContractMonth=expiry,
                                strike=strike,
                                right='C',
                                exchange=exchange
                            )
                            
                            put_contract = Option(
                                symbol=self.symbol,
                                lastTradeDateOrContractMonth=expiry,
                                strike=strike,
                                right='P',
                                exchange=exchange
                            )
                            
                            call_contracts.append(call_contract)
                            put_contracts.append(put_contract)
                        
                        # Qualify all contracts at once
                        qualified_calls = self.ib.qualifyContracts(*call_contracts)
                        qualified_puts = self.ib.qualifyContracts(*put_contracts)
                        
                        # Request market data for all options at once
                        call_tickers = {}
                        put_tickers = {}
                        
                        for i, contract in enumerate(qualified_calls):
                            if contract:
                                ticker = self.ib.reqMktData(contract, genericTickList='101,104,106')  # Include greeks and implied vol
                                call_tickers[filtered_strikes[i]] = (contract, ticker)
                        
                        for i, contract in enumerate(qualified_puts):
                            if contract:
                                ticker = self.ib.reqMktData(contract, genericTickList='101,104,106')
                                put_tickers[filtered_strikes[i]] = (contract, ticker)
                        
                        # Give time for data to arrive
                        self.ib.sleep(2)
                        
                        # Process all options
                        for strike in filtered_strikes:
                            # Process call option
                            if strike in call_tickers:
                                contract, call_ticker = call_tickers[strike]
                                
                                # Skip if no useful data
                                if not (call_ticker.bidSize or call_ticker.askSize or call_ticker.volume):
                                    continue
                                    
                                # Calculate mid price if bid/ask available
                                mid_price = None
                                if call_ticker.bid is not None and call_ticker.ask is not None:
                                    mid_price = (call_ticker.bid + call_ticker.ask) / 2
                                
                                # Create call option data
                                call_data = [{
                                    'putCall': 'CALL',
                                    'symbol': self.symbol,
                                    'description': f"{self.symbol} {exp_date} {strike} Call",
                                    'exchangeName': exchange,
                                    'bid': call_ticker.bid if call_ticker.bid is not None else 0,
                                    'ask': call_ticker.ask if call_ticker.ask is not None else 0,
                                    'last': call_ticker.last if call_ticker.last is not None else 0,
                                    'mark': mid_price if mid_price is not None else 0,
                                    'bidSize': call_ticker.bidSize if call_ticker.bidSize is not None else 0,
                                    'askSize': call_ticker.askSize if call_ticker.askSize is not None else 0,
                                    'lastSize': call_ticker.lastSize if call_ticker.lastSize is not None else 0,
                                    'highPrice': call_ticker.high if call_ticker.high is not None else 0,
                                    'lowPrice': call_ticker.low if call_ticker.low is not None else 0,
                                    'openPrice': call_ticker.open if call_ticker.open is not None else 0,
                                    'closePrice': call_ticker.close if call_ticker.close is not None else 0,
                                    'totalVolume': call_ticker.volume if call_ticker.volume is not None else 0,
                                    'openInterest': 0,  # IB doesn't provide this directly in tickers
                                    'volatility': call_ticker.impliedVol if call_ticker.impliedVol is not None else 0.2,
                                    'delta': call_ticker.modelGreeks.delta if call_ticker.modelGreeks else 0,
                                    'gamma': call_ticker.modelGreeks.gamma if call_ticker.modelGreeks else 0,
                                    'theta': call_ticker.modelGreeks.theta if call_ticker.modelGreeks else 0,
                                    'vega': call_ticker.modelGreeks.vega if call_ticker.modelGreeks else 0,
                                    'rho': call_ticker.modelGreeks.rho if call_ticker.modelGreeks else 0,
                                    'strikePrice': strike,
                                    'expirationDate': exp_str,
                                    'daysToExpiration': dte,
                                    'multiplier': 100,
                                    'inTheMoney': strike < self.current_price
                                }]
                                result['callExpDateMap'][exp_key][strike] = call_data
                            
                            # Process put option
                            if strike in put_tickers:
                                contract, put_ticker = put_tickers[strike]
                                
                                # Skip if no useful data
                                if not (put_ticker.bidSize or put_ticker.askSize or put_ticker.volume):
                                    continue
                                
                                # Calculate mid price if bid/ask available
                                mid_price = None
                                if put_ticker.bid is not None and put_ticker.ask is not None:
                                    mid_price = (put_ticker.bid + put_ticker.ask) / 2
                                
                                # Create put option data
                                put_data = [{
                                    'putCall': 'PUT',
                                    'symbol': self.symbol,
                                    'description': f"{self.symbol} {exp_date} {strike} Put",
                                    'exchangeName': exchange,
                                    'bid': put_ticker.bid if put_ticker.bid is not None else 0,
                                    'ask': put_ticker.ask if put_ticker.ask is not None else 0,
                                    'last': put_ticker.last if put_ticker.last is not None else 0,
                                    'mark': mid_price if mid_price is not None else 0,
                                    'bidSize': put_ticker.bidSize if put_ticker.bidSize is not None else 0,
                                    'askSize': put_ticker.askSize if put_ticker.askSize is not None else 0,
                                    'lastSize': put_ticker.lastSize if put_ticker.lastSize is not None else 0,
                                    'highPrice': put_ticker.high if put_ticker.high is not None else 0,
                                    'lowPrice': put_ticker.low if put_ticker.low is not None else 0,
                                    'openPrice': put_ticker.open if put_ticker.open is not None else 0,
                                    'closePrice': put_ticker.close if put_ticker.close is not None else 0,
                                    'totalVolume': put_ticker.volume if put_ticker.volume is not None else 0,
                                    'openInterest': 0,  # IB doesn't provide this directly in tickers
                                    'volatility': put_ticker.impliedVol if put_ticker.impliedVol is not None else 0.2,
                                    'delta': put_ticker.modelGreeks.delta if put_ticker.modelGreeks else 0,
                                    'gamma': put_ticker.modelGreeks.gamma if put_ticker.modelGreeks else 0,
                                    'theta': put_ticker.modelGreeks.theta if put_ticker.modelGreeks else 0,
                                    'vega': put_ticker.modelGreeks.vega if put_ticker.modelGreeks else 0,
                                    'rho': put_ticker.modelGreeks.rho if put_ticker.modelGreeks else 0,
                                    'strikePrice': strike,
                                    'expirationDate': exp_str,
                                    'daysToExpiration': dte,
                                    'multiplier': 100,
                                    'inTheMoney': strike > self.current_price
                                }]
                                result['putExpDateMap'][exp_key][strike] = put_data
                                
                        # Cancel market data for this batch to avoid overloading TWS/Gateway
                        for _, (_, ticker) in call_tickers.items():
                            self.ib.cancelMktData(ticker.contract)
                        for _, (_, ticker) in put_tickers.items():
                            self.ib.cancelMktData(ticker.contract)
                
                # If we got data, break out of the market data type loop
                if result['callExpDateMap'] and result['putExpDateMap']:
                    break
            
            # Cache the result
            self._option_chains_cache[cache_key] = result
            self._last_fetch_time = current_time
            
            return result
            
        except Exception as e:
            print(f"⚠️ IB API ERROR accessing data: {e}")
            raise
        finally:
            # Disconnect from IB
            if self.ib and self.ib.isConnected():
                self.ib.disconnect()
                print("Disconnected from Interactive Brokers") 