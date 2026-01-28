"""
Specialized Chat Agents for Agentic RAG.

Each agent is a LangGraph node function that:
1. Retrieves domain-specific data
2. Formats it as chunks with [Source N] citations
3. Appends to state["retrieved_docs"]

Agents:
- financial_chat_agent: SQL-based financial data
- news_chat_agent: semantic news search
- claims_chat_agent: RAG over user documents (pgvector)
- report_chat_agent: RBAC-filtered analysis reports
- sentiment_chat_agent: market sentiment / alerts
"""

from typing import Dict, Any, List
from uuid import UUID, uuid4
from sqlmodel import Session, select, col
from sqlalchemy import text
import os

from app.database import engine
from app.services.chat_agent_state import ChatAgentState


# ---------------------------------------------------------------------------
# Financial Agent – queries SQL tables for raw financial data
# ---------------------------------------------------------------------------

def financial_chat_agent(state: ChatAgentState) -> Dict[str, Any]:
    """Fetch key financial metrics for detected companies."""
    from app.services.finance import finance_service

    company_ids = state.get("company_ids") or []
    if not company_ids:
        return {"retrieved_docs": state.get("retrieved_docs", [])}

    chunks: List[Dict[str, Any]] = list(state.get("retrieved_docs", []))

    with Session(engine) as session:
        from app.models import Company
        for cid in company_ids:
            company = session.get(Company, UUID(cid))
            if not company:
                continue

            try:
                fin_data = finance_service.get_financials(company.ticker)
                if not fin_data:
                    continue

                def get_latest(stmt_data):
                    if not stmt_data:
                        return None, {}
                    dates = sorted(stmt_data.keys(), reverse=True)
                    if not dates:
                        return None, {}
                    return dates[0], stmt_data[dates[0]]

                content = f"Key Financial Metrics for {company.name} ({company.ticker}):\n"
                date_inc, inc = get_latest(fin_data.get("income_statement"))
                if date_inc:
                    for k in ["Total Revenue", "Net Income", "EBITDA", "Gross Profit", "Diluted EPS"]:
                        if k in inc:
                            content += f"{k}: {inc[k]}\n"

                date_bal, bal = get_latest(fin_data.get("balance_sheet"))
                if date_bal:
                    for k in ["Total Assets", "Total Liabilities Net Minority Interest",
                              "Total Equity Gross Minority Interest", "Cash And Cash Equivalents"]:
                        if k in bal:
                            content += f"{k}: {bal[k]}\n"

                date_cf, cf = get_latest(fin_data.get("cash_flow"))
                if date_cf:
                    for k in ["Operating Cash Flow", "Free Cash Flow", "Capital Expenditure"]:
                        if k in cf:
                            content += f"{k}: {cf[k]}\n"

                chunks.append({
                    "id": uuid4(),
                    "document_id": None,
                    "content": content,
                    "page_number": 1,
                    "chunk_index": 0,
                    "metadata": {"type": "financials", "company": company.ticker},
                    "filename": f"Financial Data ({company.name})",
                    "similarity": 1.0,
                    "start_line": None,
                    "end_line": None,
                })
            except Exception as e:
                print(f"[financial_chat_agent] Error for {company.ticker}: {e}")

    return {"retrieved_docs": chunks}


# ---------------------------------------------------------------------------
# News Agent – semantic search over news chunks
# ---------------------------------------------------------------------------

