from typing import Dict, Any, List
from app.agents.state import AgentState
from app.agents.base import get_llm
from app.agents.prompts import BRIEFING_CLERK_SYSTEM, get_briefing_prompt
from langchain_core.messages import SystemMessage, HumanMessage
import json
import re

def parse_brief_json(response_text: str) -> Dict[str, Any]:
    """
    Parses the JSON output from the Briefing Clerk.
    Expected format: {"government": [...], "opposition": [...]}
    """
    try:
        # 1. Try to find JSON block wrapped in ```json ... ```
        match = re.search(r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if match:
             return json.loads(match.group(1))
        
        # 2. Try generic code block ``` ... ```
        match = re.search(r"```\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if match:
             return json.loads(match.group(1))
             
        # 3. Try finding first { and last }
        start = response_text.find('{')
        end = response_text.rfind('}')
        if start != -1 and end != -1:
            json_str = response_text[start:end+1]
            return json.loads(json_str)
            
        return {}
    except Exception as e:
        print(f"Briefing Node: JSON extraction failed: {e}")
        return {}

def briefing_node(state: AgentState) -> Dict[str, Any]:
    """
    Briefing Node: Consolidates raw evidence from all agents into Legal Briefs.
    Separates findings into Government (Pro) and Opposition (Con) arguments.
    """
    print("Briefing Node: Consolidating evidence into Legal Briefs...")
    
    raw_evidence = state.get("raw_evidence", {})
    
    # Flatten evidence into text validation format
    evidence_text_parts = []
    
    # Helper to extract text from Pydantic models or Dicts
    def format_ev(source_type, items):
        if not items:
            return
            
        for item in items:
            # Handle Pydantic model or Dict
            if hasattr(item, 'model_dump'):
                data = item.model_dump()
            elif isinstance(item, dict):
                data = item
            else:
                data = {"content": str(item)}
                
            content = data.get('content', '')
            citation = data.get('citation', '')
            sentiment = data.get('sentiment', 'NEUTRAL')
            confidence = data.get('confidence', '')
            
            evidence_text_parts.append(
                f"[{source_type.upper()}] {content}\n   - Sentiment: {sentiment}, Confidence: {confidence}%, Citation: {citation}"
            )

    if 'news' in raw_evidence:
        format_ev('News', raw_evidence.get('news', []))
    if 'financial' in raw_evidence:
        format_ev('Financial', raw_evidence.get('financial', []))
    if 'claims' in raw_evidence:
        format_ev('Claims', raw_evidence.get('claims', []))
        
    full_evidence_text = "\n".join(evidence_text_parts)
    
    # Default empty briefs
    legal_briefs = {
        "government": [],
        "opposition": []
    }
    
    if not full_evidence_text:
        print("Briefing Node: No evidence found to process.")
        return {"legal_briefs": legal_briefs}

    # Call LLM to synthesize
    try:
        # Attempt Primary: Cerebras
        print("[Briefing Node] Attempting Cerebras (llama-3.3-70b)...")
        llm = get_llm("llama-3.3-70b")
        response = llm.invoke([
            SystemMessage(content=BRIEFING_CLERK_SYSTEM),
            HumanMessage(content=get_briefing_prompt(full_evidence_text))
        ])
        print("[Briefing Node] SUCCESS (Cerebras)")
        content = response.content
        
    except Exception as e:
        print(f"[Briefing Node] Cerebras failed: {e}. Fallback to Groq...")
        try:
            # Fallback: Groq (Truncate input to safe limit ~6k chars)
            truncated_text = full_evidence_text[:6000] + "... [TRUNCATED]"
            llm = get_llm("llama-3.1-8b-instant")
            response = llm.invoke([
                SystemMessage(content=BRIEFING_CLERK_SYSTEM),
                HumanMessage(content=get_briefing_prompt(truncated_text))
            ])
            print("[Briefing Node] SUCCESS (Groq)")
            content = response.content
        except Exception as e2:
            print(f"[Briefing Node] All LLMs failed: {e2}")
            return {"legal_briefs": legal_briefs}

    # Parse JSON
    parsed_data = parse_brief_json(content)
    
    if parsed_data:
        legal_briefs["government"] = parsed_data.get("government", [])
        legal_briefs["opposition"] = parsed_data.get("opposition", [])
        print(f"Briefing Node: Generated {len(legal_briefs['government'])} Govt points, {len(legal_briefs['opposition'])} Opp points.")
    else:
        print("Briefing Node: Failed to parse valid JSON from LLM response.")

    return {"legal_briefs": legal_briefs}
