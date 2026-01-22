
from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.news_agent import news_agent
from app.agents.financial_agent import financial_agent
from app.agents.claims_agent import claims_agent
from app.agents.judge import judge_agent
import concurrent.futures

def gather_intelligence(state: AgentState):
    """
    Runs worker agents in parallel.
    """
    print("Orchestrator: Starting parallel intelligence gathering...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_news = executor.submit(news_agent, state)
        future_fin = executor.submit(financial_agent, state)
        future_claims = executor.submit(claims_agent, state)
        
        results = {
            "news": future_news.result(),
            "financial": future_fin.result(),
            "claims": future_claims.result()
        }
    
    # Merge results into state update
    update = {}
    update.update(results["news"])
    update.update(results["financial"])
    update.update(results["claims"])
    
    return update

def build_graph():
    """
    Constructs the Multi-Agent workflow graph.
    """
    builder = StateGraph(AgentState)
    
    builder.add_node("gather_intelligence", gather_intelligence)
    builder.add_node("judge", judge_agent)
    
    builder.set_entry_point("gather_intelligence")
    
    builder.add_edge("gather_intelligence", "judge")
    builder.add_edge("judge", END)
    
    return builder.compile()

# Global compiled graph
app_workflow = build_graph()
