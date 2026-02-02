
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from app.agents.base import get_llm
from langchain_core.messages import HumanMessage

def test_fallback_concept():
    print("Testing Manual Fallback Concept...")
    
    # 1. Try Primary (Cerebras)
    try:
        print("\n[1] Attempting Cerebras (llama-3.3-70b)...")
        llm = get_llm("llama-3.3-70b")
        # Simple invoke
        response = llm.invoke([HumanMessage(content="Say 'Primary Success' if you can read this.")])
        print(f"Cerebras Response: {response.content}")
    except Exception as e:
        print(f"Cerebras Failed: {e}")
        
        # 2. Fallback (Groq)
        print("\n[2] Attempting Fallback to Groq (llama-3.1-8b-instant)...")
        try:
            llm_fallback = get_llm("llama-3.1-8b-instant")
            response = llm_fallback.invoke([HumanMessage(content="Say 'Fallback Success' if you can read this.")])
            print(f"Groq Response: {response.content}")
        except Exception as e2:
            print(f"Groq Failed too: {e2}")

if __name__ == "__main__":
    test_fallback_concept()
