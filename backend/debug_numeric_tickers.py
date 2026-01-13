
import yfinance as yf
import json

def test_ticker(ticker):
    print(f"\n--- Testing {ticker} ---")
    stock = yf.Ticker(ticker)
    
    # Check Income Statement
    inc = stock.income_stmt
    if inc is not None and not inc.empty:
        print(f"SUCCESS: Found {len(inc.columns)} columns in Income Statement.")
        print(inc.head(2))
    else:
        print("FAILURE: No Income Statement data.")

if __name__ == "__main__":
    # Test User's screenshot examples
    test_ticker("1155.KL")  # Maybank Numeric
    test_ticker("MAYBANK.KL") # My previous attempt
    
    test_ticker("1023.KL")  # CIMB Numeric (Derived, need to verify if 1023 is CIMB, actually CIMB is 1023)
    test_ticker("CIMB.KL")
    
    test_ticker("1015.KL") # AMMB from screenshot
    test_ticker("AMBANK.KL") 
