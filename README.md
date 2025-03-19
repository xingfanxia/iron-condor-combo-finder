# Iron Condor Option Strategy Finder

A comprehensive tool to discover and analyze optimal iron condor option strategies that are delta-neutral and aligned with your market outlook. This application helps traders find profitable iron condor combinations for indexes (like SPX) or any supported symbol, with a focus on strategies that bet against specific percentage price moves.

## Tool Overview

This application solves several key challenges for options traders:

1. **Finding Delta-Neutral Strategies**: Automatically identifies iron condor combinations with near-zero delta, reducing directional exposure
2. **Market Movement Forecasting**: Targets strategies that profit if the underlying stays within your specified price range (default 2%)
3. **Risk Management**: Evaluates risk/reward ratios, probability of profit, and expected returns
4. **Data Source Flexibility**: Connects to multiple data providers (Schwab, Interactive Brokers, CBOE, Yahoo Finance)
5. **Visualization**: Generates detailed profit/loss charts for each opportunity
6. **User-Friendly Interface**: Available via both web UI (Streamlit) and command line

## What is an Iron Condor?

An iron condor is an options strategy that involves four options with the same expiration date:
1. Long Put (buy a put at a lower strike)
2. Short Put (sell a put at a higher strike)
3. Short Call (sell a call at a higher strike)
4. Long Call (buy a call at an even higher strike)

This creates a position that profits if the underlying asset (SPX in this case) stays within a specific price range until expiration. Iron condors are primarily used to:
- Generate income in low-volatility or range-bound markets
- Take advantage of time decay (theta)
- Profit from overpriced options when implied volatility is high

## Features

- Finds optimal iron condor combinations based on current market prices
- Filters for delta-neutral positions (total position delta < configurable threshold)
- Targets positions betting against specific price moves (configurable percentage)
- Evaluates liquidity, bid/ask spreads, and risk-reward ratios
- Calculates probability of profit and expected return
- Generates profit/loss charts visualizing each trade
- Configurable number of displayed results
- Exports results to CSV for further analysis
- Multiple data source options with automatic fallback
- Interactive web user interface with intuitive parameter controls

## System Requirements

- Python 3.10 or higher (required for schwab-py and ib_async libraries)
- Internet connection for API access
- Recommended: API access to at least one of the supported data sources
- For Interactive Brokers: TWS or IB Gateway running

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project directory with your API keys:
   ```
   # Copy from .env.example and add your API keys
   cp .env.example .env
   ```
   Then edit the `.env` file to add your configuration for your preferred data sources (see API Access Setup section below).

## Project Architecture

The project follows a modular design pattern for maintainability and extensibility:

- `src/`: Contains the core Python modules
  - `ic_finder.py`: Main module coordinating all components
  - `data_sources/`: Package containing different data source implementations
    - `base.py`: Base class defining the data source interface
    - `schwab.py`, `ib.py`, `cboe.py`, `yahoo.py`: Specific implementations
    - `factory.py`: Factory function to create appropriate data source
  - `analysis.py`: Options calculations and iron condor algorithms
  - `visualization.py`: P/L chart generation
  - `utilities.py`: Helper functions and utilities
- `app.py`: Streamlit web interface
- `charts/`: Generated P/L visualization charts
- `docs/`: Documentation and screenshots

### Class Design

The modular architecture allows for:

1. **Pluggable Data Sources**: Any data source that implements the `DataSourceBase` interface can be used
2. **Configurable Parameters**: All key parameters can be adjusted through the UI or command line
3. **Separation of Concerns**: 
   - Data retrieval (data_sources)
   - Analysis and strategy finding (analysis)
   - Visualization (visualization)
   - Helper functions (utilities)
   - User interface (app.py)
4. **Extensibility**: New data sources or analysis methods can be added without modifying existing code

## Usage

### Web User Interface (Recommended)

The easiest way to use the tool is through the interactive web UI:

```
streamlit run app.py
```

This will launch a web interface in your browser with:

1. **Configuration Panel (Left Sidebar)**:
   - Symbol selection (default: SPX)
   - Data source selection (Schwab, Interactive Brokers, CBOE, Yahoo)
   - Maximum movement percentage (default: 2%)
   - Maximum position delta (default: 0.01)
   - Days to expiration range
   - Minimum liquidity threshold
   - Number of results to display
   - Chart generation toggle
   - Sort method selection

2. **Results Display (Main Panel)**:
   - Current price and target price range
   - Tabbed interface with detailed and table views
   - Expandable sections for each iron condor opportunity
   - Interactive P/L charts
   - CSV export functionality

