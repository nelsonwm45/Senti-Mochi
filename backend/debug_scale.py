
import yfinance as yf
import pandas as pd

def check_scale(ticker):
    print(f"--- Checking Scale for {ticker} ---")
    stock = yf.Ticker(ticker)
    
    inc = stock.income_stmt
    if inc is not None and not inc.empty:
        # Get Total Revenue for the most recent date
        try:
            # yfinance often indices by date.
            # We want to see the raw value.
            # Assuming 'Total Revenue' is a row index.
            if 'Total Revenue' in inc.index:
                print("Total Revenue row found.")
                # Get the first column (most recent)
                val = inc.loc['Total Revenue'].iloc[0]
                print(f"Latest Total Revenue (Raw): {val}")
                print(f"Formatted as Billions: {val / 1e9} B")
                print(f"Formatted as Millions: {val / 1e6} M")
                print(f"Formatted as 'In Thousands': {val / 1000}")
            else:
                print("Total Revenue row NOT found. Available keys:")
                print(inc.index.tolist())
        except Exception as e:
            print(f"Error accessing data: {e}")
            print(inc.head())

if __name__ == "__main__":
    check_scale("1015.KL")
    
    # Also print all keys to help with ordering
    stock = yf.Ticker("1015.KL")
    print("\n--- Income Statement Keys ---")
    print(stock.income_stmt.index.tolist())
    print("\n--- Balance Sheet Keys ---")
    print(stock.balance_sheet.index.tolist())
    print("\n--- Cash Flow Keys ---")
    print(stock.cashflow.index.tolist())
check_scale('1015.KL')
