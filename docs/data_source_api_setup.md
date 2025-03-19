# API Access Setup

This document provides detailed instructions for setting up API access with each of the supported data sources for the Iron Condor Option Strategy Finder.

## Table of Contents

- [Schwab API](#schwab-api)
- [Interactive Brokers API](#interactive-brokers-api)
- [CBOE API](#cboe-api)
- [Yahoo Finance API](#yahoo-finance-api)

## Schwab API

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

## Interactive Brokers API

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

## CBOE API

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

## Yahoo Finance API

Unlike the other data sources, Yahoo Finance doesn't require API key authentication. Our tool uses the `yfinance` Python library to access Yahoo Finance data.

### Setting up Yahoo Finance:

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