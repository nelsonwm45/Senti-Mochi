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

def _format_evidence_context(registry: Dict[str, Any]) -> str:
    """Format citation registry into a compact list for the prompt."""
    if not registry:
        return "No specific evidence citations available."
    
    lines = []
    # Sort by ID to group N1, N2.. F1, F2..
    sorted_keys = sorted(registry.keys(), key=lambda x: (x[0], int(x[1:])) if x[1:].isdigit() else (x, 0))
    
    for key in sorted_keys:
        item = registry[key]
        title = item.get("title", "Unknown Source")
        # Truncate title if too long
        if len(title) > 60:
            title = title[:57] + "..."
            
        # Add snippet if available (very short)
        snippet = ""
        if item.get("row_line"): 
            snippet = f" - {item['row_line']}"
        elif item.get("snippet"):
             snippet = f" - {item['snippet'][:50]}..."
             
        lines.append(f"[{key}] {title}{snippet}")
        
    return "\n".join(lines[:60]) # Limit to top 60 citations to be safe

def _run_lawyer_turn(role: str, state: AgentState) -> Dict[str, Any]:
    company_name = state["company_name"]
    persona = state.get("analysis_persona", "RELATIONSHIP_MANAGER")
    
    # Format persona to human-readable text
    persona_readable = {
        'INVESTOR': 'investor',
        'EQUITY_ANALYST': 'equity analyst',
        'RELATIONSHIP_MANAGER': 'relationship manager',
        'CREDIT_RISK': 'credit risk officer'
    }.get(persona, 'investor')
    
    briefs = state.get("legal_briefs", {})
    transcript = state.get("debate_transcript", []) or []
    
    # Identify briefs
    my_role_key = "government" if role == "Government" else "opposition"
    opp_role_key = "opposition" if role == "Government" else "government"
    
    my_brief_list = briefs.get(my_role_key, [])
    opp_brief_list = briefs.get(opp_role_key, [])
    
    my_brief_text = "\n".join([f"- {p}" for p in my_brief_list])
    opp_brief_text = "\n".join([f"- {p}" for p in opp_brief_list])
    
    transcript_text = "\n".join(transcript[-2:]) # Context window: last 2 turns (reduced for token efficiency)
    
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
        persona=persona_readable
    )
    
    prompt = get_lawyer_prompt(
        role=role,
        company_name=company_name,
        my_brief=my_brief_text,
        opponent_brief=opp_brief_text,
        transcript=transcript_text,
        previous_turn=previous_turn,
        persona=persona_readable
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
