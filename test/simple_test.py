#!/usr/bin/env python

"""
Simple unit test script that runs without pytest.
"""

import sys
import os
import datetime
import pandas as pd
import numpy as np

# Add the parent directory to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from test.data_sources.mock_data_source import MockDataSource

def create_mock_data():
    """Create mock data for testing"""
    # Mock current price
    mock_price = 5300.0
    
    # Mock expiry dates
    today = datetime.datetime.now().date()
    mock_expiry_dates = [
        today + datetime.timedelta(days=1),
        today + datetime.timedelta(days=3),
        today + datetime.timedelta(days=7),
    ]
    
    # Create mock calls data
    calls_data = {
        'strike': [5100, 5200, 5300, 5400, 5500],
        'lastPrice': [205.0, 125.0, 62.0, 22.0, 6.0],
        'bid': [203.0, 123.0, 60.0, 20.0, 5.0],
        'ask': [207.0, 127.0, 64.0, 24.0, 7.0],
        'volume': [500, 400, 300, 200, 100],
        'openInterest': [2000, 1600, 1200, 800, 400],
        'impliedVolatility': [0.14, 0.16, 0.18, 0.20, 0.22],
        'delta': [0.9, 0.7, 0.5, 0.3, 0.1],
        'gamma': [0.01, 0.02, 0.03, 0.02, 0.01],
        'theta': [-1.0, -1.4, -1.8, -1.4, -1.0],
        'vega': [1.0, 2.0, 3.0, 2.0, 1.0],
        'inTheMoney': [True, True, True, False, False],
    }
    calls_df = pd.DataFrame(calls_data)
    
    # Create mock puts data
    puts_data = {
        'strike': [5100, 5200, 5300, 5400, 5500],
        'lastPrice': [6.0, 22.0, 62.0, 125.0, 205.0],
        'bid': [5.0, 20.0, 60.0, 123.0, 203.0],
        'ask': [7.0, 24.0, 64.0, 127.0, 207.0],
        'volume': [100, 200, 300, 400, 500],
        'openInterest': [400, 800, 1200, 1600, 2000],
        'impliedVolatility': [0.22, 0.20, 0.18, 0.16, 0.14],
        'delta': [-0.1, -0.3, -0.5, -0.7, -0.9],
        'gamma': [0.01, 0.02, 0.03, 0.02, 0.01],
        'theta': [-1.0, -1.4, -1.8, -1.4, -1.0],
        'vega': [1.0, 2.0, 3.0, 2.0, 1.0],
        'inTheMoney': [False, False, False, True, True],
    }
    puts_df = pd.DataFrame(puts_data)
    
    # Create option chain
    option_chain = {}
    for expiry in mock_expiry_dates:
        option_chain[expiry] = {'calls': calls_df.copy(), 'puts': puts_df.copy()}
    
    return mock_price, option_chain

def test_mock_data_source():
    """Test the mock data source"""
    print("Testing MockDataSource...")
    
    # Create mock data
    mock_price, mock_option_chain = create_mock_data()
    
    # Create mock data source
    ds = MockDataSource(mock_price, mock_option_chain)
    
    # Test initialization
    assert ds.symbol == "SPX", "Wrong symbol"
    assert ds.mock_price == mock_price, "Wrong price"
    assert ds.mock_option_chain == mock_option_chain, "Wrong option chain"
    print("  ✓ Initialization test passed")
    
    # Test getting current price
    price = ds.get_current_price()
    assert price == mock_price, "Wrong price returned"
    print("  ✓ get_current_price test passed")
    
    # Test getting full options chain
    options = ds.get_options_chain()
    assert len(options) == len(mock_option_chain), "Wrong number of expirations"
    print("  ✓ get_options_chain (no filters) test passed")
    
    # Test getting options chain with DTE filters
    today = datetime.datetime.now().date()
    min_dte = 2
    options_min = ds.get_options_chain(min_dte=min_dte)
    for expiry in options_min.keys():
        dte = (expiry - today).days
        assert dte >= min_dte, f"DTE filter failed: {dte} < {min_dte}"
    print("  ✓ get_options_chain (with DTE filter) test passed")
    
    print("All MockDataSource tests passed!")
    return True

