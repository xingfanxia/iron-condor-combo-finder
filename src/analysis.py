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
        # Sanity check - ensure short_put_strike < current_price < short_call_strike
        if short_put_strike >= current_price or current_price >= short_call_strike:
            print(f"Warning: Strikes don't straddle current price - put: {short_put_strike}, price: {current_price}, call: {short_call_strike}")
            # For strikes that don't straddle the current price, use distance-based estimate
            put_distance = abs(current_price - short_put_strike) / current_price
            call_distance = abs(short_call_strike - current_price) / current_price
            
            # Higher probability for further OTM strikes
            if put_distance > 0.03 and call_distance > 0.03:
                return 0.7  # Further OTM strikes have better probability
            else:
                return 0.4  # Closer strikes have lower probability
            
        # Normalize volatility - Schwab API often returns extremely high values
        # First, detect if volatility is already a decimal or percentage
        if volatility > 10:  # Likely a percentage value (like 25% not 0.25)
            volatility = volatility / 100.0
            
        # Further cap volatility at reasonable levels
        volatility = max(min(volatility, 0.50), 0.10)  # Between 10% and 50%
        
        print(f"Using normalized volatility: {volatility:.2f} ({volatility*100:.1f}%)")
        
        # Annual volatility to daily
        daily_volatility = volatility / math.sqrt(252)
        
        # Standard deviation of price movement over the period
        std_dev = current_price * daily_volatility * math.sqrt(days_to_expiration)
        
        try:
            # Use a simplified model based on standard deviations
            # Calculate how many standard deviations away each strike is
            put_stdevs = (current_price - short_put_strike) / std_dev
            call_stdevs = (short_call_strike - current_price) / std_dev
            
            # Calculate probability using normal CDF
            prob_above_put = norm.cdf(put_stdevs)
            prob_below_call = norm.cdf(call_stdevs)
            
            # Combined probability - the probability of staying between both strikes
            prob = prob_above_put * prob_below_call
            
            # For very short-term options or extreme volatility, use a more conservative estimate
            if days_to_expiration <= 2 or volatility > 0.4:
                prob = min(prob, 0.85)  # Cap at 85% for very short term or high volatility
                
            # Ensure reasonable bounds
            prob = max(min(prob, 0.95), 0.05)  # Between 5% and 95%
            
            # Special case common iron condor probability range
            if 0.1 < put_stdevs < 2.0 and 0.1 < call_stdevs < 2.0:
                # Typical iron condor is set up for 70-85% probability
                estimated_prob = 0.5 + (min(put_stdevs, call_stdevs) / 8.0)
                # Blend with the calculated probability
                prob = (prob + estimated_prob) / 2.0
                
            print(f"Probability calculation: put_stdevs={put_stdevs:.2f}, call_stdevs={call_stdevs:.2f}, prob={prob:.2f}")
            return prob
            
        except (ValueError, ZeroDivisionError) as e:
            print(f"Error in probability calculation: {e}")
            
            # Fallback based on strike widths
            put_width_pct = (current_price - short_put_strike) / current_price
            call_width_pct = (short_call_strike - current_price) / current_price
            
            # Width-based probability estimate (wider is better)
            avg_width = (put_width_pct + call_width_pct) / 2
            prob = min(0.5 + (avg_width * 10), 0.9)  # Scale with width, cap at 90%
            
            return prob
    
    def calculate_expected_profit(self, net_credit, max_loss, prob_profit):
        """Calculate expected profit based on probability of profit"""
        # Expected value = (profit * probability of profit) + (loss * probability of loss)
        expected_profit = (net_credit * 100 * prob_profit) - (max_loss * (1 - prob_profit))
        return expected_profit
    
    def find_iron_condors(self, options_data, current_price, lower_bound, upper_bound, 
                         min_dte, max_dte, min_liquidity, max_delta=0.03, 
                         keep_best_candidates=True, spread_width=25):
        """
        Find iron condor option combinations that meet our criteria
        
        Parameters:
        options_data (dict): Options chain data
        current_price (float): Current price of the underlying
        lower_bound (float): Lower bound of our expected price range
        upper_bound (float): Upper bound of our expected price range
        min_dte (int): Minimum days to expiration
        max_dte (int): Maximum days to expiration
        min_liquidity (int): Minimum volume/open interest
        max_delta (float): Maximum acceptable overall position delta
        keep_best_candidates (bool): Keep best candidates even if they don't meet all criteria
        spread_width (int): Width between short and long legs (default: 25 points)
        
        Returns:
        list: List of dictionaries with iron condor details
        """
        print(f"Finding iron condors with these parameters:")
        print(f"- Current price: ${current_price}")
        print(f"- Expected range: ${lower_bound} to ${upper_bound}")
        print(f"- Minimum liquidity: {min_liquidity}")
        print(f"- Maximum delta: {max_delta}")
        print(f"- Spread width: {spread_width} points between short and long legs")
        
        # Calculate the exact target short strikes at the 2% bounds
        target_short_put = lower_bound  # Exact lower bound (2% below)
        target_short_call = upper_bound  # Exact upper bound (2% above)
        
        print(f"Target short put strike: ${target_short_put:.2f} (2% below current)")
        print(f"Target short call strike: ${target_short_call:.2f} (2% above current)")
        
        iron_condors = []
        rejected_count = {
            'liquidity': 0,
            'credit': 0,
            'delta': 0,
            'bounds': 0
        }
        
        # Loop through expirations
        for expiration in options_data['callExpDateMap']:
            # Parse expiration date
            exp_parts = expiration.split(':')
            if len(exp_parts) < 2:
                print(f"Invalid expiration format: {expiration}")
                continue
                
            # Get expiration date and DTE (days to expiration)
            exp_date = exp_parts[0]
            dte = int(exp_parts[1]) if len(exp_parts) > 1 and exp_parts[1].isdigit() else 0
            
            # Filter by DTE
            if dte < min_dte or dte > max_dte:
                print(f"Skipping expiration {exp_date} (DTE: {dte}) - outside DTE range {min_dte}-{max_dte}")
                continue
                
            # Make sure this expiration exists in both calls and puts
            if expiration not in options_data['putExpDateMap']:
                print(f"Expiration {expiration} not found in puts")
                continue
                
            # Collect all valid call and put options
            call_options = []
            put_options = []
            
            # Process call options for this expiration
            for strike in options_data['callExpDateMap'].get(expiration, {}):
                try:
                    option = options_data['callExpDateMap'][expiration][strike][0]
                    
                    # Filter by basic liquidity - relaxed check to include more options
                    if option.get('totalVolume', 0) < min_liquidity / 2:  # Allow half the normal minimum 
                        continue
                        
                    call_options.append({
                        'strike': float(strike),
                        'bid': option.get('bid', 0),
                        'ask': option.get('ask', 0),
                        'delta': option.get('delta', 0),
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
            
            # Process put options for this expiration
            for strike in options_data['putExpDateMap'].get(expiration, {}):
                try:
                    option = options_data['putExpDateMap'][expiration][strike][0]
                    
                    # Filter by basic liquidity - relaxed check to include more options
                    if option.get('totalVolume', 0) < min_liquidity / 2:  # Allow half the normal minimum
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
            
            # Find OTM options
            otm_puts = [p for p in put_options if p['strike'] < current_price]
            otm_calls = [c for c in call_options if c['strike'] > current_price]
            
            if len(otm_puts) < 2 or len(otm_calls) < 2:
                print(f"Not enough OTM options for expiration {exp_date}")
                continue
            
            print(f"Analyzing {exp_date} (DTE: {dte}): {len(otm_puts)} OTM puts, {len(otm_calls)} OTM calls")
            
            # Get available strikes
            all_put_strikes = [p['strike'] for p in otm_puts]
            all_call_strikes = [c['strike'] for c in otm_calls]
            
            # Find the short strikes closest to our 2% bounds
            # Calculate percentage moves from the bounds
            put_pct_move = (current_price - lower_bound) / current_price * 100  # Typically 2%
            call_pct_move = (upper_bound - current_price) / current_price * 100  # Typically 2%
            
            # For puts, we want strikes within +/- 0.5% of our target (so 1.5% to 2.5% from current price)
            target_put_pct_low = (put_pct_move - 0.5) / 100  # 1.5%
            target_put_pct_high = (put_pct_move + 0.5) / 100  # 2.5%
            lower_bound_range_min = current_price * (1 - target_put_pct_high)  # 2.5% below
            lower_bound_range_max = current_price * (1 - target_put_pct_low)   # 1.5% below
            
            # For calls, similar range of +/- 0.5% around the 2% target
            target_call_pct_low = (call_pct_move - 0.5) / 100  # 1.5%
            target_call_pct_high = (call_pct_move + 0.5) / 100  # 2.5%
            upper_bound_range_min = current_price * (1 + target_call_pct_low)   # 1.5% above
            upper_bound_range_max = current_price * (1 + target_call_pct_high)  # 2.5% above
            
            print(f"Target short put range: ${lower_bound_range_min:.2f} to ${lower_bound_range_max:.2f} (1.5% to 2.5% below)")
            print(f"Target short call range: ${upper_bound_range_min:.2f} to ${upper_bound_range_max:.2f} (1.5% to 2.5% above)")
            
            # For puts, look for strikes in our wider range
            short_put_candidates = [p for p in otm_puts if lower_bound_range_min <= p['strike'] <= lower_bound_range_max]
            if not short_put_candidates:
                # If no strikes in range, take the closest available strikes
                short_put_candidates = otm_puts
                print(f"Warning: No put strikes in target range, using all available OTM puts")
            
            # For calls, look for strikes in our wider range
            short_call_candidates = [c for c in otm_calls if upper_bound_range_min <= c['strike'] <= upper_bound_range_max]
            if not short_call_candidates:
                # If no strikes in range, take the closest available strikes
                short_call_candidates = otm_calls
                print(f"Warning: No call strikes in target range, using all available OTM calls")
            
            # Sort to get closest to our bounds
            best_short_puts = sorted(short_put_candidates, key=lambda x: abs(x['strike'] - target_short_put))
            best_short_calls = sorted(short_call_candidates, key=lambda x: abs(x['strike'] - target_short_call))
            
            # If we found candidates, print them
            if best_short_puts and best_short_calls:
                print(f"Best short put candidates: " + 
                      ", ".join([f"${p['strike']:.2f}" for p in best_short_puts[:3]]))
                print(f"Best short call candidates: " + 
                      ", ".join([f"${c['strike']:.2f}" for c in best_short_calls[:3]]))
            
            # Only continue if we found suitable short strikes
            if not best_short_puts or not best_short_calls:
                print(f"No suitable short strikes found for {exp_date}")
                continue
                
            # Find potential iron condors
            ic_candidates = 0
            
            # Loop through potential short puts close to target
            for short_put_idx, short_put in enumerate(best_short_puts[:3]):  # Look at top 3 candidates
                # Find long put below the short put
                long_put_candidates = [p for p in otm_puts if p['strike'] < short_put['strike']]
                if not long_put_candidates:
                    continue
                    
                # Pick long put with the configured spread width if available
                target_long_put_strike = short_put['strike'] - spread_width
                long_put = min(long_put_candidates, key=lambda x: abs(x['strike'] - target_long_put_strike))
                
                # Loop through potential short calls close to target
                for short_call_idx, short_call in enumerate(best_short_calls[:3]):  # Look at top 3 candidates
                    # Find long call above the short call
                    long_call_candidates = [c for c in otm_calls if c['strike'] > short_call['strike']]
                    if not long_call_candidates:
                        continue
                        
                    # Pick long call with the configured spread width if available
                    target_long_call_strike = short_call['strike'] + spread_width
                    long_call = min(long_call_candidates, key=lambda x: abs(x['strike'] - target_long_call_strike))
                    
                    # Skip if any option has zero bid/ask
                    if (long_put['ask'] <= 0 or short_put['bid'] <= 0 or
                        short_call['bid'] <= 0 or long_call['ask'] <= 0):
                        rejected_count['liquidity'] += 1
                        continue
                    
                    # Calculate key metrics
                    net_credit = (short_put['bid'] - long_put['ask'] + 
                                  short_call['bid'] - long_call['ask'])
                    
                    # Skip negative credit spreads
                    if net_credit <= 0:
                        rejected_count['credit'] += 1
                        continue
                    
                    # Increment candidate count
                    ic_candidates += 1
                    
                    # Width of spreads
                    put_width = short_put['strike'] - long_put['strike']
                    call_width = long_call['strike'] - short_call['strike']
                    
                    # Max loss (assuming equal width spreads)
                    max_loss = max(put_width, call_width) * 100 - (net_credit * 100)
                    
                    # Combine volatility from all legs (weighted average)
                    # Normalize volatility from Schwab API which can be extremely high 
                    leg_vols = []
                    for leg in [long_put, short_put, short_call, long_call]:
                        vol = leg.get('volatility', 20)
                        # Convert percentage to decimal if needed
                        if vol > 10:  # if over 10, assume it's a percentage
                            vol = vol / 100.0
                        # Cap at reasonable values
                        vol = max(min(vol, 0.5), 0.1)  # 10% to 50% range
                        leg_vols.append(vol)
                    
                    # Average the normalized volatilities
                    avg_vol = sum(leg_vols) / len(leg_vols)
                    
                    # Calculate probability of profit with normalized volatility
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
                        rejected_count['delta'] += 1
                        continue
                    
                    # Calculate distances from current price as percentages
                    put_distance_pct = ((current_price - short_put['strike']) / current_price) * 100
                    call_distance_pct = ((short_call['strike'] - current_price) / current_price) * 100
                        
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
                        
                    # Score this iron condor based on how well it matches our strategy
                    # Higher score is better
                    strategy_score = 0
                    
                    # Factor 1: Reward strategies with short strikes close to our 2% bounds
                    # Target is the specific percentage distance on each side, allow some flexibility
                    target_put_distance = put_pct_move  # Desired percent distance (typically 2%)
                    target_call_distance = call_pct_move  # Desired percent distance (typically 2%)
                    
                    # Use same scoring function as above
                    def distance_score(actual, target):
                        diff = abs(actual - target)
                        if diff <= 0.5:  # Within our wider range of +/- 0.5%
                            return 15 - diff * 10  # Gradual reduction within range
                        else:
                            return 15 - 5 - (diff - 0.5) * 15  # Steeper penalty outside range
                    
                    put_distance_score = distance_score(put_distance_pct, target_put_distance)
                    call_distance_score = distance_score(call_distance_pct, target_call_distance)
                    position_score = max(0, put_distance_score) + max(0, call_distance_score)
                    
                    # Factor 2: Reward higher probability strategies
                    prob_score = prob_profit * 5  # Higher probability is better
                    
                    # Factor 3: Reward higher credit for the risk
                    credit_per_risk = net_credit / (max_loss / 100) if max_loss > 0 else 0
                    credit_score = credit_per_risk * 10
                    
                    # Combine the scores - emphasize position score
                    strategy_score = position_score * 4 + prob_score + credit_score
                    
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
                        'probability_of_profit': prob_profit * 100,  # Convert to percentage
                        'implied_volatility': avg_vol,
                        'strategy_score': strategy_score,  # New field for scoring
                        'put_distance_pct': put_distance_pct,  # Store distances for reference
                        'call_distance_pct': call_distance_pct
                    })
                    print(f"ADDED IRON CONDOR: {short_put['strike']}/{short_call['strike']} | Score: {strategy_score:.2f}")
            
            if ic_candidates > 0:
                print(f"Found {ic_candidates} potential iron condors for {exp_date}")
                
                # If we want to keep the best candidate for this expiration regardless of criteria
                if keep_best_candidates and not any(ic['expiration'] == exp_date for ic in iron_condors):
                    # Only consider expirations within our DTE range
                    if dte < min_dte or dte > max_dte:
                        print(f"Skipping best candidate search for {exp_date} (DTE: {dte}) - outside DTE range {min_dte}-{max_dte}")
                        continue
                        
                    # Find all potential combinations for this expiration
                    exp_candidates = []
                    
                    # Loop through all potential short puts for this expiration
                    for short_put in otm_puts:
                        # Find long put below the short put
                        long_put_candidates = [p for p in otm_puts if p['strike'] < short_put['strike']]
                        if not long_put_candidates:
                            continue
                            
                        # Pick long put with the configured spread width if available
                        target_long_put_strike = short_put['strike'] - spread_width
                        long_put = min(long_put_candidates, key=lambda x: abs(x['strike'] - target_long_put_strike))
                        
                        # Loop through potential short calls
                        for short_call in otm_calls:
                            # Find long call above the short call
                            long_call_candidates = [c for c in otm_calls if c['strike'] > short_call['strike']]
                            if not long_call_candidates:
                                continue
                                
                            # Pick long call with the configured spread width if available
                            target_long_call_strike = short_call['strike'] + spread_width
                            long_call = min(long_call_candidates, key=lambda x: abs(x['strike'] - target_long_call_strike))
                            
                            # Calculate key metrics - allow negative credit for finding potential
                            net_credit = (short_put.get('bid', 0) - long_put.get('ask', 0) + 
                                        short_call.get('bid', 0) - long_call.get('ask', 0))
                            
                            # If all bids/asks are valid, this is a potential candidate
                            if (long_put.get('ask', 0) > 0 and short_put.get('bid', 0) > 0 and
                                short_call.get('bid', 0) > 0 and long_call.get('ask', 0) > 0):
                                
                                # Calculate distances from current price
                                put_distance_pct = ((current_price - short_put['strike']) / current_price) * 100
                                call_distance_pct = ((short_call['strike'] - current_price) / current_price) * 100
                                
                                # Score based on proximity to 2% target
                                target_distance = 2.0
                                distance_score = (10 - abs(put_distance_pct - target_distance) * 3 +
                                               10 - abs(call_distance_pct - target_distance) * 3)
                                
                                # Add to candidates with score
                                exp_candidates.append({
                                    'short_put': short_put,
                                    'long_put': long_put,
                                    'short_call': short_call,
                                    'long_call': long_call,
                                    'net_credit': net_credit,
                                    'distance_score': distance_score,
                                    'put_distance_pct': put_distance_pct,
                                    'call_distance_pct': call_distance_pct
                                })
                    
                    # If we found any candidates, add the best one
                    if exp_candidates:
                        # First filter candidates by delta
                        delta_filtered_candidates = []
                        for candidate in exp_candidates:
                            short_put = candidate['short_put']
                            long_put = candidate['long_put']
                            short_call = candidate['short_call']
                            long_call = candidate['long_call']
                            
                            # Calculate position delta
                            position_delta = (long_put.get('delta', 0) + short_put.get('delta', 0) + 
                                           short_call.get('delta', 0) + long_call.get('delta', 0))
                            
                            # Check delta neutrality - IMPORTANT: Use absolute value
                            if abs(position_delta) <= max_delta:
                                candidate['position_delta'] = position_delta
                                delta_filtered_candidates.append(candidate)
                        
                        # If no candidates meet delta constraint, don't add any
                        if not delta_filtered_candidates:
                            print(f"No delta-neutral candidates found for {exp_date} (max_delta: {max_delta})")
                            continue
                            
                        # Sort delta-filtered candidates by distance score
                        delta_filtered_candidates.sort(key=lambda x: x['distance_score'], reverse=True)
                        best = delta_filtered_candidates[0]
                        
                        # Use this delta-filtered candidate
                        short_put = best['short_put']
                        long_put = best['long_put']
                        short_call = best['short_call']
                        long_call = best['long_call']
                        position_delta = best['position_delta']
                        
                        # Now add this as a full iron condor
                        net_credit = best['net_credit']
                        put_width = short_put['strike'] - long_put['strike']
                        call_width = long_call['strike'] - short_call['strike']
                        max_loss = max(put_width, call_width) * 100 - (net_credit * 100)
                        
                        # Normalize volatility from Schwab API
                        leg_vols = []
                        for leg in [long_put, short_put, short_call, long_call]:
                            vol = leg.get('volatility', 20)
                            if vol > 10:
                                vol = vol / 100.0
                            vol = max(min(vol, 0.5), 0.1)
                            leg_vols.append(vol)
                        
                        avg_vol = sum(leg_vols) / len(leg_vols)
                        
                        # Calculate probability
                        prob_profit = self.calculate_probability_of_profit(
                            current_price=current_price,
                            short_put_strike=short_put['strike'],
                            short_call_strike=short_call['strike'],
                            days_to_expiration=dte,
                            volatility=avg_vol
                        )
                        
                        # Calculate Greeks
                        position_gamma = (long_put.get('gamma', 0.01) + short_put.get('gamma', 0.01) + 
                                        short_call.get('gamma', 0.01) + long_call.get('gamma', 0.01))
                        position_theta = (long_put.get('theta', -0.01) + short_put.get('theta', -0.01) + 
                                        short_call.get('theta', -0.01) + long_call.get('theta', -0.01))
                        position_vega = (long_put.get('vega', 0.1) + short_put.get('vega', 0.1) + 
                                        short_call.get('vega', 0.1) + long_call.get('vega', 0.1))
                        
                        # Expected profit
                        expected_profit = self.calculate_expected_profit(
                            net_credit=net_credit,
                            max_loss=max_loss,
                            prob_profit=prob_profit
                        )
                        
                        # Strategy score
                        target_put_distance = put_pct_move  # Desired percent distance (typically 2%)
                        target_call_distance = call_pct_move  # Desired percent distance (typically 2%)
                        
                        # Use same scoring function as above
                        def distance_score(actual, target):
                            diff = abs(actual - target)
                            if diff <= 0.5:  # Within our wider range of +/- 0.5%
                                return 15 - diff * 10  # Gradual reduction within range
                            else:
                                return 15 - 5 - (diff - 0.5) * 15  # Steeper penalty outside range
                                
                        put_distance_score = distance_score(best['put_distance_pct'], target_put_distance)
                        call_distance_score = distance_score(best['call_distance_pct'], target_call_distance)
                        position_score = max(0, put_distance_score) + max(0, call_distance_score)
                        prob_score = prob_profit * 5
                        credit_per_risk = net_credit / (max_loss / 100) if max_loss > 0 else 0
                        credit_score = credit_per_risk * 10
                        strategy_score = position_score * 4 + prob_score + credit_score
                        
                        # Add to our list
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
                            'avg_spread_pct': 0.1,  # Placeholder
                            'risk_reward': max_loss / (net_credit * 100) if net_credit > 0 else float('inf'),
                            'put_width': put_width,
                            'call_width': call_width,
                            'expected_profit': expected_profit,
                            'probability_of_profit': prob_profit * 100,
                            'implied_volatility': avg_vol,
                            'strategy_score': strategy_score,
                            'put_distance_pct': best['put_distance_pct'],
                            'call_distance_pct': best['call_distance_pct'],
                            'is_best_candidate': True  # Mark this as a "best candidate" that might not meet all criteria
                        })
                        print(f"ADDED BEST CANDIDATE: {short_put['strike']}/{short_call['strike']} | Score: {strategy_score:.2f}")
        
        # Print rejection statistics
        print(f"\nRejection statistics:")
        print(f"- Liquidity issues: {rejected_count['liquidity']}")
        print(f"- Negative credit spreads: {rejected_count['credit']}") 
        print(f"- Delta neutrality issues: {rejected_count['delta']}")
        print(f"- Strike bounds issues: {rejected_count['bounds']}")
        
        # Debug candidate details
        print(f"\nDebug: Candidate Iron Condors Details:")
        if iron_condors:
            for idx, ic in enumerate(iron_condors):
                print(f"Candidate #{idx+1}:")
                print(f"  Exp: {ic['expiration']} (DTE: {ic['dte']})")
                print(f"  Strikes: {ic['long_put_strike']}/{ic['short_put_strike']}/{ic['short_call_strike']}/{ic['long_call_strike']}")
                print(f"  Credit: ${ic['net_credit']:.2f} | Delta: {ic['position_delta']:.4f}")
                print(f"  Strategy Score: {ic['strategy_score']:.2f}")
                print(f"  Put Distance: {ic['put_distance_pct']:.2f}% | Call Distance: {ic['call_distance_pct']:.2f}%")
                print(f"  Probability: {ic['probability_of_profit']:.1f}%")
        else:
            print("  No candidates found at all")
        
        # Sort by strategy score (higher is better)
        if iron_condors:
            iron_condors.sort(key=lambda x: x['strategy_score'], reverse=True)
            print(f"Found {len(iron_condors)} iron condors, sorted by strategy score")
            return iron_condors
        else:
            print("No suitable iron condors found matching your criteria.")
            return [] 