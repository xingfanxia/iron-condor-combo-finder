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

For detailed instructions on setting up API access for each data source, please refer to the [API Setup Guide](docs/data_source_api_setup.md).

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