3. **Information Panels**:
   - Iron condor explanation
   - Tool features and capabilities
   - Data source setup instructions

![Streamlit UI Screenshot](docs/ui_screenshot.png)

### Command Line Interface

For scripting or batch processing, you can use the command-line interface:

```
python -m src.ic_finder
```

Default parameters can be modified in the `ic_finder.py` file, or by creating a custom script that imports the `IronCondorFinder` class:

```python
from src.ic_finder import IronCondorFinder

finder = IronCondorFinder(
    symbol='SPX',            # Symbol to analyze
    max_move_pct=2.0,        # Maximum expected movement (%)
    max_delta=0.01,          # Maximum position delta
    min_dte=1,               # Minimum days to expiration
    max_dte=3,               # Maximum days to expiration
    min_liquidity=50,        # Minimum option volume
    data_source='schwab',    # Data source to use
    num_results=5,           # Number of results to display
    generate_charts=True     # Whether to generate P/L charts
)

iron_condors = finder.find_iron_condors()
```

### Data Sources

1. **Schwab API**: Most accurate data with complete Greeks
2. **Interactive Brokers API**: Excellent data source with real-time Greeks
3. **CBOE API**: Good alternative, but requires a CBOE API key
4. **Yahoo Finance API**: Free fallback option with limited accuracy for Greeks

If your preferred data source is not available, the tool will automatically try the next available source in this order: Schwab → Interactive Brokers → CBOE → Yahoo Finance.

## API Access Setup

### Schwab API

To set up Schwab API access:

