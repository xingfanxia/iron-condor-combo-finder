#!/usr/bin/env python

"""
Script to show all iron condor candidates, not just the top ones.
This is useful for seeing all potential combinations that were found.
"""

import sys
from src.ic_finder import IronCondorFinder
from src.utilities import Utils

def main():
    # Parse command line arguments
    max_delta = 0.01
    spread_width = 25
    
    if len(sys.argv) > 1:
        try:
            max_delta = float(sys.argv[1])
            print(f"Using max_delta={max_delta}")
        except ValueError:
            print(f"Invalid max_delta: {sys.argv[1]}, using default {max_delta}")
    
    if len(sys.argv) > 2:
        try:
            spread_width = int(sys.argv[2])
            print(f"Using spread_width={spread_width}")
        except ValueError:
            print(f"Invalid spread_width: {sys.argv[2]}, using default {spread_width}")
    
    # Create iron condor finder with high num_results to show all candidates
    finder = IronCondorFinder(
        symbol='$SPX',
        max_move_pct=2.0,
        max_delta=max_delta,
        min_dte=1,
        max_dte=7,
        min_liquidity=10,  # Reduced from 50 to show more candidates
        data_source='schwab',
        num_results=100,   # Show many results
        generate_charts=False,
        spread_width=spread_width
    )
    
    # Find iron condors
    print(f"Finding iron condors with max_delta={max_delta} and spread_width={spread_width}...")
    iron_condors = finder.find_iron_condors()
    
    if not iron_condors:
        print("No iron condors found that match the criteria.")
        return
        
    # Display a summary of all candidates
    print("\n== SUMMARY OF ALL CANDIDATES ==")
    print(f"Found {len(iron_condors)} total iron condor candidates")
    
    if len(iron_condors) > 0:
        print("\nAll Iron Condor Candidates:")
        print("-" * 100)
        
        # Sort by various metrics
        by_prob = sorted(iron_condors, key=lambda x: x['probability_of_profit'], reverse=True)
        by_delta = sorted(iron_condors, key=lambda x: abs(x['position_delta']))
        by_credit = sorted(iron_condors, key=lambda x: x['net_credit'], reverse=True)
        by_score = sorted(iron_condors, key=lambda x: x['strategy_score'], reverse=True)
        
        # Print top 3 by probability
        print("\n🎯 TOP 3 BY PROBABILITY OF PROFIT:")
        for i, ic in enumerate(by_prob[:3]):
            print(f"#{i+1} - {ic['expiration']} | {ic['short_put_strike']}/{ic['short_call_strike']} | " +
                  f"Prob: {ic['probability_of_profit']:.1f}% | Delta: {ic['position_delta']:.4f} | " +
                  f"Credit: ${ic['net_credit']:.2f}")
        
        # Print top 3 by delta neutrality
        print("\n⚖️ TOP 3 BY DELTA NEUTRALITY:")
        for i, ic in enumerate(by_delta[:3]):
            print(f"#{i+1} - {ic['expiration']} | {ic['short_put_strike']}/{ic['short_call_strike']} | " +
                  f"Delta: {ic['position_delta']:.4f} | Prob: {ic['probability_of_profit']:.1f}% | " +
                  f"Credit: ${ic['net_credit']:.2f}")
        
        # Print top 3 by credit
        print("\n💰 TOP 3 BY CREDIT AMOUNT:")
        for i, ic in enumerate(by_credit[:3]):
            print(f"#{i+1} - {ic['expiration']} | {ic['short_put_strike']}/{ic['short_call_strike']} | " +
                  f"Credit: ${ic['net_credit']:.2f} | Prob: {ic['probability_of_profit']:.1f}% | " +
                  f"Delta: {ic['position_delta']:.4f}")
        
        # Print top 3 by overall score
        print("\n🏆 TOP 3 BY OVERALL SCORE:")
        for i, ic in enumerate(by_score[:3]):
            print(f"#{i+1} - {ic['expiration']} | {ic['short_put_strike']}/{ic['short_call_strike']} | " +
                  f"Score: {ic['strategy_score']:.2f} | Prob: {ic['probability_of_profit']:.1f}% | " +
                  f"Delta: {ic['position_delta']:.4f} | Credit: ${ic['net_credit']:.2f}")
        
        # Print detailed view of all candidates
        print("\n== DETAILED VIEW OF ALL CANDIDATES ==")
        for i, ic in enumerate(iron_condors):
            print(f"{i+1}. {ic['expiration']} - {ic['long_put_strike']}/{ic['short_put_strike']}/{ic['short_call_strike']}/{ic['long_call_strike']}")
            print(f"   Credit: ${ic['net_credit']:.2f} | Prob: {ic['probability_of_profit']:.1f}% | Delta: {ic['position_delta']:.4f}")
            print(f"   Put Distance: {ic['put_distance_pct']:.2f}% | Call Distance: {ic['call_distance_pct']:.2f}%")
            print(f"   Score: {ic['strategy_score']:.2f}\n")

if __name__ == "__main__":
    main() 