class MockDataSource:
    """Mock data source for testing"""
    
    def __init__(self, mock_price, mock_option_chain):
        """Initialize with mock data
        
        Args:
            mock_price: Mock current price of the underlying
            mock_option_chain: Mock option chain data
        """
        self.mock_price = mock_price
        self.mock_option_chain = mock_option_chain
        self.symbol = "SPX"
    
    def get_current_price(self):
        """Get current price of the underlying
        
        Returns:
            float: Current price
        """
        return self.mock_price
    
    def get_options_chain(self, min_dte=None, max_dte=None):
        """Get options chain for the symbol
        
        Args:
            min_dte: Minimum days to expiration (optional)
            max_dte: Maximum days to expiration (optional)
            
        Returns:
            dict: Dictionary of options data by expiration date
        """
        # Filter by DTE if specified
        import datetime
        today = datetime.datetime.now().date()
        
        filtered_chain = {}
        for expiry, data in self.mock_option_chain.items():
            dte = (expiry - today).days
            
            # Apply DTE filters if specified
            if min_dte is not None and dte < min_dte:
                continue
            if max_dte is not None and dte > max_dte:
                continue
                
            filtered_chain[expiry] = data
        
        return filtered_chain 