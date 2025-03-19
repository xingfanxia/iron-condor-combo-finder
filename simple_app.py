import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime
from src.ic_finder import IronCondorFinder

st.set_page_config(page_title="Iron Condor Finder (Yahoo Finance)", layout="wide")

def main():
    st.title("Iron Condor Option Strategy Finder")
    st.markdown("### Using Yahoo Finance Data")
    
    st.markdown("""
    This tool helps you find optimal iron condor option combinations that are 
    delta neutral and bet against specific price moves.
    
    *Note: This version uses only Yahoo Finance data which doesn't require authentication.*
    """)
    
    # Sidebar for configurations
    st.sidebar.header("Configuration")
    
    # Symbol selection
    symbol = st.sidebar.text_input("Symbol", value="SPX")
    
    # Parameter configurations
    st.sidebar.subheader("Parameters")
    
    max_move_pct = st.sidebar.slider(
        "Max Movement %", 
        min_value=0.5, 
        max_value=5.0, 
        value=2.0, 
        step=0.1,
        help="Maximum expected price movement percentage we're betting against"
    )
    
    max_delta = st.sidebar.slider(
        "Max Position Delta", 
        min_value=0.001, 
        max_value=0.1, 
        value=0.01, 
        step=0.001,
        format="%.3f",
        help="Maximum acceptable overall position delta"
    )
    
    min_dte, max_dte = st.sidebar.slider(
        "Days to Expiration (DTE) Range", 
        min_value=0, 
        max_value=60, 
        value=(1, 3),
        help="Range of days to expiration for options to consider"
    )
    
    min_liquidity = st.sidebar.slider(
        "Min Liquidity (Volume)",
        min_value=10,
        max_value=1000,
        value=50,
        step=10,
        help="Minimum option volume to ensure adequate liquidity"
    )
    
    num_results = st.sidebar.slider(
        "Number of Results",
        min_value=1,
        max_value=20,
        value=5,
        help="Number of top iron condors to display"
    )
    
    generate_charts = st.sidebar.checkbox(
        "Generate P/L Charts", 
        value=True,
        help="Generate profit/loss charts for each iron condor"
    )
    
    # Run button
    if st.sidebar.button("Find Iron Condors"):
        with st.spinner("Searching for iron condors using Yahoo Finance data..."):
            try:
                # Create finder with Yahoo data source only
                finder = IronCondorFinder(
                    symbol=symbol,
                    max_move_pct=max_move_pct,
                    max_delta=max_delta,
                    min_dte=min_dte,
                    max_dte=max_dte,
                    min_liquidity=min_liquidity,
                    data_source='yahoo',  # Force Yahoo Finance
                    num_results=num_results,
                    generate_charts=generate_charts
                )
                
                # Run search
                iron_condors = finder.find_iron_condors()
                
                if not iron_condors:
                    st.warning("No suitable iron condors found with these parameters.")
                    return
                
                # Display current price and range
                current_price = finder.data_source_client.get_current_price()
                lower_bound = current_price * (1 - max_move_pct/100)
                upper_bound = current_price * (1 + max_move_pct/100)
                
                st.markdown(f"#### Current {symbol} price: ${current_price:.2f}")
                st.markdown(f"Looking for iron condors that profit if {symbol} stays between "
                           f"${lower_bound:.2f} and ${upper_bound:.2f}")
                
                # Display results
                st.markdown("### Top Iron Condor Opportunities")
                
                # Create tabs for different views
                tab1, tab2 = st.tabs(["Detailed View", "Table View"])
                
                with tab1:
                    # Detailed view with cards
                    for i, ic in enumerate(iron_condors[:num_results]):
                        with st.expander(
                            f"#{i+1} - Expiration: {ic['expiration']} (DTE: {ic['dte']}) - "
                            f"Strikes: {ic['long_put_strike']}/{ic['short_put_strike']}/"
                            f"{ic['short_call_strike']}/{ic['long_call_strike']}",
                            expanded=(i==0)  # First one expanded by default
                        ):
                            col1, col2 = st.columns([1, 1])
                            
                            with col1:
                                st.markdown("##### Structure")
                                st.markdown(f"Long Put Strike: **${ic['long_put_strike']:.2f}**")
                                st.markdown(f"Short Put Strike: **${ic['short_put_strike']:.2f}**")
                                st.markdown(f"Short Call Strike: **${ic['short_call_strike']:.2f}**")
                                st.markdown(f"Long Call Strike: **${ic['long_call_strike']:.2f}**")
                                
                                st.markdown("##### Profit Metrics")
                                st.markdown(f"Net Credit: **${ic['net_credit']:.2f}**")
                                st.markdown(f"Max Loss: **${ic['max_loss']:.2f}**")
                                st.markdown(f"Expected Profit: **${ic['expected_profit']:.2f}**")
                                st.markdown(f"Probability of Profit: **{ic['prob_profit']*100:.1f}%**")
                                st.markdown(f"Risk/Reward Ratio: **{ic['risk_reward']:.2f}**")
                                
                                st.markdown("##### Greeks")
                                st.markdown(f"Delta: **{ic['position_delta']:.4f}**")
                                st.markdown(f"Gamma: **{ic['position_gamma']:.4f}**")
                                st.markdown(f"Theta: **${ic['position_theta']:.2f}**")
                                st.markdown(f"Vega: **{ic['position_vega']:.4f}**")
                            
                            with col2:
                                if generate_charts and 'chart_path' in ic and ic['chart_path']:
                                    chart_path = ic['chart_path']
                                    if os.path.exists(chart_path):
                                        st.image(chart_path, use_column_width=True)
                                    else:
                                        st.info(f"Chart not available for this iron condor")
                                else:
                                    st.info("P/L Charts are disabled. Enable in settings to see visualization.")
                
                with tab2:
                    # Table view of all results
                    if iron_condors:
                        # Select important columns for display
                        display_cols = [
                            'expiration', 'dte', 
                            'long_put_strike', 'short_put_strike', 'short_call_strike', 'long_call_strike',
                            'net_credit', 'max_loss', 'prob_profit', 'expected_profit', 'position_delta', 'risk_reward'
                        ]
                        
                        # Create DataFrame
                        display_df = pd.DataFrame(iron_condors[:num_results])
                        
                        # Format numeric columns for better display
                        if 'prob_profit' in display_df.columns:
                            display_df['prob_profit'] = display_df['prob_profit'].apply(lambda x: f"{x*100:.1f}%")
                        if 'position_delta' in display_df.columns:
                            display_df['position_delta'] = display_df['position_delta'].apply(lambda x: f"{x:.4f}")
                        if 'net_credit' in display_df.columns:
                            display_df['net_credit'] = display_df['net_credit'].apply(lambda x: f"${x:.2f}")
                        if 'max_loss' in display_df.columns:
                            display_df['max_loss'] = display_df['max_loss'].apply(lambda x: f"${x:.2f}")
                        if 'expected_profit' in display_df.columns:
                            display_df['expected_profit'] = display_df['expected_profit'].apply(lambda x: f"${x:.2f}")
                        if 'risk_reward' in display_df.columns:
                            display_df['risk_reward'] = display_df['risk_reward'].apply(lambda x: f"{x:.2f}")
                        
                        # Display the table
                        st.dataframe(display_df[display_cols], use_container_width=True)
                        
                        # Export button
                        csv = display_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "Download results as CSV",
                            csv,
                            f"iron_condors_{symbol}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv",
                            "text/csv",
                            key='download-csv'
                        )
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("Troubleshooting suggestions:")
                st.markdown("""
                - Check that the symbol is valid and has options available
                - Try a different expiration range
                - Try a wider max movement percentage
                - Reduce the minimum liquidity requirement
                - Yahoo Finance API limitations may cause temporary failures
                """)
    
    # Information section
    with st.expander("What is an Iron Condor?"):
        st.markdown("""
        An iron condor is an options strategy consisting of:
        
        1. **Long Put** (buy a put at a lower strike)
        2. **Short Put** (sell a put at a higher strike)
        3. **Short Call** (sell a call at a higher strike)
        4. **Long Call** (buy a call at an even higher strike)
        
        **Key characteristics:**
        - All options have the same expiration date
        - Creates a position that profits if the underlying stays within a range
        - Maximum profit is the net premium received (net credit)
        - Maximum loss is limited by the width of either spread minus the premium
        - Delta-neutral setups aim to eliminate directional bias
        
        Iron condors are typically used when you expect the underlying to trade within a range.
        """)
        
        st.image("https://www.investopedia.com/thmb/h1QOLpWkrJYIgZfMbwd5Jg8UWro=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/Clipboard01-57c6e8e35f9b5829f455ffd3.jpg", 
                caption="Iron Condor Payoff Diagram")
    
    with st.expander("About Yahoo Finance Data"):
        st.markdown("""
        ### Yahoo Finance Data Source
        
        This simplified version of the tool uses only the Yahoo Finance API, which:
        
        - **Requires no authentication** or API keys
        - Is accessible to anyone without special access
        - Provides basic options data including strikes, prices, and volume
        - Has limitations for professional use
        
        #### Limitations to be aware of:
        
        - **Greeks are estimated** since Yahoo doesn't provide them directly
        - Calculations use simplified Black-Scholes approximations
        - Data may have slight delays (typically 15-20 minutes)
        - There can be gaps in the options chain data
        - Rate limits may apply with frequent usage
        
        For professional trading, consider upgrading to Schwab or Interactive Brokers data once your API access is approved.
        """)

if __name__ == "__main__":
    main() 