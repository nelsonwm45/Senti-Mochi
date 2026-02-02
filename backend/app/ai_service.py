
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os

def get_financial_advice(profile_summary: str) -> str:
    """
    Generates financial advice based on the user's profile summary.
    """
    from app.agents.base import get_llm
    from langchain_core.messages import SystemMessage, HumanMessage

    # Attempt Primary: Cerebras
    try:
        print(f"[Financial Advice] Attempting Cerebras (llama-3.3-70b)...")
        llm = get_llm("llama-3.3-70b")
        template = f"You are a professional financial advisor. Based on the client profile, provide 3 actionable financial tips.\n\nClient Profile:\n{profile_summary}\n\nFinancial Advice:"
        response = llm.invoke([HumanMessage(content=template)])
        print(f"[Financial Advice] SUCCESS (Cerebras)")
        return response.content
    except Exception as e:
        print(f"[Financial Advice] Cerebras failed: {e}. Fallback to Groq...")
        llm = get_llm("llama-3.1-8b-instant")
        template = f"You are a professional financial advisor. Based on the client profile, provide 3 actionable financial tips.\n\nClient Profile:\n{profile_summary}\n\nFinancial Advice:"
        response = llm.invoke([HumanMessage(content=template)])
        print(f"[Financial Advice] SUCCESS (Groq)")
        return response.content


