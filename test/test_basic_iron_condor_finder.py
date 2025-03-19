import pytest
from datetime import datetime
import pandas as pd
import math

from test.data_sources.mock_data_source import MockDataSource

# Simple Iron Condor finding function for testing purposes
def find_iron_condors(options_chain, current_price, max_move_pct=2.0, max_delta=0.01):
    """
    Simple iron condor finder function for testing
    
    Parameters:
    options_chain: Dictionary with expiry dates as keys and option chains as values
    current_price: Current price of the underlying
    max_move_pct: Maximum expected move (in %) we're betting against
    max_delta: Maximum acceptable overall position delta
    
    Returns:
    list: List of iron condor opportunities
    """
    results = []
    
    # Calculate price range
    lower_bound = current_price * (1 - max_move_pct/100)
    upper_bound = current_price * (1 + max_move_pct/100)
    
    # Iterate through expiry dates
    for expiry, data in options_chain.items():
        calls = data['calls']
        puts = data['puts']
        
        # Find calls with strikes above the upper bound
        valid_calls = calls[calls['strike'] >= upper_bound]
        
        # Find puts with strikes below the lower bound
        valid_puts = puts[puts['strike'] <= lower_bound]
        
        if valid_calls.empty or valid_puts.empty:
            continue
        
        # Try different combinations
        for i, short_call_row in valid_calls.iterrows():
            short_call_strike = short_call_row['strike']
            
            # Find the next higher strike for long call
            long_call_candidates = valid_calls[valid_calls['strike'] > short_call_strike]
            if long_call_candidates.empty:
                continue
                
            long_call_row = long_call_candidates.iloc[0]
            long_call_strike = long_call_row['strike']
            
            for j, short_put_row in valid_puts.iterrows():
                short_put_strike = short_put_row['strike']
                
                # Find the next lower strike for long put
                long_put_candidates = valid_puts[valid_puts['strike'] < short_put_strike]
                if long_put_candidates.empty:
                    continue
                    
                long_put_row = long_put_candidates.iloc[-1]
                long_put_strike = long_put_row['strike']
                
                # Calculate position delta
                position_delta = (
                    short_call_row['delta'] + 
                    long_call_row['delta'] + 
                    short_put_row['delta'] + 
                    long_put_row['delta']
                )
                
                # Filter by delta neutrality
                if abs(position_delta) > max_delta:
                    continue
                
                # Calculate net credit
                net_credit = (
                    short_call_row['bid'] - long_call_row['ask'] + 
                    short_put_row['bid'] - long_put_row['ask']
                )
                
                # Calculate max loss
                call_spread_width = long_call_strike - short_call_strike
                put_spread_width = short_put_strike - long_put_strike
                max_loss = min(call_spread_width, put_spread_width) - net_credit
                
                # Only include profitable iron condors
                if net_credit <= 0 or max_loss <= 0:
                    continue
                
                # Calculate basic metrics
                risk_reward = max_loss / net_credit
                
                # Add to results
                dte = (expiry - datetime.now().date()).days
                iron_condor = {
                    'expiry': expiry,
                    'dte': dte,
                    'short_put_strike': short_put_strike,
                    'long_put_strike': long_put_strike,
                    'short_call_strike': short_call_strike,
                    'long_call_strike': long_call_strike,
                    'net_credit': net_credit,
                    'max_loss': max_loss,
                    'position_delta': position_delta,
                    'risk_reward': risk_reward,
                }
                results.append(iron_condor)
    
    # Sort by risk/reward ratio (better opportunities first)
    results.sort(key=lambda x: x['risk_reward'])
    return results

def test_find_iron_condors(mock_spx_price, mock_option_chain):
    """Test finding iron condors using mock data"""
    # Get options data from mock data source
    data_source = MockDataSource(mock_spx_price, mock_option_chain)
    current_price = data_source.get_current_price()
    options_chain = data_source.get_options_chain()
    
    # Find iron condors
    iron_condors = find_iron_condors(options_chain, current_price)
    
    # Basic assertions
    assert isinstance(iron_condors, list)
    
    # Should find at least some iron condors
    assert len(iron_condors) > 0
    
    # Check structure of results
    for ic in iron_condors:
        assert 'expiry' in ic
        assert 'short_put_strike' in ic
        assert 'long_put_strike' in ic
        assert 'short_call_strike' in ic
        assert 'long_call_strike' in ic
        assert 'net_credit' in ic
        assert 'max_loss' in ic
        assert 'position_delta' in ic
        assert 'risk_reward' in ic
        
        # Validate strike order
        assert ic['long_put_strike'] < ic['short_put_strike']
        assert ic['short_put_strike'] < ic['short_call_strike']
        assert ic['short_call_strike'] < ic['long_call_strike']
        
        # Validate metrics
        assert ic['net_credit'] > 0
        assert ic['max_loss'] > 0
        assert abs(ic['position_delta']) <= 0.01
        
        # Check that risk/reward is reasonable (not too high)
        assert 1 < ic['risk_reward'] < 30 