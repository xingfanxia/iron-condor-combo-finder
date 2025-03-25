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
        
        # Format the structure showing the short strikes clearly
        output.append(f"Structure: {ic['long_put_strike']} / [{ic['short_put_strike']}] / [{ic['short_call_strike']}] / {ic['long_call_strike']}")
        
        # Add percent distance from current price
        if 'put_distance_pct' in ic and 'call_distance_pct' in ic:
            target = 2.0  # Our 2% target
            put_distance = ic['put_distance_pct']
            call_distance = ic['call_distance_pct']
            
            # Indicate how close we are to the 2% target with symbols
            put_indicator = "✓" if abs(put_distance - target) < 0.3 else "⚠️"
            call_indicator = "✓" if abs(call_distance - target) < 0.3 else "⚠️"
            
            output.append(f"Target: 2% range | Actual: Short Put {put_indicator} {put_distance:.2f}% below, " +
                          f"Short Call {call_indicator} {call_distance:.2f}% above")
        elif 'current_price' in ic or ('risk_reward' in ic and ic['net_credit'] > 0):
            # Calculate based on available data
            if 'current_price' in ic:
                current_price = ic['current_price']
            else:
                # Estimate current price from risk_reward ratio
                current_price = ic['max_loss'] / (ic['risk_reward'] * ic['net_credit'])
                
            if current_price > 0:
                put_pct = ((current_price - ic['short_put_strike']) / current_price) * 100
                call_pct = ((ic['short_call_strike'] - current_price) / current_price) * 100
                output.append(f"Distance: Short Put {put_pct:.2f}% below | Short Call {call_pct:.2f}% above")
        
        # Financial information
        output.append(f"Net Credit: ${ic['net_credit']:.2f} | Max Loss: ${ic['max_loss']:.2f}")
        
        # Add max profit and collateral
        max_profit = ic['net_credit'] * 100
        max_width = max(ic['put_width'], ic['call_width'])
        collateral = max_width * 100 - max_profit
        output.append(f"Max Profit: ${max_profit:.2f} | Collateral: ${collateral:.2f}")
        
        # Profitability metrics
        if ic['probability_of_profit'] >= 60:
            prob_indicator = "✓"
        elif ic['probability_of_profit'] >= 40:
            prob_indicator = "⚠️"
        else:
            prob_indicator = "❌"
            
        output.append(f"Expected Profit: ${ic['expected_profit']:.2f} | Prob of Profit: {prob_indicator} {ic['probability_of_profit']:.1f}%")
        
        # Greeks - briefly formatted
        output.append(f"Greeks - Delta: {ic['position_delta']:.4f} | Gamma: {ic['position_gamma']:.4f} | Theta: ${ic['position_theta']:.2f}")
        
        # Risk metrics
        output.append(f"Risk/Reward: {ic['risk_reward']:.2f} | Put Width: {ic['put_width']} | Call Width: {ic['call_width']}")
        
        # Format volatility appropriately
        volatility = ic['implied_volatility']
        if volatility > 1:  # If still stored as percentage rather than decimal
            volatility = volatility / 100.0
        output.append(f"Implied Volatility: {volatility*100:.1f}%")
        
        if 'strategy_score' in ic:
            output.append(f"Strategy Score: {ic['strategy_score']:.2f} (higher is better)")
        
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
            return sorted(iron_condors, key=lambda x: x['probability_of_profit'], reverse=True)
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
    
    @staticmethod
    def calculate_expected_profit(iron_condor):
        """Calculate expected profit from iron condor data"""
        net_credit = iron_condor.get('net_credit', 0)
        max_loss = iron_condor.get('max_loss', 0)
        probability = iron_condor.get('probability_of_profit', 0) / 100  # Convert from percentage
        
        # Expected value = (profit * probability of profit) + (loss * probability of loss)
        expected_profit = (net_credit * 100 * probability) - (max_loss * (1 - probability))
        return expected_profit 