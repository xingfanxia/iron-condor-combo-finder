import pytest
import math
from src.analysis import OptionsAnalysis

@pytest.fixture
def options_analysis():
    """Fixture for OptionsAnalysis instance"""
    return OptionsAnalysis(risk_free_rate=0.05)

def test_calculate_probability_of_profit(options_analysis):
    """Test calculation of probability of profit"""
    # Set up test data
    current_price = 5300.0
    short_put_strike = 5200.0
    short_call_strike = 5400.0
    days_to_expiration = 7
    volatility = 0.2  # 20% annual volatility
    
    # Calculate probability
    prob = options_analysis.calculate_probability_of_profit(
        current_price, short_put_strike, short_call_strike, 
        days_to_expiration, volatility
    )
    
    # Basic sanity checks
    assert 0 <= prob <= 1, "Probability should be between 0 and 1"
    
    # Test with wider strikes - should increase probability
    wider_prob = options_analysis.calculate_probability_of_profit(
        current_price, 5100.0, 5500.0, 
        days_to_expiration, volatility
    )
    assert wider_prob > prob, "Wider strikes should increase probability of profit"
    
    # Test with higher volatility - should decrease probability
    higher_vol_prob = options_analysis.calculate_probability_of_profit(
        current_price, short_put_strike, short_call_strike, 
        days_to_expiration, volatility * 1.5
    )
    assert higher_vol_prob < prob, "Higher volatility should decrease probability of profit"
    
    # Test with longer expiration - should decrease probability
    longer_exp_prob = options_analysis.calculate_probability_of_profit(
        current_price, short_put_strike, short_call_strike, 
        days_to_expiration * 2, volatility
    )
    assert longer_exp_prob < prob, "Longer expiration should decrease probability of profit"

def test_calculate_expected_profit(options_analysis):
    """Test calculation of expected profit"""
    # Set up test data
    net_credit = 5.0  # $5.00 per share
    max_loss = 45.0   # $45.00 per share
    
    # Test with high probability
    high_prob = 0.8
    high_exp_profit = options_analysis.calculate_expected_profit(net_credit, max_loss, high_prob)
    assert high_exp_profit > 0, "With high probability, expected profit should be positive"
    
    # Test with breakeven probability
    # At what probability do we break even?
    # net_credit * 100 * prob - max_loss * (1 - prob) = 0
    # Solve for prob: prob = max_loss / (max_loss + net_credit * 100)
    breakeven_prob = max_loss / (max_loss + net_credit * 100)
    breakeven_exp_profit = options_analysis.calculate_expected_profit(net_credit, max_loss, breakeven_prob)
    assert abs(breakeven_exp_profit) < 0.01, "At breakeven probability, expected profit should be close to zero"
    
    # Test with low probability
    low_prob = 0.2
    low_exp_profit = options_analysis.calculate_expected_profit(net_credit, max_loss, low_prob)
    assert low_exp_profit < 0, "With low probability, expected profit should be negative"

# We'll add a simplified find_iron_condors test using our mock data in a separate test file 