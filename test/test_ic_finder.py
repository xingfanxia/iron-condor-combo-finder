import pytest
import pandas as pd
import datetime
from unittest.mock import patch, MagicMock

from src.ic_finder import IronCondorFinder
from test.data_sources.mock_data_source import MockDataSource

@pytest.fixture
def patched_data_source(mock_spx_price, mock_option_chain):
    """Fixture that patches the create_data_source function to return our mock data source"""
    mock_ds = MockDataSource(mock_spx_price, mock_option_chain)
    
    # Create a patcher for the create_data_source function
    with patch('src.ic_finder.create_data_source', return_value=mock_ds) as patcher:
        yield patcher

@pytest.fixture
def patched_chart_generator():
    """Fixture that patches the ChartGenerator to avoid actually creating charts"""
    with patch('src.ic_finder.ChartGenerator') as mock:
        # Configure the mock to return a MagicMock when instantiated
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        
        # Configure the generate_chart method to return a dummy filename
        mock_instance.generate_chart.return_value = "charts/test_chart.png"
        
        yield mock_instance

@pytest.fixture
def ic_finder(patched_data_source, patched_chart_generator):
    """Fixture for an IronCondorFinder instance using our mocks"""
    finder = IronCondorFinder(
        symbol='SPX',
        max_move_pct=2.0,
        max_delta=0.01,
        min_dte=1,
        max_dte=7,
        min_liquidity=50,
        data_source='mock',  # The actual data source is mocked
        num_results=5,
        generate_charts=True
    )
    return finder

def test_init(ic_finder, mock_spx_price, mock_option_chain):
    """Test IronCondorFinder initialization"""
    # Check that parameters are set correctly
    assert ic_finder.symbol == 'SPX'
    assert ic_finder.max_move_pct == 2.0
    assert ic_finder.max_delta == 0.01
    assert ic_finder.min_dte == 1
    assert ic_finder.max_dte == 7
    assert ic_finder.min_liquidity == 50
    assert ic_finder.num_results == 5
    assert ic_finder.generate_charts == True
    
    # Check that components are initialized
    assert ic_finder.data_source_client is not None
    assert ic_finder.analysis is not None
    assert ic_finder.utils is not None

def test_calculate_price_range(ic_finder, mock_spx_price):
    """Test calculation of price range"""
    lower, upper = ic_finder._calculate_price_range(mock_spx_price)
    
    # For 2% move on SPX at 5300:
    expected_lower = mock_spx_price * (1 - 0.02)  # 5194
    expected_upper = mock_spx_price * (1 + 0.02)  # 5406
    
    assert abs(lower - expected_lower) < 0.01
    assert abs(upper - expected_upper) < 0.01

@patch('src.ic_finder.IronCondorFinder._find_iron_condors_for_expiry')
def test_find_iron_condors(mock_find_for_expiry, ic_finder, mock_option_chain):
    """Test the find_iron_condors method with mocked _find_iron_condors_for_expiry"""
    # Configure mock to return a list of fake iron condors
    mock_find_for_expiry.return_value = [
        {
            'expiry': list(mock_option_chain.keys())[0],
            'dte': 1,
            'short_put_strike': 5200,
            'long_put_strike': 5150,
            'short_call_strike': 5400,
            'long_call_strike': 5450,
            'net_credit': 4.5,
            'max_loss': 45.5,
            'position_delta': 0.005,
            'position_gamma': 0.002,
            'position_theta': 1.2,
            'position_vega': -0.3,
            'prob_profit': 0.65,
            'expected_profit': 1.75,
            'risk_reward': 10.1,
            'avg_spread': 0.04,
            'implied_volatility': 0.18,
            'chart_path': None
        },
        # Add a second mock iron condor with different values
    ]
    
    # Call the method
    results = ic_finder.find_iron_condors()
    
    # Check that the method returned the expected results
    assert len(results) > 0
    assert 'expiry' in results[0]
    assert 'net_credit' in results[0]
    assert 'prob_profit' in results[0]
    
    # Verify that the chart generation was called if generate_charts is True
    if ic_finder.generate_charts:
        assert 'chart_path' in results[0]

# We'll add more tests as we develop the IronCondorFinder class further 