from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os

def get_financial_advice(profile_summary: str) -> str:
    """
    Generates financial advice based on the user's profile summary.
    """
    # Initialize LLM lazily to prevent multiprocessing issues
    # Using Groq via ChatOpenAI compatibility layer
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        return "Error: GROQ_API_KEY is not set."

    llm = ChatOpenAI(
        temperature=0.7, 
        model_name="llama-3.3-70b-versatile", # Using Groq's supported model
        openai_api_key=groq_api_key,
        openai_api_base="https://api.groq.com/openai/v1"
    )

    template = """
    You are a professional financial advisor. Based on the following client profile, provide 3 actionable financial tips.
    
    Client Profile:
    {profile_summary}
    
    Financial Advice:
    """
    
    prompt = PromptTemplate(
        input_variables=["profile_summary"],
        template=template,
    )
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        response = chain.invoke({"profile_summary": profile_summary})
        return response
    except Exception as e:
        return f"Error generating advice: {str(e)}"

def analyze_financial_sentiment(text: str) -> dict:
    """
    Analyzes financial sentiment of text.
    Returns dict: { "score": "Positive"|"Neutral"|"Adverse", "confidence": float, "rationale": str }
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        return {"score": "Neutral", "confidence": 0.0, "rationale": "API Key missing"}

    llm = ChatOpenAI(
        temperature=0.1, # Low temp for classification
        model_name="llama-3.3-70b-versatile", 
        openai_api_key=groq_api_key,
        openai_api_base="https://api.groq.com/openai/v1"
    )

    template = """
    You are a financial sentiment analyzer. Analyze the following text and classify its sentiment regarding the subject company or market.
    
    Text:
    {text}
    
    Output JSON only:
    {{
        "score": "Positive" or "Neutral" or "Adverse",
        "confidence": <float between 0.0 and 1.0>,
        "rationale": "<brief explanation>"
    }}
    """
    
    prompt = PromptTemplate(
        input_variables=["text"],
        template=template,
    )
    
    # Use JsonOutputParser if available, or just Str and json.loads
    from langchain_core.output_parsers import JsonOutputParser
    chain = prompt | llm | JsonOutputParser()
    
    try:
        # Truncate text if too long to avoid token limits
        safe_text = text[:4000]
        response = chain.invoke({"text": safe_text})
        return response
    except Exception as e:
        return {"score": "Neutral", "confidence": 0.0, "rationale": f"Error: {str(e)}"}