1. **Create a Schwab Developer Account**:
   - Visit the [Schwab Developer Portal](https://developer.schwab.com/)
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

7. **Installation Notes**:
   - Our project uses the `schwab-py` library (included in requirements.txt)
   - The library requires Python 3.10 or higher
   - If you're transitioning from TDAmeritrade, note that options symbols and equity index symbols are formatted differently

8. **Useful Resources**:
   - [schwab-py Documentation](https://schwab-py.readthedocs.io/)
   - [schwab-py GitHub Repository](https://github.com/alexgolec/schwab-py)

For more detailed setup instructions, see the [schwab-py documentation](https://schwab-py.readthedocs.io/en/latest/getting-started.html).

### Interactive Brokers API

To set up Interactive Brokers API access:

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

8. **Paper Trading First**: It's recommended to test with paper trading before using live accounts.

For troubleshooting and more detailed information:
- [Interactive Brokers API Documentation](https://www.interactivebrokers.com/en/index.php?f=5041)
- [ib_async library](https://github.com/ib-api-reloaded/ib_async)
- [IBKR Campus API Courses](https://www.interactivebrokers.com/campus/ibkr-api-page/getting-started/)
- [IBKR Quant Blog](https://www.interactivebrokers.com/en/trading/ib-api.php) - Articles on programming with IBKR APIs

### CBOE API

To set up CBOE data API access:

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

### Yahoo Finance API

Unlike the other data sources, Yahoo Finance doesn't require API key authentication. Our tool uses the `yfinance` Python library to access Yahoo Finance data.

#### Setting up Yahoo Finance:

1. **No API Key Required**: Yahoo Finance API access is available without authentication
   
2. **Install the yfinance Library**:
   ```
   pip install yfinance
   ```
   Note: This is already included in our `requirements.txt`

3. **Basic Usage in Code**:
   ```python
   import yfinance as yf
   
   # Get ticker data
   ticker = yf.Ticker("SPX")
   
   # Get available options expiration dates
   expirations = ticker.options
   
   # Get options chain for a specific expiration date
   options = ticker.option_chain(expirations[0])
   
   # Separate calls and puts
   calls = options.calls
   puts = options.puts
   ```

4. **Limitations to Be Aware Of**:
   - Data accuracy may not be as reliable as paid sources
   - Options Greeks are not provided directly (our tool calculates estimates)
   - Rate limiting may occur with excessive requests
   - Yahoo may occasionally change their API structure without notice
   - Historical options data is limited

5. **Usage Guidelines**:
   - Add delays between requests to avoid rate limiting
   - Implement error handling for API changes
   - Verify critical data with additional sources before trading

While Yahoo Finance is a convenient fallback option, we recommend using Schwab or Interactive Brokers APIs for more accurate and complete options data, especially for the Greeks which are essential for iron condor strategy evaluation.

## Output

The tool provides comprehensive output in multiple formats:

### Web Interface Display

The web interface provides an interactive view of results with:
- Detailed view with expandable sections for each iron condor
- Table view for easy comparison of multiple strategies
- Interactive P/L charts
- Downloadable CSV export

### Command Line Output

When run from the command line, the output includes:
- Current price and target price range
- Detailed information for each identified iron condor
- Path to saved P/L charts
- Path to exported CSV file

Example:
```
Current SPX price: $5300.50
Looking for iron condors that profit if SPX stays between $5194.49 and $5406.51

Top 5 Iron Condor Opportunities:
--------------------------------------------------
#1 - Expiration: 2023-05-19 (DTE: 2)
Structure: 5100.0/5150.0/5450.0/5500.0
Net Credit: $4.35 | Max Loss: $45.65
Expected Profit: $2.17 | Prob of Profit: 68.5%
Greeks - Delta: 0.0082 | Gamma: 0.0022 | Theta: $1.48 | Vega: -0.0845
Risk/Reward: 10.49 | Avg Spread: 3.82%
Implied Volatility: 22.5%
P/L chart saved: charts/ic_2023-05-19_5100.0_5150.0_5450.0_5500.0.png
...
```

### Profit/Loss Charts

For each iron condor opportunity, the tool generates a detailed profit/loss chart showing:
- Profit/loss profile across different potential prices
- Key strike prices and breakeven points
- Current price of the underlying
- Profitable (green) and unprofitable (red) regions
- Max profit and loss values
- Probability of profit

The charts are saved to the `charts/` directory with filenames that include the expiration and strikes.

![Sample P/L Chart](charts/sample_chart.png)

### CSV Export

The exported CSV includes all found iron condors with detailed metrics for each trade, including:
- Expiration date and DTE (days to expiration)
- Strike prices for all four legs
- Net credit and maximum loss
- Expected profit and probability of profit
- All Greeks (delta, gamma, theta, vega)
- Risk/reward ratio and bid/ask spread percentage

## Key Metrics Explained

The tool evaluates iron condor strategies using several important metrics:

1. **Net Credit**: The amount received when opening the position
2. **Max Loss**: The maximum potential loss (usually width between spreads minus net credit)
3. **Probability of Profit**: Estimated likelihood of the strategy being profitable at expiration
4. **Expected Profit**: Probability-weighted average profit
5. **Risk/Reward Ratio**: The ratio of max loss to max profit (lower is better)
6. **Position Delta**: Overall directional exposure (closer to zero is more market-neutral)
7. **Position Theta**: Daily time decay benefit
8. **Position Vega**: Exposure to changes in implied volatility
9. **Implied Volatility**: Average IV across the four options
10. **Bid/Ask Spread**: Average spread as a percentage (lower means better liquidity)

## Advanced Usage

### Custom Analysis

You can extend the analysis by modifying the `OptionsAnalysis` class in `src/analysis.py`. Key areas for customization:

- Probability calculation methods
- Filtering criteria for iron condors
- Risk-reward evaluation algorithms
- Greeks calculations and thresholds

### Custom Data Sources

To add a new data source:

1. Create a new class in the `src/data_sources/` directory that inherits from `DataSourceBase`
2. Implement the required methods: `get_current_price()` and `get_options_chain()`
3. Add your data source to the factory function in `src/data_sources/factory.py`

### Batch Processing

For analyzing multiple symbols or parameter combinations:

```python
from src.ic_finder import IronCondorFinder

symbols = ['SPX', 'NDX', 'RUT']
move_percentages = [1.5, 2.0, 2.5]

for symbol in symbols:
    for move_pct in move_percentages:
        finder = IronCondorFinder(
            symbol=symbol,
            max_move_pct=move_pct,
            # other parameters...
        )
        iron_condors = finder.find_iron_condors()
        # Process results...
```

## Notes and Limitations

- The tool prioritizes the chosen data source but provides graceful fallback options
- If a data source fails, the tool will try alternatives in this order: Schwab → Interactive Brokers → CBOE → Yahoo Finance
- Yahoo Finance doesn't provide Greeks directly, so estimates are used
- Always verify trade details before executing any real trades
- Probability calculations use a simplified model and should be considered estimates
- Requires Python 3.10+ due to schwab-py and ib_async dependency requirements
- Some features may require an active market session (depending on data source)

## Contributing

Contributions are welcome! Areas for potential improvement include:

- Additional data sources
- More sophisticated probability models
- Additional options strategies beyond iron condors
- Performance optimizations for faster analysis
- Enhanced visualization options

## License

This project is open source and available under the MIT License.

## Acknowledgements

- The schwab-py library for Schwab API access
- The ib_async library for Interactive Brokers integration
- Streamlit for the interactive web interface
- All contributors who have helped improve this tool 