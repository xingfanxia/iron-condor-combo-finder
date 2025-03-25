import os
import sys
from pathlib import Path

# Add the project root to the Python path so we can import modules correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from schwab.auth import easy_client
from schwab.client import Client

# Load environment variables from .env file
load_dotenv()

def test_schwab_connection():
    # Initialize the Schwab client
    client = easy_client(
        api_key=os.getenv('SCHWAB_API_KEY'),
        app_secret=os.getenv('SCHWAB_APP_SECRET'),
        callback_url=os.getenv('SCHWAB_CALLBACK_URL'),
        token_path=os.getenv('SCHWAB_TOKEN_PATH')
    )
    
    try:
        # No need to call login() with easy_client
        print("✅ Authentication successful!")
        
        # Use $SPX symbol for the S&P 500 Index
        spx_symbol = '$SPX'
        print(f"\nGetting quote for {spx_symbol}...")
        quote_response = client.get_quotes(symbols=[spx_symbol])
        quote = quote_response.json()
        
        if spx_symbol in quote and 'quote' in quote[spx_symbol] and 'lastPrice' in quote[spx_symbol]['quote']:
            current_price = quote[spx_symbol]['quote']['lastPrice']
            print(f"✅ Successfully retrieved S&P 500 quote: ${current_price}")
        else:
            print(f"❌ Could not get price for {spx_symbol}. Raw response: {quote}")
            return False
            
        # Try to get option chain with the S&P 500 symbol
        print(f"\nGetting options chain for {spx_symbol}...")
        option_chain_response = client.get_option_chain(
            symbol=spx_symbol,
            contract_type=Client.Options.ContractType.ALL,
            strike_count=5
        )
        option_chain = option_chain_response.json()
        
        # Check if we have expiration dates in the response
        if 'callExpDateMap' in option_chain and option_chain['callExpDateMap']:
            expirations = list(option_chain['callExpDateMap'].keys())
            if expirations:
                print(f"✅ Successfully retrieved options chain!")
                print(f"Available expirations: {', '.join(expirations[:3])}...")
            else:
                print("No expiration dates found in the options chain.")
        else:
            print("Options chain format is different than expected, raw response:", option_chain)
        
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Schwab API connection...")
    success = test_schwab_connection()
    
    if success:
        print("\n🎉 All tests passed! Your Schwab API connection is working correctly.")
    else:
        print("\n⚠️ Test failed. Please check your API credentials and try again.") 