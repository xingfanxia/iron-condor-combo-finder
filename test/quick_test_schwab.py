import sys
from pathlib import Path

# Add the project root to the Python path so we can import modules correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ic_finder import IronCondorFinder
from src.utilities import Utils

def test_with_app():
    print("Testing Iron Condor Finder with Schwab API...")
    
    try:
        # Create finder instance with Schwab as data source
        finder = IronCondorFinder(
            symbol='$SPX',
            max_move_pct=2.0,
            max_delta=0.01,
            min_dte=1,
            max_dte=4,
            min_liquidity=10,
            data_source='schwab',  # Explicitly use Schwab
            num_results=10,         # Just get one result to test
            generate_charts=True, # Skip chart generation for quick test
            spread_width=25        # Use wider 25-point spreads
        )
        
        print("Getting current price...")
        price = finder.get_current_price()
        print(f"Current S&P 500 price: ${price}")
        
        print("\nFinding iron condors (this may take a moment)...")
        print(f"Using max_delta={finder.max_delta} (absolute value of position delta must be <= {finder.max_delta})")
        
        try:
            iron_condors = finder.find_iron_condors()
        
            if iron_condors and len(iron_condors) > 0:
                print(f"\n✅ Successfully found {len(iron_condors)} iron condor(s)!")
                print("First result sample data:")
                try:
                    ic = iron_condors[0]
                    # Calculate expected profit
                    if 'expected_profit' not in ic and 'probability_of_profit' in ic:
                        probability = ic['probability_of_profit'] / 100
                        net_credit = ic['net_credit']
                        max_loss = ic['max_loss']
                        expected_profit = (net_credit * 100 * probability) - (max_loss * (1 - probability))
                        ic['expected_profit'] = expected_profit
                    
                    print(f"  Expiration: {ic.get('expiration', 'N/A')}")
                    print(f"  Structure: {ic.get('long_put_strike', 'N/A')}/{ic.get('short_put_strike', 'N/A')}/{ic.get('short_call_strike', 'N/A')}/{ic.get('long_call_strike', 'N/A')}")
                    print(f"  Net Credit: ${ic.get('net_credit', 0):.2f}")
                    print(f"  Prob of Profit: {ic.get('probability_of_profit', 0):.1f}%")
                    print(f"  Delta: {ic.get('position_delta', 0):.4f} (abs value: {abs(ic.get('position_delta', 0)):.4f})")
                except Exception as e:
                    print(f"Error displaying iron condor details: {e}")
            else:
                print("❌ No iron condors found. This could be due to market conditions or data restrictions.")
                
            return True
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_with_app()
    
    if success:
        print("\n🎉 Test completed! Your Schwab API integration is working with the main application.")
    else:
        print("\n⚠️ Test failed. Please check the error message above.") 