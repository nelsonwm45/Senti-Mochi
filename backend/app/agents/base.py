
import os
from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm(model_name: str = "llama-3.3-70b-versatile") -> BaseChatModel:
    """
    Factory to return the appropriate LLM based on model name.
    """
    
    if "gemini" in model_name:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0,
            max_output_tokens=8192,
        )
            
    # Cerebras Support via OpenAI SDK
    # Checks for direct model names or "cerebras" keyword if we add one
    if model_name in ["gpt-oss-120b", "llama-3.3-70b", "llama3.1-8b", "qwen-2.5-72b-instruct", "qwen-2.5-32b-instruct", "zai-glm-4.7"] or "cerebras" in model_name:
        from langchain_openai import ChatOpenAI
        
        api_key = os.getenv("CEREBRAS_API_KEY")
        if not api_key:
            raise ValueError("CEREBRAS_API_KEY not found in environment variables")
            
        print(f"DEBUG: Using Cerebras provider for model {model_name}")
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url="https://api.cerebras.ai/v1",
            temperature=0,
            max_retries=3,
        )

    elif "llama" in model_name or "groq" in model_name:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
            
        # If the model name is generic "groq", default to llama-3.3-70b-versatile
        if model_name == "groq":
            model_name = "llama-3.3-70b-versatile"
            
        llm = ChatGroq(
            model_name=model_name,
            api_key=api_key,
            temperature=0,
            max_retries=5, # Built-in retry for connection/server errors
            max_tokens=8192,
        )
        # Add a custom wrapper or just rely on LangChain's retry if sufficient, 
        # but here we can rely on ChatGroq's internal retry or just configure it.
        # However, for 429 specifically, increasing max_retries is key.
        print(f"DEBUG: Using Groq provider for model {model_name}")
        return llm


    else:
        raise ValueError(f"Unsupported model: {model_name}")


def extract_json_from_response(response_text: str) -> list:
    """
    Extracts and parses a JSON block from the LLM response text.
    Expected format: ```json [...] ``` or just [...] at the end.
    Returns empty list if parsing fails.
    """
    import re
    import json
    
    # Try to find JSON block
    json_match = re.search(r"```json\s*(\[.*?\])\s*```", response_text, re.DOTALL)
    if not json_match:
        # Try generic code block
        json_match = re.search(r"```\s*(\[.*?\])\s*```", response_text, re.DOTALL)
        
    if json_match:
        json_str = json_match.group(1)
    else:
        # optimize: try to find the last occurrence of '[' and ']'
        try:
            start = response_text.rindex('[')
            end = response_text.rindex(']') + 1
            json_str = response_text[start:end]
        except ValueError:
            return []

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON evidence from response.")
        return []
