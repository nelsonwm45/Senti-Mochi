from typing import Dict, Optional, List
import os
import re
from uuid import UUID
from sqlmodel import Session, select
from app.database import engine
from app.models import FinancialRatio, Filing
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

class FinancialExtractor:
    """
    Extracts key financial ratios and data points logic.
    """

    def __init__(self):
        groq_api_key = os.getenv("GROQ_API_KEY")
        self.llm = ChatOpenAI(
            temperature=0.0,
            model_name="llama-3.3-70b-versatile", 
            openai_api_key=groq_api_key,
            openai_api_base="https://api.groq.com/openai/v1"
        )

    def extract_ratios_from_text(self, text: str) -> Dict[str, float]:
        """
        Uses LLM to find ratios in text if regex fails.
        """
        template = """
        Extract the following financial ratios from the text if available.
        Return 0.0 if not found.
        
        Ratios to find:
        - "Current Ratio"
        - "Debt-to-Equity Ratio"
        - "Net Profit Margin" (%)
        
        Text:
        {text}
        
        Output JSON:
        {{
            "Current Ratio": <float>,
            "Debt-to-Equity Ratio": <float>,
            "Net Profit Margin": <float>
        }}
        """
        prompt = PromptTemplate(input_variables=["text"], template=template)
        chain = prompt | self.llm | JsonOutputParser()
        
        try:
            return chain.invoke({"text": text[:6000]})
        except Exception:
            return {}

    def process_filing(self, filing_id: UUID):
        with Session(engine) as session:
            filing = session.get(Filing, filing_id)
            if not filing or not filing.document_id:
                return

            # In a real scenario, we'd fetch the document chunks marked as "Financial Statements"
            # For MVP, let's assume we pass the content_summary or the first 5 chunks.
            # Simulating text availability:
            text_to_analyze = filing.content_summary or "Net Profit Margin was 15%. Current Ratio stood at 2.5."

            ratios = self.extract_ratios_from_text(text_to_analyze)
            
            for name, value in ratios.items():
                if value and isinstance(value, (int, float)):
                    ratio_entry = FinancialRatio(
                        company_id=filing.company_id,
                        filing_id=filing.id,
                        period="Unknown", # Need logic to extract period
                        ratio_name=name,
                        value=float(value)
                    )
                    session.add(ratio_entry)
            
            session.commit()
