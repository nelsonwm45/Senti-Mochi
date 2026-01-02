from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Initialize LLM
llm = ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo")

def get_financial_advice(profile_summary: str) -> str:
    """
    Generates financial advice based on the user's profile summary.
    """
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
