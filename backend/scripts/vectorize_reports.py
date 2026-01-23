
from sqlmodel import Session, select
from app.database import engine
from app.models import AnalysisReport, ReportChunk
from app.services.rag import RAGService
from uuid import uuid4

def vectorize_existing_reports():
    print("Starting vectorization of existing reports...")
    rag_service = RAGService()
    
    with Session(engine) as session:
        # Get all reports
        reports = session.exec(select(AnalysisReport)).all()
        print(f"Found {len(reports)} reports.")
        
        for report in reports:
            # Check if already vectorized
            existing_chunks = session.exec(select(ReportChunk).where(ReportChunk.report_id == report.id)).all()
            if existing_chunks:
                print(f"Report {report.id} already has {len(existing_chunks)} chunks. Skipping.")
                continue
                
            print(f"Processing Report {report.id} for Company {report.company_id}...")
            
            # Define sections to embed
            sections = [
                ("summary", f"**Investment Thesis**:\n{report.summary}"),
                ("bull_case", f"**Bull Case**:\n{report.bull_case}"),
                ("bear_case", f"**Bear Case**:\n{report.bear_case}"),
                ("risk_factors", f"**Risk Factors**:\n{report.risk_factors}")
            ]
            
            chunks_to_add = []
            for idx, (section_type, content) in enumerate(sections):
                if not content or len(content) < 10: continue

                # Get Company Name for context (optimized query)
                # We can just lazily access report.company.name if relationship is loaded, 
                # but safer to query if lazy loading specific
                company_name = report.company.name if report.company else "Unknown Company"
                
                context_content = f"[{company_name} Analysis Report - {section_type.replace('_', ' ').title()}]\n{content}"
                
                try:
                    embedding = rag_service.embed_query(context_content)
                    if embedding:
                        chunk = ReportChunk(
                            id=uuid4(),
                            report_id=report.id,
                            content=context_content,
                            chunk_index=idx,
                            section_type=section_type,
                            embedding=embedding
                        )
                        chunks_to_add.append(chunk)
                        print(f"  - Vectorized {section_type}")
                except Exception as e:
                    print(f"  - Error embedding {section_type}: {e}")

            if chunks_to_add:
                session.add_all(chunks_to_add)
                session.commit()
                print(f"Saved {len(chunks_to_add)} chunks for Report {report.id}")
                
    print("Vectorization complete.")

if __name__ == "__main__":
    vectorize_existing_reports()
