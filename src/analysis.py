import math
from scipy.stats import norm

class OptionsAnalysis:
    """Class for options analysis functions"""
    
    def __init__(self, risk_free_rate=0.05):
        """Initialize with risk-free rate"""
        self.risk_free_rate = risk_free_rate
    
    def calculate_probability_of_profit(self, current_price, short_put_strike, short_call_strike, 
                                      days_to_expiration, volatility):
        """
        Calculate probability of profit for an iron condor
        
        This uses the Black-Scholes model to estimate the probability that the 
        underlying price will remain between the short strikes at expiration
        """
        # Annual volatility to daily
        daily_volatility = volatility / math.sqrt(252)
        
        # Standard deviation of price movement over the period
        std_dev = current_price * daily_volatility * math.sqrt(days_to_expiration)
        
        # Calculate probability using normal CDF
        prob_below_call = norm.cdf(
            (math.log(short_call_strike / current_price) + 
             (self.risk_free_rate - 0.5 * volatility**2) * days_to_expiration/365) / 
            (volatility * math.sqrt(days_to_expiration/365))
        )
        
        prob_above_put = 1 - norm.cdf(
            (math.log(short_put_strike / current_price) + 
             (self.risk_free_rate - 0.5 * volatility**2) * days_to_expiration/365) / 
            (volatility * math.sqrt(days_to_expiration/365))
        )
        
        # Probability that price stays between short put and short call
        return prob_below_call - prob_above_put
    
    def calculate_expected_profit(self, net_credit, max_loss, prob_profit):
        """Calculate expected profit based on probability of profit"""
        # Expected value = (profit * probability of profit) + (loss * probability of loss)
        expected_profit = (net_credit * 100 * prob_profit) - (max_loss * (1 - prob_profit))
        return expected_profit
    
    def find_iron_condors(self, options_data, current_price, lower_bound, upper_bound, 
                         min_dte, max_dte, min_liquidity, max_delta=0.01):
        """Find iron condor combinations that meet the criteria"""
        # Process options data
        iron_condors = []
        
        if not options_data.get('callExpDateMap') or not options_data.get('putExpDateMap'):
            print("Error: No options data available")
            return []
        
        for expiration in options_data['callExpDateMap']:
            # Parse expiration and DTE
            exp_date = expiration.split(':')[0]
            try:
                from datetime import datetime
                dte = (datetime.strptime(exp_date, '%Y-%m-%d') - datetime.now()).days
            except ValueError:
                print(f"Error parsing expiration date {exp_date}")
                continue
            
            if not (min_dte <= dte <= max_dte):
                continue
                
            call_options = []
            put_options = []
            
            # Process calls
            for strike in options_data['callExpDateMap'][expiration]:
                try:
                    option = options_data['callExpDateMap'][expiration][strike][0]
                    
                    # Filter by basic liquidity
                    if option.get('totalVolume', 0) < min_liquidity:
                        continue
                        
                    call_options.append({
                        'strike': float(strike),
                        'bid': option.get('bid', 0),
                        'ask': option.get('ask', 0),
                        'delta': option.get('delta', 0.5),
                        'gamma': option.get('gamma', 0.01),
                        'theta': option.get('theta', -0.01),
                        'vega': option.get('vega', 0.1),
                        'volume': option.get('totalVolume', 0),
                        'open_interest': option.get('openInterest', 0),
                        'spread': option.get('ask', 0) - option.get('bid', 0),
                        'volatility': option.get('volatility', 0.2)
                    })
                except (ValueError, IndexError) as e:
                    print(f"Error processing call option at strike {strike}: {e}")
                    continue
            
            # Process puts
            for strike in options_data['putExpDateMap'].get(expiration, {}):
                try:
                    option = options_data['putExpDateMap'][expiration][strike][0]
                    
                    # Filter by basic liquidity
                    if option.get('totalVolume', 0) < min_liquidity:
                        continue
                        
                    put_options.append({
                        'strike': float(strike),
                        'bid': option.get('bid', 0),
                        'ask': option.get('ask', 0),
                        'delta': option.get('delta', 0),  # This will be negative for puts
                        'gamma': option.get('gamma', 0.01),
                        'theta': option.get('theta', -0.01),
                        'vega': option.get('vega', 0.1),
                        'volume': option.get('totalVolume', 0),
                        'open_interest': option.get('openInterest', 0),
                        'spread': option.get('ask', 0) - option.get('bid', 0),
                        'volatility': option.get('volatility', 0.2)
                    })
                except (ValueError, IndexError) as e:
                    print(f"Error processing put option at strike {strike}: {e}")
                    continue
            
            if not call_options or not put_options:
                print(f"Not enough valid options for expiration {exp_date}")
                continue
            
            # Sort options
            call_options.sort(key=lambda x: x['strike'])
            put_options.sort(key=lambda x: x['strike'])
            
            # Find potential iron condors
            for i in range(len(put_options) - 1):
                if put_options[i]['strike'] >= lower_bound:
                    break
                    
                for j in range(len(call_options) - 1):
                    if call_options[j]['strike'] <= upper_bound:
                        continue
                        
                    # Create potential iron condor
                    # Long put, short put, short call, long call
                    long_put = put_options[i]
                    short_put = put_options[i + 1]
                    short_call = call_options[j]
                    long_call = call_options[j + 1]
                    
                    # Skip if any option has zero bid/ask
                    if (long_put['ask'] <= 0 or short_put['bid'] <= 0 or
                        short_call['bid'] <= 0 or long_call['ask'] <= 0):
                        continue
                    
                    # Calculate key metrics
                    net_credit = (short_put['bid'] - long_put['ask'] + 
                                  short_call['bid'] - long_call['ask'])
                    
                    # Skip negative credit spreads
                    if net_credit <= 0:
                        continue
                    
                    # Width of spreads
                    put_width = short_put['strike'] - long_put['strike']
                    call_width = long_call['strike'] - short_call['strike']
                    
                    # Max loss (assuming equal width spreads)
                    max_loss = max(put_width, call_width) * 100 - (net_credit * 100)
                    
                    # Combine volatility from all legs (weighted average)
                    avg_vol = (
                        long_put.get('volatility', 0.2) +
                        short_put.get('volatility', 0.2) +
                        short_call.get('volatility', 0.2) +
                        long_call.get('volatility', 0.2)
                    ) / 4
                    
                    # Calculate probability of profit
                    prob_profit = self.calculate_probability_of_profit(
                        current_price=current_price,
                        short_put_strike=short_put['strike'],
                        short_call_strike=short_call['strike'],
                        days_to_expiration=dte,
                        volatility=avg_vol
                    )
                    
                    # Calculate overall position delta
                    position_delta = (long_put['delta'] + short_put['delta'] + 
                                      short_call['delta'] + long_call['delta'])
                    
                    # Calculate overall Greeks
                    position_gamma = (long_put['gamma'] + short_put['gamma'] + 
                                     short_call['gamma'] + long_call['gamma'])
                    position_theta = (long_put['theta'] + short_put['theta'] + 
                                     short_call['theta'] + long_call['theta'])
                    position_vega = (long_put['vega'] + short_put['vega'] + 
                                    short_call['vega'] + long_call['vega'])
                    
                    # Calculate expected profit
                    expected_profit = self.calculate_expected_profit(
                        net_credit=net_credit,
                        max_loss=max_loss,
                        prob_profit=prob_profit
                    )
                    
                    # Filter by delta neutrality
                    if abs(position_delta) > max_delta:
                        continue
                        
                    # Calculate average bid/ask spread as percentage
                    try:
                        avg_spread_pct = (
                            long_put['spread'] / ((long_put['bid'] + long_put['ask'])/2 or 1) +
                            short_put['spread'] / ((short_put['bid'] + short_put['ask'])/2 or 1) +
                            short_call['spread'] / ((short_call['bid'] + short_call['ask'])/2 or 1) +
                            long_call['spread'] / ((long_call['bid'] + long_call['ask'])/2 or 1)
                        ) / 4
                    except ZeroDivisionError:
                        avg_spread_pct = float('inf')  # Skip options with zero prices
                        continue
                    
                    # Add to our list of potential iron condors
                    iron_condors.append({
                        'expiration': exp_date,
                        'dte': dte,
                        'long_put_strike': long_put['strike'],
                        'short_put_strike': short_put['strike'],
                        'short_call_strike': short_call['strike'],
                        'long_call_strike': long_call['strike'],
                        'net_credit': net_credit,
                        'max_loss': max_loss,
                        'position_delta': position_delta,
                        'position_gamma': position_gamma,
                        'position_theta': position_theta,
                        'position_vega': position_vega,
                        'avg_spread_pct': avg_spread_pct,
                        'risk_reward': max_loss / (net_credit * 100) if net_credit > 0 else float('inf'),
                        'put_width': put_width,
                        'call_width': call_width,
                        'expected_profit': expected_profit,
                        'prob_profit': prob_profit,
                        'implied_volatility': avg_vol
                    })
        
        # Sort by risk/reward ratio
        if iron_condors:
            iron_condors.sort(key=lambda x: x['risk_reward'])
            return iron_condors
        else:
            print("No suitable iron condors found matching your criteria.")
            return [] 