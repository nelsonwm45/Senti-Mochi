import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from dotenv import load_dotenv
load_dotenv("backend/.env")

from app.agents.base import get_llm
from langchain_core.messages import HumanMessage

def test_cerebras():
    print("Testing Cerebras connection...")
    try:
        model_name = "llama-3.3-70b"
        llm = get_llm(model_name)
        print(f"LLM created: {llm}")
        
        # Verify it's actually using the override
        if not hasattr(llm, "base_url") or "cerebras" not in str(llm.base_url):
             print("WARNING: base_url does not look like Cerebras. Checking type...")
             # It acts as ChatOpenAI, checking attributes
        
        response = llm.invoke([HumanMessage(content="Hello, are you running on Cerebras? Answer shortly.")])
        print(f"Response: {response.content}")
        print("SUCCESS: Cerebras connection established.")
    except Exception as e:
        print(f"FAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cerebras()