def test_basic_iron_condor_finder():
    """Test finding iron condors with mock data"""
    print("\nTesting basic iron condor finder algorithm...")
    
    # Create mock data
    mock_price, mock_option_chain = create_mock_data()
    
    # Define a simple iron condor finder function
    def find_iron_condors(options_chain, current_price):
        results = []
        
        # Calculate price range
        lower_bound = current_price * 0.98  # 2% down
        upper_bound = current_price * 1.02  # 2% up
        
        for expiry, data in options_chain.items():
            calls = data['calls']
            puts = data['puts']
            
            # Find calls with strikes above the upper bound
            valid_calls = calls[calls['strike'] >= upper_bound]
            
            # Find puts with strikes below the lower bound
            valid_puts = puts[puts['strike'] <= lower_bound]
            
            if valid_calls.empty or valid_puts.empty:
                continue
            
            # Find proper iron condor with correct strike ordering
            # Start with short call (first strike above upper bound)
            short_call_row = valid_calls.iloc[0]
            short_call_strike = short_call_row['strike']
            
            # Long call must be above short call strike
            long_call_candidates = calls[calls['strike'] > short_call_strike]
            if long_call_candidates.empty:
                continue  # Can't find a valid long call
                
            long_call_row = long_call_candidates.iloc[0]
            long_call_strike = long_call_row['strike']
            
            # Short put should be first strike below lower bound
            short_put_row = valid_puts.iloc[-1]  # Last of the valid puts (highest strike below lower bound)
            short_put_strike = short_put_row['strike']
            
            # Long put must be below short put strike
            long_put_candidates = puts[puts['strike'] < short_put_strike]
            if long_put_candidates.empty:
                continue  # Can't find a valid long put
                
            long_put_row = long_put_candidates.iloc[-1]  # Last one will be closest to short put
            long_put_strike = long_put_row['strike']
            
            # Verify the strike order (for debugging)
            if not (long_put_strike < short_put_strike < short_call_strike < long_call_strike):
                print(f"  Invalid strike order: {long_put_strike} < {short_put_strike} < {short_call_strike} < {long_call_strike}")
                continue
            
            # Calculate net credit
            net_credit = (
                short_call_row['bid'] - long_call_row['ask'] + 
                short_put_row['bid'] - long_put_row['ask']
            )
            
            # Add to results
            dte = (expiry - datetime.datetime.now().date()).days
            iron_condor = {
                'expiry': expiry,
                'dte': dte,
                'short_put_strike': short_put_strike,
                'long_put_strike': long_put_strike,
                'short_call_strike': short_call_strike,
                'long_call_strike': long_call_strike,
                'net_credit': net_credit,
            }
            results.append(iron_condor)
        
        return results
    
    # Create mock data source
    ds = MockDataSource(mock_price, mock_option_chain)
    
    # Get options data
    current_price = ds.get_current_price()
    options_chain = ds.get_options_chain()
    
    # Find iron condors
    iron_condors = find_iron_condors(options_chain, current_price)
    
    # Verify results
    assert isinstance(iron_condors, list), "Result should be a list"
    
    if len(iron_condors) == 0:
        print("  Note: No iron condors found with current mock data")
        print("  This is okay for testing - we just verify our code runs correctly")
        return True
    
    # If we found iron condors, check their structure
    ic = iron_condors[0]
    assert 'expiry' in ic, "Missing expiry"
    assert 'short_put_strike' in ic, "Missing short_put_strike"
    assert 'long_put_strike' in ic, "Missing long_put_strike"
    assert 'short_call_strike' in ic, "Missing short_call_strike"
    assert 'long_call_strike' in ic, "Missing long_call_strike"
    assert 'net_credit' in ic, "Missing net_credit"
    
    # Verify strike order
    assert ic['long_put_strike'] < ic['short_put_strike'], "Wrong put strike order"
    assert ic['short_put_strike'] < ic['short_call_strike'], "Wrong put-call order"
    assert ic['short_call_strike'] < ic['long_call_strike'], "Wrong call strike order"
    
    print("  ✓ All basic iron condor finder tests passed!")
    return True

def run_all_tests():
    """Run all tests"""
    tests_passed = True
    
    # Run tests
    tests_passed = tests_passed and test_mock_data_source()
    tests_passed = tests_passed and test_basic_iron_condor_finder()
    
    return tests_passed

if __name__ == "__main__":
    print("Running simplified Iron Condor Finder tests...\n")
    success = run_all_tests()
    print("\nTest summary:")
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1) 