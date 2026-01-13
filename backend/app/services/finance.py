
import yfinance as yf
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlmodel import Session, select, desc
from app.database import engine
from app.models import Company, FinancialStatement

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
    def sync_financials(ticker: str, session: Session = None):
        """
        Fetch financials from yfinance and save to database.
        """
        print(f"Syncing financials for {ticker}...")
        local_session = False
        if not session:
            session = Session(engine)
            local_session = True
            
        try:
            # Get company ID
            company = session.exec(select(Company).where(Company.ticker == ticker)).first()
            if not company:
                print(f"Company {ticker} not found in DB")
                return

            stock = yf.Ticker(ticker)
            
            # Helper to convert DataFrame to dict safely
            def df_to_dict(df):
                if df is None or df.empty:
                    return {}
                df = df.astype(object).where(df.notnull(), None)
                # Convert timestamp keys to string
                return {k.strftime('%Y-%m-%d') if hasattr(k, 'strftime') else str(k): v for k, v in df.to_dict().items()}
            
            data_map = {
                "income_statement": df_to_dict(stock.income_stmt),
                "balance_sheet": df_to_dict(stock.balance_sheet),
                "cash_flow": df_to_dict(stock.cashflow)
            }
            
            for stmt_type, periods_data in data_map.items():
                for period, data in periods_data.items():
                    # Check existing
                    statement = session.exec(select(FinancialStatement).where(
                        FinancialStatement.company_id == company.id,
                        FinancialStatement.period == period,
                        FinancialStatement.statement_type == stmt_type
                    )).first()
                    
                    if statement:
                        statement.data = data
                        statement.fetched_at = datetime.now(timezone.utc)
                        session.add(statement)
                    else:
                        new_stmt = FinancialStatement(
                            company_id=company.id,
                            period=period,
                            statement_type=stmt_type,
                            data=data,
                            fetched_at=datetime.now(timezone.utc)
                        )
                        session.add(new_stmt)
            
            session.commit()
            print(f"Synced financials for {ticker}")
            
        except Exception as e:
            print(f"Error syncing financials for {ticker}: {e}")
        finally:
            if local_session:
                session.close()

    @staticmethod
    def get_financials(ticker: str) -> Dict[str, Any]:
        """
        Fetch financial statements from DB. If not present, sync first.
        """
        with Session(engine) as session:
            company = session.exec(select(Company).where(Company.ticker == ticker)).first()
            if not company:
                return {}
                
            # Check if we have data
            stmts = session.exec(select(FinancialStatement).where(
                FinancialStatement.company_id == company.id
            )).all()
            
            if not stmts:
                FinanceService.sync_financials(ticker, session)
                stmts = session.exec(select(FinancialStatement).where(
                    FinancialStatement.company_id == company.id
                )).all()
            
            # Group by type
            result = {
                "income_statement": {},
                "balance_sheet": {},
                "cash_flow": {}
            }
            
            for stmt in stmts:
                if stmt.statement_type in result:
                    result[stmt.statement_type][stmt.period] = stmt.data
            
            return result


    @staticmethod
    def get_financials_context(ticker: str) -> str:
        """
        Get financials formatted for LLM context.
        """
        data = FinanceService.get_financials(ticker)
        if not data:
            return ""
            
        summary = f"Financial Data for {ticker}:\n"
        
        # Helper to get latest year column
        def get_latest(stmt_data):
            if not stmt_data: return None, {}
            # Sort keys (dates) descending
            dates = sorted(stmt_data.keys(), reverse=True)
            if not dates: return None, {}
            return dates[0], stmt_data[dates[0]]

        # Income Statement
        date, inc = get_latest(data.get("income_statement"))
        if date:
            summary += f"[Income Statement {date}]\n"
            keys = ["Total Revenue", "Net Income", "EBITDA", "Gross Profit"]
            for k in keys:
                if k in inc: summary += f"  {k}: {inc[k]}\n"
        
        # Balance Sheet
        date, bal = get_latest(data.get("balance_sheet"))
        if date:
            summary += f"[Balance Sheet {date}]\n"
            keys = ["Total Assets", "Total Liabilities Net Minority Interest", "Total Equity Gross Minority Interest", "Cash And Cash Equivalents"]
            for k in keys:
                if k in bal: summary += f"  {k}: {bal[k]}\n"

        # Cash Flow
        date, cf = get_latest(data.get("cash_flow"))
        if date:
            summary += f"[Cash Flow {date}]\n"
            keys = ["Operating Cash Flow", "Free Cash Flow", "Capital Expenditure"]
            for k in keys:
                if k in cf: summary += f"  {k}: {cf[k]}\n"
                
        return summary + "\n"

finance_service = FinanceService()
