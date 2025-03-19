"""Factory function for creating data sources"""

from .schwab import SchwabDataSource
from .cboe import CBOEDataSource
from .yahoo import YahooDataSource
from .ib import IBDataSource


def create_data_source(source_type, symbol, min_dte, max_dte, min_liquidity):
    """Factory function to create the appropriate data source
    
    Args:
        source_type (str): Type of data source ('schwab', 'ib', 'cboe', or 'yahoo')
        symbol (str): Symbol to fetch data for
        min_dte (int): Minimum days to expiration
        max_dte (int): Maximum days to expiration
        min_liquidity (int): Minimum option volume to consider
        
    Returns:
        DataSourceBase: An instance of the appropriate data source class
    """
    if source_type == 'schwab':
        return SchwabDataSource(symbol, min_dte, max_dte, min_liquidity)
    elif source_type == 'ib':
        return IBDataSource(symbol, min_dte, max_dte, min_liquidity)
    elif source_type == 'cboe':
        return CBOEDataSource(symbol, min_dte, max_dte, min_liquidity)
    else:  # Default to Yahoo
        return YahooDataSource(symbol, min_dte, max_dte, min_liquidity) 