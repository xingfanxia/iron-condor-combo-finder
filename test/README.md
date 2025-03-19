# Iron Condor Finder Tests

This directory contains unit tests for the Iron Condor Finder application. The tests use pytest and mock data to validate the functionality of the application without requiring real API access.

## Test Structure

- `conftest.py`: Contains common test fixtures including mock option data
- `data_sources/`: Tests for data source implementations
  - `mock_data_source.py`: A mock data source implementation for testing
  - `test_mock_data_source.py`: Tests for the mock data source
- `test_analysis.py`: Tests for the options analysis functionality
- `test_ic_finder.py`: Tests for the main IronCondorFinder class
- `test_utilities.py`: Tests for utility functions
- `test_visualization.py`: Tests for chart generation
- `test_basic_iron_condor_finder.py`: Simple test showing the core iron condor finding algorithm with mock data

## Setup

Install the test dependencies:

```bash
pip install -r test-requirements.txt
```

## Running Tests

To run all tests:

```bash
pytest
```

To run a specific test file:

```bash
pytest test/test_analysis.py
```

To run tests with verbose output:

```bash
pytest -v
```

To run tests with code coverage:

```bash
pytest --cov=src
```

## Mock Data

The tests use mock option data that simulates a typical options chain for SPX with various strikes and expirations. The mock data includes:

- Multiple expiration dates
- Realistic option prices and Greeks
- Appropriate bid/ask spreads
- Simulated liquidity metrics (volume and open interest)

This allows us to test the iron condor finding algorithm and analysis functions without needing real market data.

## Adding New Tests

When adding new functionality to the application, please add corresponding tests. The general pattern is:

1. Create fixtures for any required test data in `conftest.py` or in the test file
2. Use mocking for any external dependencies
3. Test both the happy path and error conditions
4. For data manipulation functions, verify the output has the expected structure and values

## Testing Data Sources

For testing actual data source implementations (like Schwab or Interactive Brokers):

1. Create a subclass of the source-specific test in `test/data_sources/`
2. Use VCR or similar tools to record and replay API responses
3. Add appropriate environment variables in CI to skip integration tests that require credentials

Note: Don't commit real API credentials to the repository, even in test fixtures. 