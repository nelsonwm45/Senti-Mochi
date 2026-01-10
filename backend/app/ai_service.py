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
        model_name="llama3-70b-8192", # Using Groq's supported model
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