def news_chat_agent(state: ChatAgentState) -> Dict[str, Any]:
    """Perform semantic search on news articles for detected companies."""
    company_ids = state.get("company_ids") or []
    query_embedding = state.get("query_embedding", [])
    if not company_ids or not query_embedding:
        return {"retrieved_docs": state.get("retrieved_docs", [])}

    chunks: List[Dict[str, Any]] = list(state.get("retrieved_docs", []))

    with Session(engine) as session:
        embedding_str = f"[{','.join(map(str, query_embedding))}]"

        for cid in company_ids:
            try:
                query_sql = f"""
                    SELECT
                        nc.id, nc.news_id, nc.content, nc.chunk_index,
                        1 - (nc.embedding <=> '{embedding_str}'::vector) as similarity,
                        na.title, na.published_at, na.source, na.url
                    FROM news_chunks nc
                    JOIN news_articles na ON nc.news_id = na.id
                    WHERE na.company_id = '{cid}'
                    ORDER BY similarity DESC
                    LIMIT 5
                """
                results = session.exec(text(query_sql)).fetchall()

                for row in results:
                    chunks.append({
                        "id": row[0],
                        "document_id": None,
                        "content": row[2],
                        "page_number": 1,
                        "chunk_index": row[3],
                        "metadata": {
                            "type": "news",
                            "source": row[7],
                            "published_at": row[6].strftime('%Y-%m-%d') if row[6] else None,
                            "url": row[8],
                        },
                        "filename": f"News: {row[5]}",
                        "similarity": float(row[4] or 0.0),
                        "start_line": None,
                        "end_line": None,
                        "url": row[8],
                    })

                # Also grab latest article as baseline
                from app.models import NewsArticle
                latest = session.exec(
                    select(NewsArticle)
                    .where(NewsArticle.company_id == UUID(cid))
                    .order_by(NewsArticle.published_at.desc())
                    .limit(1)
                ).first()

                if latest:
                    content_str = (
                        f"[{latest.published_at.strftime('%Y-%m-%d')}] {latest.title} "
                        f"(Source: {latest.source})"
                    )
                    if latest.content:
                        content_str += f"\nSummary: {latest.content[:500]}..."

                    chunks.append({
                        "id": uuid4(),
                        "document_id": None,
                        "content": content_str,
                        "page_number": 1,
                        "chunk_index": 0,
                        "metadata": {"type": "news", "subtype": "latest", "url": latest.url},
                        "filename": f"Latest News: {latest.title}",
                        "similarity": 0.9,
                        "start_line": None,
                        "end_line": None,
                        "url": latest.url,
                    })
            except Exception as e:
                print(f"[news_chat_agent] Error for company {cid}: {e}")

    return {"retrieved_docs": chunks}


# ---------------------------------------------------------------------------
# Claims Agent – RAG search over user-uploaded PDFs/docs (pgvector)
# ---------------------------------------------------------------------------

def claims_chat_agent(state: ChatAgentState) -> Dict[str, Any]:
    """Vector search over user's documents with security isolation."""
    user_id = state.get("user_id")
    query_embedding = state.get("query_embedding", [])
    document_ids = state.get("document_ids")
    company_ids = state.get("company_ids")
    limit = state.get("max_results", 5)

    if not query_embedding:
        return {"retrieved_docs": state.get("retrieved_docs", [])}

    chunks: List[Dict[str, Any]] = list(state.get("retrieved_docs", []))

    with Session(engine) as session:
        embedding_str = f"[{','.join(map(str, query_embedding))}]"

        company_filter = ""
        if company_ids:
            ids_str = ",".join([f"'{c}'" for c in company_ids])
            company_filter = f"AND d.company_id IN ({ids_str}) AND d.is_deleted = false"

        doc_filter = ""
        if document_ids:
            ids_str = ",".join([f"'{d}'" for d in document_ids])
            doc_filter = f"AND d.id IN ({ids_str})"

        query_sql = f"""
            SELECT
                dc.id, dc.document_id, dc.content, dc.page_number,
                dc.chunk_index, dc.metadata_, d.filename, d.user_id,
                1 - (dc.embedding <=> '{embedding_str}'::vector) as similarity,
                dc.start_line, dc.end_line, d.company_id
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE d.user_id = '{user_id}'
              AND d.is_deleted = false
              {company_filter}
              {doc_filter}
              AND 1 - (dc.embedding <=> '{embedding_str}'::vector) >= 0.5
            ORDER BY similarity DESC
            LIMIT {limit}
        """
        results = session.exec(text(query_sql)).fetchall()

        for row in results:
            chunks.append({
                "id": row[0],
                "document_id": row[1],
                "content": row[2],
                "page_number": row[3],
                "chunk_index": row[4],
                "metadata": row[5],
                "filename": row[6],
                "similarity": float(row[8]),
                "start_line": row[9],
                "end_line": row[10],
                "url": f"/api/v1/documents/{row[1]}/download",
            })

    return {"retrieved_docs": chunks}


# ---------------------------------------------------------------------------
# Report Agent – RBAC-filtered analysis reports
# ---------------------------------------------------------------------------

