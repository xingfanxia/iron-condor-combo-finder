import pytest
import os
import tempfile
import numpy as np
from unittest.mock import patch, MagicMock

from src.visualization import ChartGenerator

@pytest.fixture
def chart_generator():
    """Fixture for chart generator with a temporary output directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield ChartGenerator(output_dir=temp_dir)

@pytest.fixture
def mock_iron_condor_data():
    """Fixture for sample iron condor data"""
    return {
        'long_put_strike': 5150,
        'short_put_strike': 5200,
        'short_call_strike': 5400,
        'long_call_strike': 5450,
        'net_credit': 4.5,
        'max_loss': 45.5,
        'prob_profit': 0.65,
        'expiration': '2023-06-18',
        'dte': 3,
        'position_delta': 0.005,
        'position_gamma': 0.002,
        'position_theta': 1.2,
        'position_vega': -0.3,
        'expected_profit': 1.75,
        'risk_reward': 10.1,
        'avg_spread_pct': 0.0004,
        'implied_volatility': 0.18
    }

def test_init(chart_generator):
    """Test initialization of ChartGenerator"""
    assert chart_generator.output_dir is not None
    assert os.path.exists(chart_generator.output_dir)

@patch('matplotlib.pyplot.savefig')
@patch('matplotlib.pyplot.close')
@patch('matplotlib.pyplot.fill_between')
@patch('numpy.linspace', return_value=np.array([1, 2, 3]))
@patch('src.visualization.ChartGenerator.calculate_profits', return_value=np.array([10, -5, 15]))
def test_generate_iron_condor_chart(mock_calc_profits, mock_linspace, mock_fill_between, 
                                  mock_close, mock_savefig, chart_generator, mock_iron_condor_data):
    """Test generation of iron condor chart with mocked numpy operations"""
    current_price = 5300.0
    
    # Call the method
    filename = chart_generator.generate_iron_condor_chart(mock_iron_condor_data, current_price)
    
    # Check that the method returns a filename
    assert filename is not None
    assert isinstance(filename, str)
    assert filename.endswith('.png')
    
    # Check that savefig was called
    mock_savefig.assert_called_once()
    
    # Check that close was called to avoid memory leaks
    mock_close.assert_called_once()
    
    # Check that the numpy array operations were called
    mock_linspace.assert_called_once()
    mock_calc_profits.assert_called_once()

@patch('matplotlib.pyplot.savefig')
@patch('matplotlib.pyplot.close')
@patch('matplotlib.pyplot.fill_between')
@patch('numpy.linspace', return_value=np.array([1, 2, 3]))
@patch('src.visualization.ChartGenerator.calculate_profits', return_value=np.array([10, -5, 15]))
def test_generate_iron_condor_chart_with_custom_filename(
    mock_calc_profits, mock_linspace, mock_fill_between, mock_close, mock_savefig, 
    chart_generator, mock_iron_condor_data
):
    """Test generation of iron condor chart with custom filename"""
    current_price = 5300.0
    custom_filename = "custom_test_chart.png"
    
    # Call the method with custom filename
    filename = chart_generator.generate_iron_condor_chart(
        mock_iron_condor_data, current_price, filename=custom_filename
    )
    
    # Check that the method returns the custom filename
    assert filename == os.path.join(chart_generator.output_dir, custom_filename)
    
    # Check that savefig was called with the custom filename
    mock_savefig.assert_called_once()
    
    # Check that close was called to avoid memory leaks
    mock_close.assert_called_once() 