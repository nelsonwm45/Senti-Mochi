
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
            
    elif "llama" in model_name or "groq" in model_name:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
            
        # If the model name is generic "groq", default to llama-3.3-70b-versatile
        if model_name == "groq":
            model_name = "llama-3.3-70b-versatile"
            
        return ChatGroq(
            model_name=model_name,
            api_key=api_key,
            temperature=0,
        )
    
    else:
        raise ValueError(f"Unsupported model: {model_name}")
