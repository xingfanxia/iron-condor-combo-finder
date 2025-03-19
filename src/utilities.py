import pandas as pd
import datetime
import os

class Utils:
    """Utility functions for options strategies"""
    
    @staticmethod
    def export_to_csv(iron_condors, symbol, filename=None):
        """Export iron condors to CSV file"""
        if not iron_condors:
            print("No iron condors to export")
            return None
            
        if filename is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"ic_opportunities_{symbol}_{timestamp}.csv"
            
        try:
            df = pd.DataFrame(iron_condors)
            df.to_csv(filename, index=False)
            print(f"Exported {len(iron_condors)} iron condors to {filename}")
            return filename
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return None
    
    @staticmethod
    def format_iron_condor_output(ic, index, include_chart=True):
        """Format iron condor for console output"""
        output = []
        output.append(f"#{index+1} - Expiration: {ic['expiration']} (DTE: {ic['dte']})")
        output.append(f"Structure: {ic['long_put_strike']}/{ic['short_put_strike']}/{ic['short_call_strike']}/{ic['long_call_strike']}")
        output.append(f"Net Credit: ${ic['net_credit']:.2f} | Max Loss: ${ic['max_loss']:.2f}")
        output.append(f"Expected Profit: ${ic['expected_profit']:.2f} | Prob of Profit: {ic['prob_profit']*100:.1f}%")
        output.append(f"Greeks - Delta: {ic['position_delta']:.4f} | Gamma: {ic['position_gamma']:.4f} | Theta: ${ic['position_theta']:.2f} | Vega: {ic['position_vega']:.4f}")
        output.append(f"Risk/Reward: {ic['risk_reward']:.2f} | Avg Spread: {ic['avg_spread_pct']*100:.2f}%")
        output.append(f"Implied Volatility: {ic['implied_volatility']*100:.1f}%")
        
        if include_chart and 'chart_file' in ic:
            output.append(f"P/L chart saved: {ic['chart_file']}")
            
        return '\n'.join(output)
    
    @staticmethod
    def sort_iron_condors(iron_condors, sort_method="risk_reward"):
        """Sort iron condors by specified method"""
        if not iron_condors:
            return []
            
        if sort_method == "expected_profit":
            return sorted(iron_condors, key=lambda x: x['expected_profit'], reverse=True)
        elif sort_method == "probability":
            return sorted(iron_condors, key=lambda x: x['prob_profit'], reverse=True)
        else:  # Default to risk/reward (lowest first)
            return sorted(iron_condors, key=lambda x: x['risk_reward'])
    
    @staticmethod
    def get_strike_ranges(current_price, max_move_pct):
        """Calculate the lower and upper bounds for a given max move percentage"""
        lower_bound = current_price * (1 - max_move_pct/100)
        upper_bound = current_price * (1 + max_move_pct/100)
        return lower_bound, upper_bound
    
    @staticmethod
    def validate_file_path(path):
        """Validate and create directory if needed for a file path"""
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory)
                return True
            except Exception as e:
                print(f"Error creating directory {directory}: {e}")
                return False
        return True 