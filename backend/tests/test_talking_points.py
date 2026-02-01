
import os
import sys
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.agents.base import get_llm
from app.agents.prompts import TALKING_POINTS_SYSTEM, get_talking_points_prompt
from langchain_core.messages import SystemMessage, HumanMessage

def test_generation():
    print("Testing LLM connection...")
    try:
        llm = get_llm("llama-3.1-8b-instant")
        print("LLM initialized.")
    except Exception as e:
        print(f"Failed to initialize LLM: {e}")
        return

    print("Testing Prompt Generation...")
    prompt = get_talking_points_prompt(
        company_name="Test Corp",
        rating="BUY",
        summary="A great company.",
        financial_analysis="Revenue up.",
        claims_analysis="Good ESG.",
        news_analysis="No bad news."
    )
    print("Prompt generated.")

    print("Invoking LLM...")
    try:
        response = llm.invoke([
            SystemMessage(content=TALKING_POINTS_SYSTEM),
            HumanMessage(content=prompt)
        ])
        print("LLM Response received:")
        print(response.content)
    except Exception as e:
        print(f"LLM Invocation Failed: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_generation()
