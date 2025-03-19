import pytest
import pandas as pd
import datetime
import numpy as np

@pytest.fixture
def mock_spx_price():
    """Fixture for mock SPX price"""
    return 5300.0

@pytest.fixture
def mock_option_expiry_dates():
    """Fixture for mock option expiry dates"""
    today = datetime.datetime.now().date()
    return [
        today + datetime.timedelta(days=1),
        today + datetime.timedelta(days=3),
        today + datetime.timedelta(days=7),
        today + datetime.timedelta(days=14),
        today + datetime.timedelta(days=30),
        today + datetime.timedelta(days=60),
    ]

@pytest.fixture
def mock_calls_data():
    """Fixture for mock calls data"""
    # Create a DataFrame with mock call options data
    calls_data = {
        'strike': [5100, 5150, 5200, 5250, 5300, 5350, 5400, 5450, 5500],
        'lastPrice': [210.0, 165.0, 126.0, 92.0, 62.0, 38.0, 22.0, 12.0, 6.0],
        'bid': [208.0, 163.0, 124.0, 90.0, 60.0, 36.0, 20.0, 10.0, 5.0],
        'ask': [212.0, 167.0, 128.0, 94.0, 64.0, 40.0, 24.0, 14.0, 7.0],
        'change': [-5.0, -4.5, -4.0, -3.5, -3.0, -2.5, -2.0, -1.5, -1.0],
        'percentChange': [-2.33, -2.66, -3.08, -3.67, -4.62, -6.17, -8.33, -11.11, -14.29],
        'volume': [500, 450, 400, 350, 300, 250, 200, 150, 100],
        'openInterest': [2000, 1800, 1600, 1400, 1200, 1000, 800, 600, 400],
        'impliedVolatility': [0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.20, 0.21, 0.22],
        'delta': [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1],
        'gamma': [0.01, 0.015, 0.02, 0.025, 0.03, 0.025, 0.02, 0.015, 0.01],
        'theta': [-1.0, -1.2, -1.4, -1.6, -1.8, -1.6, -1.4, -1.2, -1.0],
        'vega': [1.0, 1.5, 2.0, 2.5, 3.0, 2.5, 2.0, 1.5, 1.0],
        'inTheMoney': [True, True, True, True, False, False, False, False, False],
    }
    return pd.DataFrame(calls_data)

@pytest.fixture
def mock_puts_data():
    """Fixture for mock puts data"""
    # Create a DataFrame with mock put options data
    puts_data = {
        'strike': [5100, 5150, 5200, 5250, 5300, 5350, 5400, 5450, 5500],
        'lastPrice': [6.0, 12.0, 22.0, 38.0, 62.0, 92.0, 126.0, 165.0, 210.0],
        'bid': [5.0, 10.0, 20.0, 36.0, 60.0, 90.0, 124.0, 163.0, 208.0],
        'ask': [7.0, 14.0, 24.0, 40.0, 64.0, 94.0, 128.0, 167.0, 212.0],
        'change': [-1.0, -1.5, -2.0, -2.5, -3.0, -3.5, -4.0, -4.5, -5.0],
        'percentChange': [-14.29, -11.11, -8.33, -6.17, -4.62, -3.67, -3.08, -2.66, -2.33],
        'volume': [100, 150, 200, 250, 300, 350, 400, 450, 500],
        'openInterest': [400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000],
        'impliedVolatility': [0.22, 0.21, 0.20, 0.19, 0.18, 0.17, 0.16, 0.15, 0.14],
        'delta': [-0.1, -0.2, -0.3, -0.4, -0.5, -0.6, -0.7, -0.8, -0.9],
        'gamma': [0.01, 0.015, 0.02, 0.025, 0.03, 0.025, 0.02, 0.015, 0.01],
        'theta': [-1.0, -1.2, -1.4, -1.6, -1.8, -1.6, -1.4, -1.2, -1.0],
        'vega': [1.0, 1.5, 2.0, 2.5, 3.0, 2.5, 2.0, 1.5, 1.0],
        'inTheMoney': [False, False, False, False, False, True, True, True, True],
    }
    return pd.DataFrame(puts_data)

@pytest.fixture
def mock_option_chain(mock_option_expiry_dates, mock_calls_data, mock_puts_data):
    """Fixture for complete mock option chain"""
    # Create a dictionary with expiry dates as keys and option chains as values
    option_chain = {}
    for expiry in mock_option_expiry_dates:
        # Add some random variation to each expiry's data
        calls = mock_calls_data.copy()
        puts = mock_puts_data.copy()
        
        # Adjust values slightly for each expiration
        days_to_expiry = (expiry - datetime.datetime.now().date()).days
        iv_adjustment = 1 + (days_to_expiry / 100)
        price_adjustment = 1 + (days_to_expiry / 200)
        
        calls['impliedVolatility'] = calls['impliedVolatility'] * iv_adjustment
        puts['impliedVolatility'] = puts['impliedVolatility'] * iv_adjustment
        
        calls['lastPrice'] = calls['lastPrice'] * price_adjustment
        puts['lastPrice'] = puts['lastPrice'] * price_adjustment
        calls['bid'] = calls['bid'] * price_adjustment
        puts['bid'] = puts['bid'] * price_adjustment
        calls['ask'] = calls['ask'] * price_adjustment
        puts['ask'] = puts['ask'] * price_adjustment
        
        option_chain[expiry] = {'calls': calls, 'puts': puts}
    
    return option_chain 