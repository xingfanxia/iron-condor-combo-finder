import pytest
import os
import pandas as pd
from unittest.mock import patch, mock_open

from src.utilities import Utils

@pytest.fixture
def mock_iron_condors():
    """Fixture for sample iron condor data list"""
    return [
        {
            'expiration': '2023-06-18',
            'dte': 3,
            'long_put_strike': 5150,
            'short_put_strike': 5200,
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
            'avg_spread_pct': 0.0004,
            'implied_volatility': 0.18,
            'chart_file': 'charts/test_chart.png'
        },
        {
            'expiration': '2023-06-25',
            'dte': 10,
            'long_put_strike': 5100,
            'short_put_strike': 5150,
            'short_call_strike': 5450,
            'long_call_strike': 5500,
            'net_credit': 5.2,
            'max_loss': 44.8,
            'position_delta': -0.002,
            'position_gamma': 0.001,
            'position_theta': 1.5,
            'position_vega': -0.4,
            'prob_profit': 0.62,
            'expected_profit': 1.5,
            'risk_reward': 8.6,
            'avg_spread_pct': 0.0005,
            'implied_volatility': 0.19,
            'chart_file': 'charts/test_chart2.png'
        }
    ]

@patch('pandas.DataFrame.to_csv')
def test_export_to_csv_with_auto_filename(mock_to_csv, mock_iron_condors):
    """Test exporting iron condors to CSV with auto-generated filename"""
    symbol = 'SPX'
    
    # Call the method with auto-generated filename
    filename = Utils.export_to_csv(mock_iron_condors, symbol)
    
    # Check that filename was generated correctly
    assert filename is not None
    assert symbol in filename
    assert filename.startswith('ic_opportunities_')
    assert filename.endswith('.csv')
    
    # Check that to_csv was called
    mock_to_csv.assert_called_once()

@patch('pandas.DataFrame.to_csv')
def test_export_to_csv_with_custom_filename(mock_to_csv, mock_iron_condors):
    """Test exporting iron condors to CSV with custom filename"""
    symbol = 'SPX'
    custom_filename = 'test_export.csv'
    
    # Call the method with custom filename
    filename = Utils.export_to_csv(mock_iron_condors, symbol, filename=custom_filename)
    
    # Check that the correct filename was returned
    assert filename == custom_filename
    
    # Check that to_csv was called with the custom filename
    mock_to_csv.assert_called_once_with(custom_filename, index=False)

def test_export_to_csv_empty_list():
    """Test exporting empty iron condor list"""
    symbol = 'SPX'
    
    # Call the method with empty list
    filename = Utils.export_to_csv([], symbol)
    
    # Should return None when list is empty
    assert filename is None

def test_format_iron_condor_output(mock_iron_condors):
    """Test formatting iron condor for console output"""
    ic = mock_iron_condors[0]
    index = 1
    
    # Test with chart
    output_with_chart = Utils.format_iron_condor_output(ic, index, include_chart=True)
    assert isinstance(output_with_chart, str)
    assert f"#{index+1}" in output_with_chart
    assert str(ic['expiration']) in output_with_chart
    assert str(ic['net_credit']) in output_with_chart
    assert str(ic['prob_profit']) in output_with_chart
    assert "chart_file" in output_with_chart
    
    # Test without chart
    output_without_chart = Utils.format_iron_condor_output(ic, index, include_chart=False)
    assert isinstance(output_without_chart, str)
    assert "chart_file" not in output_without_chart 