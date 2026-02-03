from typing import Dict, Any, List
from app.agents.state import AgentState
from app.agents.base import get_llm
from app.agents.prompts import LAWYER_SYSTEM, get_lawyer_prompt
from langchain_core.messages import SystemMessage, HumanMessage

def government_agent(state: AgentState) -> Dict[str, Any]:
    """
    Government Lawyer: Defends the company using Pro-Company briefs.
    """
    print("Debate: Government is speaking...")
    return _run_lawyer_turn("Government", state)

def opposition_agent(state: AgentState) -> Dict[str, Any]:
    """
    Opposition Lawyer: Critiques the company using Anti-Company briefs.
    """
    print("Debate: Opposition is speaking...")
    return _run_lawyer_turn("Opposition", state)

def _run_lawyer_turn(role: str, state: AgentState) -> Dict[str, Any]:
    company_name = state["company_name"]
    persona = state.get("analysis_persona", "RELATIONSHIP_MANAGER")
    briefs = state.get("legal_briefs", {})
    transcript = state.get("debate_transcript", []) or []
    
    # Identify briefs
    my_role_key = "government" if role == "Government" else "opposition"
    opp_role_key = "opposition" if role == "Government" else "government"
    
    my_brief_list = briefs.get(my_role_key, [])
    opp_brief_list = briefs.get(opp_role_key, [])
    
    my_brief_text = "\n".join([f"- {p}" for p in my_brief_list])
    opp_brief_text = "\n".join([f"- {p}" for p in opp_brief_list])
    
    transcript_text = "\n".join(transcript[-4:]) # Context window: last 4 turns
    
    # Determine previous turn text
    if transcript:
        last_turn = transcript[-1]
        # format: "Role: Message"
        if ": " in last_turn:
            previous_turn = last_turn.split(": ", 1)[1]
        else:
            previous_turn = last_turn
    else:
        previous_turn = "Opening Statement"

    system_msg = LAWYER_SYSTEM.format(
        role=role.upper(),
        company_name=company_name,
        persona=persona
    )
    
    prompt = get_lawyer_prompt(
        role=role,
        my_brief=my_brief_text,
        opponent_brief=opp_brief_text,
        transcript=transcript_text,
        previous_turn=previous_turn
    )

    try:
        # Use Cerebras for debate (faster inference is good for loops)
        llm = get_llm("llama-3.3-70b")
        response = llm.invoke([
            SystemMessage(content=system_msg),
            HumanMessage(content=prompt)
        ])
        argument = response.content.strip()
        
    except Exception as e:
        print(f"Lawyer Agent ({role}) failed: {e}. Fallback to Groq...")
        llm = get_llm("llama-3.1-8b-instant")
        response = llm.invoke([
            SystemMessage(content=system_msg),
            HumanMessage(content=prompt)
        ])
        argument = response.content.strip()

    # Append to transcript
    new_entry = f"{role}: {argument}"
    
    # Need to verify if 'debate_transcript' in dict accumulation overrides or appends.
    # In LangGraph, if we return {key: value}, it usually overwrites unless Reducer is used.
    # State definition validation needed.
    # state.py uses TypedDict. Simple overwrite.
    # So I must return the FULL transcript + new entry.
    
    updated_transcript = transcript + [new_entry]
    
    # Add to specific arguments list for UI
    # state.py has government_arguments: List[str]
    # We should update those too.
    
    updates = {
        "debate_transcript": updated_transcript
    }
    
    if role == "Government":
        existing_gov = state.get("government_arguments", []) or []
        updates["government_arguments"] = existing_gov + [argument]
    else:
        existing_opp = state.get("opposition_arguments", []) or []
        updates["opposition_arguments"] = existing_opp + [argument]
        
    return updates
