import pytest
import datetime

from test.data_sources.mock_data_source import MockDataSource

def test_mock_data_source_initialization(mock_spx_price, mock_option_chain):
    """Test that the mock data source can be initialized correctly"""
    ds = MockDataSource(mock_spx_price, mock_option_chain)
    assert ds.symbol == "SPX"
    assert ds.mock_price == mock_spx_price
    assert ds.mock_option_chain == mock_option_chain

def test_get_current_price(mock_spx_price, mock_option_chain):
    """Test getting current price from mock data source"""
    ds = MockDataSource(mock_spx_price, mock_option_chain)
    price = ds.get_current_price()
    assert price == mock_spx_price

def test_get_options_chain_no_filters(mock_spx_price, mock_option_chain):
    """Test getting full options chain without date filters"""
    ds = MockDataSource(mock_spx_price, mock_option_chain)
    options = ds.get_options_chain()
    
    # Should return all expiry dates
    assert len(options) == len(mock_option_chain)
    
    # Check that the data structure is correct
    for expiry, data in options.items():
        assert 'calls' in data
        assert 'puts' in data
        assert 'strike' in data['calls'].columns
        assert 'delta' in data['calls'].columns
        assert 'strike' in data['puts'].columns
        assert 'delta' in data['puts'].columns

def test_get_options_chain_with_dte_filters(mock_spx_price, mock_option_chain):
    """Test getting options chain with DTE filters"""
    ds = MockDataSource(mock_spx_price, mock_option_chain)
    
    today = datetime.datetime.now().date()
    
    # Test min_dte filter
    min_dte = 5
    options_min = ds.get_options_chain(min_dte=min_dte)
    
    for expiry in options_min.keys():
        dte = (expiry - today).days
        assert dte >= min_dte
    
    # Test max_dte filter
    max_dte = 10
    options_max = ds.get_options_chain(max_dte=max_dte)
    
    for expiry in options_max.keys():
        dte = (expiry - today).days
        assert dte <= max_dte
    
    # Test both filters
    options_both = ds.get_options_chain(min_dte=5, max_dte=20)
    
    for expiry in options_both.keys():
        dte = (expiry - today).days
        assert 5 <= dte <= 20 