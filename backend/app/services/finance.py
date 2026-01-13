
import yfinance as yf
from typing import Dict, Any, Optional

class FinanceService:
    @staticmethod
    def get_company_info(ticker: str) -> Dict[str, Any]:
        """
        Fetch basic company info from yfinance.
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                "name": info.get("longName") or info.get("shortName") or ticker,
                "ticker": ticker.upper(),
                "sector": info.get("sector"),
                "sub_sector": info.get("industry"),
                "website_url": info.get("website")
            }
        except Exception as e:
            print(f"Error fetching info for {ticker}: {e}")
            return None

    @staticmethod
    def get_financials(ticker: str) -> Dict[str, Any]:
        """
        Fetch financial statements (Income, Balance, Cash Flow) from yfinance.
        """
        try:
            stock = yf.Ticker(ticker)
            
            # Helper to convert DataFrame to dict safely
            def df_to_dict(df):
                if df is None or df.empty:
                    return {}
                # Handle NaN values which cause JSON error
                # Handle NaN values which cause JSON error
                # Use where logic: keep value if not null, else replace with None. 
                # Cast to object first so None is preserved and not cast back to NaN.
                df = df.astype(object).where(df.notnull(), None)
                # Convert timestamp keys to string strings for JSON serialization
                return {k.strftime('%Y-%m-%d') if hasattr(k, 'strftime') else str(k): v for k, v in df.to_dict().items()}

            income = df_to_dict(stock.income_stmt)
            balance = df_to_dict(stock.balance_sheet)
            cashflow = df_to_dict(stock.cashflow)
            
            return {
                "income_statement": income,
                "balance_sheet": balance,
                "cash_flow": cashflow
            }
        except Exception as e:
            print(f"Error fetching financials for {ticker}: {e}")
            return {}


finance_service = FinanceService()
