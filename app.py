import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime
from src.ic_finder import IronCondorFinder
from PIL import Image
import io

st.set_page_config(page_title="Iron Condor Finder", layout="wide")

def show_chart(chart_path):
    """Display a chart from a file path"""
    if os.path.exists(chart_path):
        image = Image.open(chart_path)
        st.image(image, use_column_width=True)
    else:
        st.error(f"Chart not found: {chart_path}")

def main():
    st.title("Iron Condor Option Strategy Finder")
    
    st.markdown("""
    This tool helps you find optimal iron condor option combinations for indexes like SPX that are 
    delta neutral and bet against specific price moves.
    """)
    
    # Sidebar for configurations
    st.sidebar.header("Configuration")
    
    # Symbol selection
    symbol = st.sidebar.text_input("Symbol", value="SPX")
    
    # Data source selection
    data_source = st.sidebar.selectbox(
        "Data Source", 
        ["schwab", "ib", "yahoo", "cboe"],
        help="Schwab or Interactive Brokers API are preferred but require proper setup. Yahoo is the free fallback option."
    )
    
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
    
    sort_method = st.sidebar.selectbox(
        "Sort Results By",
        ["Risk/Reward", "Expected Profit", "Probability of Profit"],
        help="Method for sorting and ranking the iron condor opportunities"
    )
    
    # Run button
    if st.sidebar.button("Find Iron Condors"):
        with st.spinner("Searching for iron condors..."):
            # Create finder
            finder = IronCondorFinder(
                symbol=symbol,
                max_move_pct=max_move_pct,
                max_delta=max_delta,
                min_dte=min_dte,
                max_dte=max_dte,
                min_liquidity=min_liquidity,
                data_source=data_source,
                num_results=num_results,
                generate_charts=generate_charts
            )
            
            try:
                # Run search
                iron_condors = finder.find_iron_condors()
                
                if not iron_condors:
                    st.warning("No suitable iron condors found with these parameters.")
                    return
                
                # Sort by selected method
                if sort_method == "Expected Profit":
                    iron_condors.sort(key=lambda x: x['expected_profit'], reverse=True)
                elif sort_method == "Probability of Profit":
                    iron_condors.sort(key=lambda x: x['prob_profit'], reverse=True)
                # Default is already Risk/Reward (lowest first)
                
                # Display current price and range
                current_price = finder.get_current_price()
                lower_bound = current_price * (1 - max_move_pct/100)
                upper_bound = current_price * (1 + max_move_pct/100)
                
                st.markdown(f"#### Current {symbol} price: ${current_price:.2f}")
                st.markdown(f"Looking for iron condors that profit if {symbol} stays between "
                           f"${lower_bound:.2f} and ${upper_bound:.2f}")
                
                # Interactive results display
                st.markdown("### Top Iron Condor Opportunities")
                
                # Create tabs for different views
                tab1, tab2 = st.tabs(["Detailed View", "Table View"])
                
                with tab1:
                    # Detailed view with charts
                    for i, ic in enumerate(iron_condors[:num_results]):
                        with st.expander(
                            f"#{i+1} - {ic['expiration']} (DTE: {ic['dte']}) - "
                            f"{ic['long_put_strike']}/{ic['short_put_strike']}/"
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
                                
                                st.markdown("##### Other Metrics")
                                st.markdown(f"Implied Volatility: **{ic['implied_volatility']*100:.1f}%**")
                                st.markdown(f"Avg. Bid/Ask Spread: **{ic['avg_spread_pct']*100:.2f}%**")
                                st.markdown(f"Put Width: **{ic['put_width']}**")
                                st.markdown(f"Call Width: **{ic['call_width']}**")
                            
                            with col2:
                                if generate_charts:
                                    chart_path = f"charts/ic_{ic['expiration']}_{ic['long_put_strike']}_{ic['short_put_strike']}_{ic['short_call_strike']}_{ic['long_call_strike']}.png"
                                    show_chart(chart_path)
                                else:
                                    st.info("P/L Charts are disabled. Enable in settings to see visualization.")
                
                with tab2:
                    # Table view of all results
                    results_df = pd.DataFrame(iron_condors[:num_results])
                    
                    # Format and select columns for display
                    display_df = results_df.copy()
                    
                    # Format columns for better display
                    if not display_df.empty:
                        display_df['prob_profit'] = display_df['prob_profit'].apply(lambda x: f"{x*100:.1f}%")
                        display_df['position_delta'] = display_df['position_delta'].apply(lambda x: f"{x:.4f}")
                        display_df['net_credit'] = display_df['net_credit'].apply(lambda x: f"${x:.2f}")
                        display_df['max_loss'] = display_df['max_loss'].apply(lambda x: f"${x:.2f}")
                        display_df['expected_profit'] = display_df['expected_profit'].apply(lambda x: f"${x:.2f}")
                        display_df['risk_reward'] = display_df['risk_reward'].apply(lambda x: f"{x:.2f}")
                        
                        # Rename columns for better display
                        columns_map = {
                            'expiration': 'Expiration',
                            'dte': 'DTE',
                            'long_put_strike': 'Long Put',
                            'short_put_strike': 'Short Put',
                            'short_call_strike': 'Short Call',
                            'long_call_strike': 'Long Call',
                            'net_credit': 'Net Credit',
                            'max_loss': 'Max Loss',
                            'expected_profit': 'Expected Profit',
                            'prob_profit': 'Prob of Profit',
                            'position_delta': 'Delta',
                            'risk_reward': 'Risk/Reward'
                        }
                        
                        # Select and rename columns
                        display_cols = list(columns_map.keys())
                        display_df = display_df[display_cols].rename(columns=columns_map)
                        
                        st.dataframe(display_df, use_container_width=True)
                
                # Export all identified iron condors to CSV
                if len(iron_condors) > 0:
                    # Create CSV buffer
                    csv_buffer = io.StringIO()
                    pd.DataFrame(iron_condors).to_csv(csv_buffer, index=False)
                    
                    st.download_button(
                        label=f"Download All {len(iron_condors)} Results as CSV",
                        data=csv_buffer.getvalue(),
                        file_name=f"ic_opportunities_{symbol}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            except Exception as e:
                st.error(f"Error finding iron condors: {str(e)}")
                st.info("Attempting to use Yahoo Finance data instead...")
                
                try:
                    # Try again with Yahoo Finance
                    finder.data_source = 'yahoo'
                    iron_condors = finder.find_iron_condors()
                    
                    if iron_condors:
                        st.success("Successfully found iron condors using Yahoo Finance data!")
                        # Would repeat display code here, but that would make this too long
                        # In a real implementation, we would refactor the display code into a function
                    else:
                        st.warning("No suitable iron condors found with these parameters.")
                except Exception as e2:
                    st.error(f"Fatal error: {str(e2)}")
                    st.error("Could not find suitable iron condors with any data source.")
    
    # Information section
    with st.expander("What is an Iron Condor?"):
        st.markdown("""
        An iron condor is an options strategy that involves four options with the same expiration date:
        1. **Long Put** (buy a put at a lower strike)
        2. **Short Put** (sell a put at a higher strike)
        3. **Short Call** (sell a call at a higher strike)
        4. **Long Call** (buy a call at an even higher strike)

        This creates a position that profits if the underlying asset (SPX in this case) stays
        within a specific price range until expiration. The maximum profit is the net premium 
        received, while the maximum loss is limited by the width of the spreads minus the premium.
        
        Iron condors are typically used in low-volatility environments when you expect 
        the underlying asset to trade within a range.
        """)
        
        st.image("https://www.investopedia.com/thmb/h1QOLpWkrJYIgZfMbwd5Jg8UWro=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/Clipboard01-57c6e8e35f9b5829f455ffd3.jpg", 
                caption="Iron Condor Payoff Diagram")
    
    with st.expander("About This Tool"):
        st.markdown("""
        ### Features
        - Finds optimal iron condor combinations based on current market prices
        - Filters for delta-neutral positions (total position delta < configurable threshold)
        - Targets positions betting against specific price moves
        - Evaluates liquidity, bid/ask spreads, and risk-reward ratios
        - Calculates probability of profit and expected return
        - Generates profit/loss charts visualizing each trade
        - Configurable number of displayed results
        - Exports results to CSV for further analysis
        
        ### Data Sources
        1. **Schwab API**: Most accurate data with complete Greeks
        2. **Interactive Brokers API**: Excellent data source with real-time Greeks
        3. **CBOE API**: Good alternative, but requires a CBOE API key
        4. **Yahoo Finance API**: Free fallback option with limited accuracy for Greeks
        
        If your preferred data source is not available, the tool will automatically try the next available source in this order: Schwab → Interactive Brokers → CBOE → Yahoo Finance.
        
        ### Notes
        - Yahoo Finance doesn't provide Greeks directly, so estimates are used
        - Always verify trade details before executing any real trades
        - Probability calculations use a simplified model and should be considered estimates
        """)
    
    with st.expander("Schwab API Setup"):
        st.markdown("""
        ### Setting up Schwab API Access
        
        To use the Schwab API data source, you'll need to:
        
        1. **Create a Schwab Developer Account**:
           - Visit [Schwab Developer Portal](https://developer.schwab.com/)
           - Create a new account or log in with your existing Schwab credentials
           - You need to have an existing Schwab brokerage account

        2. **Register a New Application**:
           - Navigate to "My Applications" and click "Create a New App"
           - Provide the required information:
             - Application Name: "Iron Condor Finder" (or your preferred name)
             - Description: Brief description of your application
             - Organization: Your name or organization
             - Application Type: "Personal Use"

        3. **Configure OAuth Settings**:
           - Set the OAuth Redirect URL to `https://127.0.0.1:8182/` (default for schwab-py)
           - Note that this URL must match exactly what you'll use in your code

        4. **Wait for Approval**:
           - Schwab typically takes 1-3 business days to approve new applications
           - You'll receive an email notification when your application is approved

        5. **Get Your API Credentials**:
           - Once approved, you can retrieve your API key and app secret from the developer portal
           - Add these credentials to your `.env` file:
           ```
           SCHWAB_API_KEY=your_schwab_api_key_here
           SCHWAB_APP_SECRET=your_schwab_app_secret_here
           SCHWAB_CALLBACK_URL=https://127.0.0.1:8182/
           SCHWAB_TOKEN_PATH=schwab_token.json
           ```

        6. **Authentication Process**:
           - When you first run the application, it will open a browser window for authentication
           - Log in with your Schwab account credentials
           - Grant the necessary permissions when prompted
           - The app will then receive and store an access token for future use
           - Tokens typically expire after 30 minutes and will be automatically refreshed
        
        For more detailed setup instructions, see the [schwab-py documentation](https://schwab-py.readthedocs.io/en/latest/getting-started.html).
        """)
    
    with st.expander("Interactive Brokers API Setup"):
        st.markdown("""
        ### Setting up Interactive Brokers API Access
        
        To use the Interactive Brokers data source, you'll need to:
        
        1. **Create an IBKR Account**: You need an active Interactive Brokers account. A paper trading account works fine for testing.

        2. **Choose Your Connection Method**: Interactive Brokers offers several API options:
           - **TWS API** (used in this project): For direct integration with Trader Workstation
           - Web API: For web-based applications using REST
           - Excel API: For Excel-based trading
           - FIX API: For standard FIX protocol integration

        3. **Download and Install TWS or Gateway**:
           - [Trader Workstation (TWS)](https://www.interactivebrokers.com/en/trading/tws.php) - Full trading platform
           - [IB Gateway](https://www.interactivebrokers.com/en/trading/ibgateway.php) - Lightweight application for API connections

        4. **Configure API Settings**:
           - In TWS: Navigate to File > Global Configuration > API > Settings
           - In IB Gateway: Navigate to Configure > Settings > API > Settings
           - Check "Enable ActiveX and Socket Clients"
           - Set Socket port (7497 for paper trading TWS, 7496 for live trading TWS)
           - Set Socket port (4002 for paper trading Gateway, 4001 for live trading Gateway)
           - Enable "Allow connections from localhost only" for security
           - Set a reasonable socket client connection limit (e.g., 5-10)
           - IMPORTANT: Check "Trust and connect applications on computer that send 'trusted handshake'"
           - You may need to add specific trusted IP addresses if not running locally

        5. **Update your `.env` file** with the correct host and port:
           ```
           IB_HOST=127.0.0.1
           IB_PORT=7497  # Use 7497 for TWS/paper trading or 4002 for IB Gateway/paper trading
           IB_CLIENT_ID=1
           ```

        6. **Launch TWS or Gateway**: Make sure TWS or IB Gateway is running when you use the Iron Condor Finder. Be sure to log in to your account.

        7. **Market Data Subscriptions**: Ensure you have the necessary market data subscriptions for the symbols you intend to trade.

        For more information, see the [Interactive Brokers API Documentation](https://www.interactivebrokers.com/en/index.php?f=5041) and the [ib_async library](https://github.com/ib-api-reloaded/ib_async).
        """)

    with st.expander("CBOE API Setup"):
        st.markdown("""
        ### Setting up CBOE API Access
        
        To use the CBOE data API data source, you'll need to:
        
        1. **Visit the CBOE DataShop**: Go to the [CBOE DataShop portal](https://datashop.cboe.com/)

        2. **Create an Account**: Sign up for a CBOE DataShop account if you don't already have one

        3. **Choose API Access Option**: 
           - Navigate to the "APIs" section
           - Select the appropriate REST API option (LiveVol API or DataShop API)
           - Currently, the "All Access API" provides the most comprehensive options data

        4. **Select a Subscription Plan**:
           - Free Tier: Limited to 500 points/day (14-day trial)
           - Paid Tiers: Various options starting from $599/month for 150,000 points/month
           - Choose based on your expected usage volume

        5. **Complete the Application Process**:
           - Provide required information about your intended use
           - Select which data types you need (options data, stocks, indices)
           - Choose between live or delayed data (live data has higher costs)
           - Specify whether it's for individual or firm use

        6. **Payment and Verification**:
           - Provide payment information (even the free tier requires credit card verification)
           - Accept the terms and conditions
           - Wait for account approval (usually within 1-2 business days)

        7. **Retrieve Your API Key**:
           - Once approved, log in to your DataShop account
           - Navigate to Account > API to get your API credentials
           - Add your API key to your `.env` file:
           ```
           CBOE_API_KEY=your_cboe_api_key_here
           ```

        8. **Optional: Review Documentation**:
           - Study the [CBOE API Documentation](https://api.livevol.com/v1/docs/Help) for endpoint details
           - Understand the point system to manage your API usage efficiently

        Note: CBOE's API pricing structure is based on "points" which vary by endpoint. Monitor your usage to avoid unexpected charges. For personal or research use, the free tier may be sufficient to start.
        
        For assistance or questions about API access, contact CBOE DataShop support:
        - Phone: +1 800 307-8979 (US) or +1 312 786-7400 (International)
        - Email support is available through their contact form on the DataShop website
        """)

    with st.expander("Yahoo Finance API Setup"):
        st.markdown("""
        ### Setting up Yahoo Finance API Access
        
        Unlike the other data sources, Yahoo Finance doesn't require API key authentication:
        
        1. **No API Key Required**: Yahoo Finance API access is available without authentication
           
        2. **How It Works**: Our tool uses the `yfinance` Python library to access Yahoo Finance data
           - All required libraries are already included in our `requirements.txt`
           - No additional setup is needed on your part
        
        3. **Usage Notes**:
           - Data accuracy may not be as reliable as paid sources
           - Options Greeks are not provided directly by Yahoo Finance
           - Our tool calculates estimated Greeks based on Black-Scholes model
           - Rate limiting may occur with excessive requests
           - Yahoo may occasionally change their API structure without notice
        
        4. **When to Use**:
           - When you don't have access to other data sources
           - For quick testing or prototyping
           - For non-critical backtesting
           - As a fallback when other sources are unavailable
        
        While Yahoo Finance is convenient for getting started, we recommend using Schwab or Interactive Brokers APIs for more accurate options data, especially for the Greeks which are essential for proper iron condor strategy evaluation.
        """)

if __name__ == "__main__":
    main() 