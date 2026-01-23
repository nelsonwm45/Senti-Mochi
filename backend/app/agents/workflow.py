
from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.news_agent import news_agent
from app.agents.financial_agent import financial_agent
from app.agents.claims_agent import claims_agent
from app.agents.judge import judge_agent
import concurrent.futures

def gather_intelligence(state: AgentState):
    """
    Runs worker agents sequentially to avoid Rate Limits.
    """
    print("Orchestrator: Starting sequential intelligence gathering...")
    
    # Run sequentially
    news_result = news_agent(state)
    fin_result = financial_agent(state)
    claims_result = claims_agent(state)

    update = {}
    update.update(news_result)
    update.update(fin_result)
    update.update(claims_result)
    
    return update

def cross_examination(state: AgentState):
    """
    Second Phase: Agents critique each other.
    Runs sequentially.
    """
    print("Orchestrator: Starting debate/critique phase...")
    from app.agents.news_agent import news_critique
    from app.agents.financial_agent import financial_critique
    from app.agents.claims_agent import claims_critique

    news_critique_result = news_critique(state)
    fin_critique_result = financial_critique(state)
    claims_critique_result = claims_critique(state)
    
    update = {}
    update.update(news_critique_result)
    update.update(fin_critique_result)
    update.update(claims_critique_result)
    
    return update

def build_graph():
    """
    Constructs the Multi-Agent workflow graph.
    """
    builder = StateGraph(AgentState)
    
    builder.add_node("gather_intelligence", gather_intelligence)
    builder.add_node("cross_examination", cross_examination)
    builder.add_node("judge", judge_agent)
    
    builder.set_entry_point("gather_intelligence")
    
    builder.add_edge("gather_intelligence", "cross_examination")
    builder.add_edge("cross_examination", "judge")
    builder.add_edge("judge", END)
    
    return builder.compile()

# Global compiled graph
app_workflow = build_graph()
