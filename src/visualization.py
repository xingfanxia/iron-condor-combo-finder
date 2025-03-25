import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import datetime

class ChartGenerator:
    """Class for generating profit/loss charts for options strategies"""
    
    def __init__(self, output_dir='charts'):
        """Initialize chart generator"""
        self.output_dir = output_dir
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def calculate_profits(self, prices, long_put_strike, short_put_strike, short_call_strike, long_call_strike, net_credit):
        """Calculate profit/loss for each price point
        
        This method is separated to allow patching during testing
        """
        profits = []
        for price in prices:
            # Long put payout
            if price <= long_put_strike:
                long_put_profit = long_put_strike - price
            else:
                long_put_profit = 0
    
            # Short put payout
            if price <= short_put_strike:
                short_put_profit = -(short_put_strike - price)
            else:
                short_put_profit = 0
    
            # Short call payout
            if price >= short_call_strike:
                short_call_profit = -(price - short_call_strike)
            else:
                short_call_profit = 0
    
            # Long call payout
            if price >= long_call_strike:
                long_call_profit = price - long_call_strike
            else:
                long_call_profit = 0
    
            # Total profit (include credit received)
            total_profit = (long_put_profit + short_put_profit +
                           short_call_profit + long_call_profit +
                           net_credit) * 100
    
            profits.append(total_profit)
            
        return np.array(profits)
    
    def generate_iron_condor_chart(self, ic_data, current_price, filename=None):
        """Generate profit/loss chart for an iron condor"""
        # Extract strike prices
        long_put_strike = ic_data['long_put_strike']
        short_put_strike = ic_data['short_put_strike']
        short_call_strike = ic_data['short_call_strike']
        long_call_strike = ic_data['long_call_strike']
        net_credit = ic_data['net_credit']
        
        # Generate price range for x-axis
        price_range_low = max(long_put_strike * 0.9, current_price * 0.8)
        price_range_high = min(long_call_strike * 1.1, current_price * 1.2)
        prices = np.linspace(price_range_low, price_range_high, 1000)
        
        # Calculate P/L for each price point
        profits = self.calculate_profits(prices, long_put_strike, short_put_strike, 
                                        short_call_strike, long_call_strike, net_credit)
        
        # Create plot
        plt.figure(figsize=(10, 6))
        sns.set_style('whitegrid')
        
        # Plot P/L curve
        plt.plot(prices, profits, 'b-', linewidth=2)
        
        # Add horizontal line at y=0
        plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
        
        # Add vertical lines at key price points
        plt.axvline(x=current_price, color='g', linestyle='--', label=f'Current: ${current_price:.2f}')
        plt.axvline(x=long_put_strike, color='gray', linestyle=':', alpha=0.7)
        plt.axvline(x=short_put_strike, color='gray', linestyle=':', alpha=0.7)
        plt.axvline(x=short_call_strike, color='gray', linestyle=':', alpha=0.7)
        plt.axvline(x=long_call_strike, color='gray', linestyle=':', alpha=0.7)
        
        # Add shaded area for profitable region
        plt.fill_between(prices, 0, profits, where=(profits > 0), color='green', alpha=0.3)
        plt.fill_between(prices, 0, profits, where=(profits <= 0), color='red', alpha=0.3)
        
        # Label strikes
        plt.annotate(f'Long Put: ${long_put_strike:.2f}', xy=(long_put_strike, min(profits)/2),
                     xytext=(-30, 30), textcoords='offset points', rotation=90,
                     arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        plt.annotate(f'Short Put: ${short_put_strike:.2f}', xy=(short_put_strike, min(profits)/2),
                     xytext=(-30, 30), textcoords='offset points', rotation=90,
                     arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        plt.annotate(f'Short Call: ${short_call_strike:.2f}', xy=(short_call_strike, min(profits)/2),
                     xytext=(-30, 30), textcoords='offset points', rotation=90,
                     arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        plt.annotate(f'Long Call: ${long_call_strike:.2f}', xy=(long_call_strike, min(profits)/2),
                     xytext=(-30, 30), textcoords='offset points', rotation=90,
                     arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        # Add title and labels
        plt.title(f'Iron Condor P/L at Expiration - {ic_data.get("expiration", "")}', fontsize=14)
        plt.xlabel('Price of Underlying at Expiration', fontsize=12)
        plt.ylabel('Profit/Loss ($)', fontsize=12)
        
        # Add profit metrics as text
        # Calculate max profit and collateral
        max_profit = net_credit * 100
        max_width = max(long_call_strike - short_call_strike, short_put_strike - long_put_strike)
        collateral = max_width * 100 - max_profit
        
        text = plt.text(0.05, 0.05, 
                  f'Iron Condor: {long_put_strike} / {short_put_strike} / {short_call_strike} / {long_call_strike}\n'
                  f'Expiration: {ic_data["expiration"]} (DTE: {ic_data["dte"]})\n'
                  f'Current Price: ${current_price:.2f}\n'
                  f'Net Credit: ${net_credit:.2f}\n'
                  f'Max Loss: ${ic_data["max_loss"]:.2f}\n'
                  f'Max Profit: ${max_profit:.2f} | Collateral: ${collateral:.2f}\n'
                  f'P(Profit): {ic_data["probability_of_profit"]:.1f}%\n'
                  f'Expected Profit: ${ic_data["expected_profit"]:.2f}',
                  transform=plt.gca().transAxes, fontsize=10,
                  bbox=dict(facecolor='white', alpha=0.7))
        
        # Add legend
        plt.legend()
        
        # Set tight layout
        plt.tight_layout()
        
        # Generate filename if not provided
        if not filename:
            expiry_str = ic_data.get("expiration", "").replace("-", "")
            strikes_str = f"{long_put_strike}_{short_put_strike}_{short_call_strike}_{long_call_strike}"
            filename = f"ic_{expiry_str}_{strikes_str}.png"
        
        # Save the chart
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def generate_comparison_chart(self, iron_condors, current_price, filename=None):
        """Generate chart comparing multiple iron condors"""
        if not iron_condors:
            return None
            
        plt.figure(figsize=(12, 8))
        sns.set_style('whitegrid')
        
        # Determine price range based on all iron condors
        min_strike = min([ic['long_put_strike'] for ic in iron_condors])
        max_strike = max([ic['long_call_strike'] for ic in iron_condors])
        
        price_range_low = max(min_strike * 0.9, current_price * 0.8)
        price_range_high = min(max_strike * 1.1, current_price * 1.2)
        prices = np.linspace(price_range_low, price_range_high, 1000)
        
        # Plot each iron condor
        for i, ic in enumerate(iron_condors[:5]):  # Limit to 5 for clarity
            long_put_strike = ic['long_put_strike']
            short_put_strike = ic['short_put_strike']
            short_call_strike = ic['short_call_strike']
            long_call_strike = ic['long_call_strike']
            net_credit = ic['net_credit']
            
            # Calculate P/L for this iron condor
            profits = self.calculate_profits(prices, long_put_strike, short_put_strike, 
                                          short_call_strike, long_call_strike, net_credit)
            
            # Plot with distinct color
            plt.plot(prices, profits, 
                    label=f'#{i+1}: {short_put_strike}/{short_call_strike} (${net_credit:.2f})',
                    linewidth=2)
            
        # Add current price line
        plt.axvline(x=current_price, color='black', linestyle='--', label=f'Current: ${current_price:.2f}')
        
        # Add break-even horizontal line
        plt.axhline(y=0, color='red', linestyle='-', alpha=0.3)
        
        # Add title and labels
        plt.title('Iron Condor Comparison - P/L at Expiration', fontsize=14)
        plt.xlabel('Price of Underlying at Expiration', fontsize=12)
        plt.ylabel('Profit/Loss ($)', fontsize=12)
        
        # Add legend
        plt.legend(title="Iron Condors", loc='upper right')
        
        # Set tight layout
        plt.tight_layout()
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"ic_comparison_{timestamp}.png"
        
        # Save the chart
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath

    def generate_multiple_charts(self, iron_condors, current_price, max_charts=None):
        """Generate charts for multiple iron condors"""
        chart_files = []
        
        # Limit the number of charts if specified
        if max_charts:
            iron_condors = iron_condors[:max_charts]
            
        for ic in iron_condors:
            chart_file = self.generate_iron_condor_chart(ic, current_price)
            chart_files.append(chart_file)
            
        return chart_files 