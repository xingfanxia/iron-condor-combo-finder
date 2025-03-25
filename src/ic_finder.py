import pandas as pd
import datetime
import os
from dotenv import load_dotenv

# Import modules
from src.data_sources import create_data_source
from src.analysis import OptionsAnalysis
from src.visualization import ChartGenerator
from src.utilities import Utils

# Load environment variables
load_dotenv()

class IronCondorFinder:
    """
    Main class for finding optimal iron condor options combinations
    that are delta neutral and bet against specific percentage moves
    """
    
    def __init__(self, symbol='$SPX', max_move_pct=2.0, max_delta=0.01, 
                 min_dte=1, max_dte=1, min_liquidity=50, data_source='schwab',
                 num_results=5, generate_charts=True, spread_width=25):
        """
        Initialize the Iron Condor finder
        
        Parameters:
        symbol (str): The underlying symbol to trade
        max_move_pct (float): Maximum expected move (in %) we're betting against
        max_delta (float): Maximum acceptable overall position delta
        min_dte (int): Minimum days to expiration
        max_dte (int): Maximum days to expiration
        min_liquidity (int): Minimum volume for options to consider
        data_source (str): Data source to use - 'schwab', 'yahoo', or 'cboe'
        num_results (int): Number of top results to display
        generate_charts (bool): Whether to generate P/L charts
        spread_width (int): Width between short and long legs in points (default: 25)
        """
        self.symbol = symbol
        self.max_move_pct = max_move_pct
        self.max_delta = max_delta
        self.min_dte = min_dte
        self.max_dte = max_dte
        self.min_liquidity = min_liquidity
        self.data_source = data_source
        self.num_results = num_results
        self.generate_charts = generate_charts
        self.spread_width = spread_width
        
        # Initialize components
        self.data_source_client = create_data_source(
            data_source, symbol, min_dte, max_dte, min_liquidity
        )
        self.analysis = OptionsAnalysis()
        self.chart_generator = ChartGenerator('charts') if generate_charts else None
    
    def get_current_price(self):
        """Get current price of the underlying asset"""
        return self.data_source_client.get_current_price()
    
    def find_iron_condors(self):
        """Find iron condor combinations that meet our criteria"""
        # Get current price
        current_price = self.get_current_price()
        
        if not current_price:
            raise ValueError("Could not determine current price")
            
        try:
            # Get options chain data
            options_data = self.data_source_client.get_option_chain()
        except Exception as e:
            print(f"Error getting options data: {e}")
            print("Attempting to use Yahoo Finance data as fallback...")
            self.data_source = 'yahoo'
            self.data_source_client = create_data_source(
                'yahoo', self.symbol, self.min_dte, self.max_dte, self.min_liquidity
            )
            options_data = self.data_source_client.get_option_chain()
        
        print(f"Current {self.symbol} price: ${current_price:.2f}")
        
        # Calculate price range we're betting within
        lower_bound, upper_bound = Utils.get_strike_ranges(current_price, self.max_move_pct)
        
        # Calculate date ranges for clarity
        today = datetime.datetime.now().date()
        min_date = today + datetime.timedelta(days=self.min_dte)
        max_date = today + datetime.timedelta(days=self.max_dte)
        
        print(f"Looking for iron condors with expiration between {min_date} and {max_date} (DTE: {self.min_dte}-{self.max_dte})")
        print(f"Targeting price range between ${lower_bound:.2f} and ${upper_bound:.2f} (±{self.max_move_pct}%)")
        print(f"Using {self.spread_width}-point spreads between short and long legs")
        
        # Find iron condors using analysis module
        iron_condors = self.analysis.find_iron_condors(
            options_data=options_data,
            current_price=current_price,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            min_dte=self.min_dte,
            max_dte=self.max_dte,
            min_liquidity=self.min_liquidity,
            max_delta=self.max_delta,
            spread_width=self.spread_width
        )
        
        # If no iron condors were found, try again with relaxed delta constraint
        if not iron_condors:
            print("\nNo iron condors found with standard criteria. Trying with relaxed delta constraint...")
            iron_condors = self.analysis.find_iron_condors(
                options_data=options_data,
                current_price=current_price,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                min_dte=self.min_dte,
                max_dte=self.max_dte,
                min_liquidity=self.min_liquidity,
                max_delta=0.05,  # Relaxed delta constraint
                spread_width=self.spread_width  # Use the same spread width
            )
        
        # Generate charts if requested
        if self.generate_charts and iron_condors and self.chart_generator:
            chart_files = self.chart_generator.generate_multiple_charts(
                iron_condors[:self.num_results], current_price
            )
            
            # Add chart file paths to iron condor data
            for i, chart_file in enumerate(chart_files):
                if i < len(iron_condors):
                    iron_condors[i]['chart_file'] = chart_file
        
        # Print top results
        if iron_condors:
            print(f"\nTop {min(self.num_results, len(iron_condors))} Iron Condor Opportunities:")
            print("-" * 50)
            
            for i, ic in enumerate(iron_condors[:self.num_results]):
                # Calculate expected profit for each iron condor 
                if 'expected_profit' not in ic:
                    ic['expected_profit'] = Utils.calculate_expected_profit(ic)
                    
                print(Utils.format_iron_condor_output(ic, i))
                print()
                
            # Check if user wants to see all candidates
            if self.num_results < len(iron_condors):
                print(f"\nAdditional {len(iron_condors) - self.num_results} candidates found.")
                print("To see all candidates, set num_results parameter higher or run with --show-all flag")
        
        return iron_condors
    
    def export_results(self, iron_condors):
        """Export iron condors to CSV file"""
        return Utils.export_to_csv(iron_condors, self.symbol)


def main():
    # Create an iron condor finder
    finder = IronCondorFinder(
        symbol='$SPX',
        max_move_pct=2.0,
        max_delta=0.01,
        min_dte=1,
        max_dte=4,
        min_liquidity=50,
        data_source='schwab',  # Options: 'schwab', 'yahoo', 'cboe'
        num_results=5,         # Number of results to display
        generate_charts=True,  # Generate P/L charts
        spread_width=25        # 25-point spread between short and long legs
    )
    
    # Find the best iron condors
    try:
        iron_condors = finder.find_iron_condors()
        if iron_condors:
            finder.export_results(iron_condors)
    except Exception as e:
        print(f"Error finding iron condors: {e}")
        print("Attempting to use Yahoo Finance data instead...")
        
        # Use the Yahoo Finance data instead
        finder.data_source = 'yahoo'
        finder.data_source_client = create_data_source(
            'yahoo', finder.symbol, finder.min_dte, finder.max_dte, finder.min_liquidity
        )
        try:
            iron_condors = finder.find_iron_condors()
            if iron_condors:
                finder.export_results(iron_condors)
        except Exception as e:
            print(f"Fatal error: {e}")
            print("Could not find suitable iron condors with any data source.")


if __name__ == "__main__":
    main() 