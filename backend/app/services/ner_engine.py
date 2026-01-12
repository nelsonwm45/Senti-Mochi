from typing import List, Dict
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.models import Company # For future linking

class NEREngine:
    """
    Extracts named entities relevant to financial context:
    - PERSON (Directors, CEOs)
    - ORG (Companies, Parties involved)
    - EVENT (M&A, Litigation, Resignation)
    """
    
    def __init__(self):
        groq_api_key = os.getenv("GROQ_API_KEY")
        self.llm = ChatOpenAI(
            temperature=0.0,
            model_name="llama-3.3-70b-versatile",
            openai_api_key=groq_api_key,
            openai_api_base="https://api.groq.com/openai/v1"
        )
        
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        template = """
        Extract the following entities from the financial text below.
        
        Categories:
        - "DIRECTORS": Person names (Key Personnel)
        - "COMPANIES": Organization names
        - "EVENTS": Key events (e.g. "Resignation", "Acquisition", "Quarterly Results")
        
        Text:
        {text}
        
        Output JSON:
        {{
            "DIRECTORS": ["name1", ...],
            "COMPANIES": ["org1", ...],
            "EVENTS": ["event1", ...]
        }}
        """
        prompt = PromptTemplate(input_variables=["text"], template=template)
        chain = prompt | self.llm | JsonOutputParser()
        
        try:
            return chain.invoke({"text": text[:4000]})
        except Exception as e:
            return {"error": str(e)}