def report_chat_agent(state: ChatAgentState) -> Dict[str, Any]:
    """
    Fetch analysis reports STRICTLY filtered by user role.

    RBAC Rule: If user_role == "MARKET_ANALYST", only return reports
    generated with analysis_persona == "MARKET_ANALYST". No cross-role leakage.
    """
    company_ids = state.get("company_ids") or []
    query_embedding = state.get("query_embedding", [])
    user_role = state.get("analysis_persona", "INVESTOR")

    if not company_ids or not query_embedding:
        return {"retrieved_docs": state.get("retrieved_docs", [])}

    chunks: List[Dict[str, Any]] = list(state.get("retrieved_docs", []))
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    with Session(engine) as session:
        embedding_str = f"[{','.join(map(str, query_embedding))}]"

        for cid in company_ids:
            try:
                # STRICT RBAC filter: only reports matching user's persona
                query_sql = f"""
                    SELECT
                        rc.id, rc.report_id, rc.content, rc.chunk_index,
                        1 - (rc.embedding <=> '{embedding_str}'::vector) as similarity,
                        rc.section_type, c.ticker
                    FROM report_chunks rc
                    JOIN analysis_reports ar ON rc.report_id = ar.id
                    JOIN companies c ON ar.company_id = c.id
                    WHERE ar.company_id = '{cid}'
                      AND ar.analysis_persona = '{user_role}'
                    ORDER BY similarity DESC
                    LIMIT 3
                """
                results = session.exec(text(query_sql)).fetchall()

                for row in results:
                    ticker = row[6]
                    chunks.append({
                        "id": row[0],
                        "document_id": None,
                        "content": row[2],
                        "page_number": 1,
                        "chunk_index": row[3],
                        "metadata": {
                            "type": "report",
                            "company_id": cid,
                            "report_id": str(row[1]),
                            "section": row[5],
                        },
                        "filename": f"Analysis Report: {row[5].replace('_', ' ').title()}",
                        "similarity": float(row[4] or 0.0),
                        "start_line": None,
                        "end_line": None,
                        "url": f"{frontend_url}/watchlist?ticker={ticker}",
                    })
            except Exception as e:
                print(f"[report_chat_agent] Error for company {cid}: {e}")

    return {"retrieved_docs": chunks}


# ---------------------------------------------------------------------------
# Market Sentiment Agent – sentiment data / alerts
# ---------------------------------------------------------------------------

def sentiment_chat_agent(state: ChatAgentState) -> Dict[str, Any]:
    """Fetch aggregated sentiment scores and recent sentiment signals."""
    company_ids = state.get("company_ids") or []
    if not company_ids:
        return {"retrieved_docs": state.get("retrieved_docs", [])}

    chunks: List[Dict[str, Any]] = list(state.get("retrieved_docs", []))

    with Session(engine) as session:
        from app.models import NewsArticle, Company

        for cid in company_ids:
            try:
                company = session.get(Company, UUID(cid))
                if not company:
                    continue

                # Get recent articles with sentiment
                articles = session.exec(
                    select(NewsArticle)
                    .where(NewsArticle.company_id == UUID(cid))
                    .where(NewsArticle.sentiment_label.is_not(None))
                    .order_by(NewsArticle.published_at.desc())
                    .limit(10)
                ).all()

                if not articles:
                    continue

                # Aggregate
                scores = [a.sentiment_score for a in articles if a.sentiment_score is not None]
                avg_score = sum(scores) / len(scores) if scores else 0
                pos = sum(1 for a in articles if a.sentiment_label == "positive")
                neg = sum(1 for a in articles if a.sentiment_label == "negative")
                neu = sum(1 for a in articles if a.sentiment_label == "neutral")

                content = (
                    f"Market Sentiment Summary for {company.name} ({company.ticker}):\n"
                    f"Average Sentiment Score: {avg_score:.2f} (scale: -1 to 1)\n"
                    f"Breakdown (last {len(articles)} articles): "
                    f"Positive={pos}, Negative={neg}, Neutral={neu}\n\n"
                    f"Recent Signals:\n"
                )
                for a in articles[:5]:
                    content += (
                        f"- [{a.published_at.strftime('%Y-%m-%d')}] "
                        f"{a.sentiment_label.upper()} ({a.sentiment_score:.2f}): "
                        f"{a.title}\n"
                    )

                chunks.append({
                    "id": uuid4(),
                    "document_id": None,
                    "content": content,
                    "page_number": 1,
                    "chunk_index": 0,
                    "metadata": {"type": "sentiment", "company": company.ticker},
                    "filename": f"Sentiment ({company.name})",
                    "similarity": 1.0,
                    "start_line": None,
                    "end_line": None,
                })
            except Exception as e:
                print(f"[sentiment_chat_agent] Error for company {cid}: {e}")

    return {"retrieved_docs": chunks}
