
import os
import sys
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock the database engine before importing agents to avoid init errors if any
with patch('app.database.engine'):
    from app.agents.state import AgentState
    from app.agents.workflow import app_workflow

def run_verification():
    print("Starting Debate Architecture Verification (Orchestration Check)...")


    # Patch the functions that workflow.py has ALREADY imported
    # We must patch them in the `app.agents.workflow` namespace for the first phase
    with patch('app.agents.workflow.news_agent') as mock_news, \
         patch('app.agents.workflow.financial_agent') as mock_fin, \
         patch('app.agents.workflow.claims_agent') as mock_claims, \
         patch('app.agents.news_agent.news_critique') as mock_news_crit, \
         patch('app.agents.financial_agent.financial_critique') as mock_fin_crit, \
         patch('app.agents.claims_agent.claims_critique') as mock_claims_crit, \
         patch('app.agents.judge.judge_agent') as mock_judge:

        # Setup Return Values
        mock_news.return_value = {"news_analysis": "News: Growth is high."}
        mock_fin.return_value = {"financial_analysis": "Fin: Revenue is low."}
        mock_claims.return_value = {"claims_analysis": "Claims: We are growing."}

        mock_news_crit.return_value = {"news_critique": "Critique: News disagrees with Fin."}
        mock_fin_crit.return_value = {"financial_critique": "Critique: Fin disagrees with News."}
        mock_claims_crit.return_value = {"claims_critique": "Critique: Claims agrees with News."}

        mock_judge.return_value = {"final_report": "Judge: Decision made.", "final_rating": "BUY"}

        # Prepare State
        initial_state = AgentState(
            company_id="test-uuid",
            company_name="TestCorp",
            news_data="",
            financial_data="",
            claims_data="",
            errors=[]
        )

        # Run Workflow
        print("Invoking Agent Workflow...")
        try:
            final_state = app_workflow.invoke(initial_state)
            print("Workflow finished successfully.")
        except Exception as e:
            print(f"Workflow failed: {e}")
            return

        # Verification Checks
        print("\n--- Verification Results ---")
        
        # Check Execution Counts
        print(f"1. News Agent called: {mock_news.called}")
        print(f"2. Financial Agent called: {mock_fin.called}")
        print(f"3. Claims Agent called: {mock_claims.called}")
        
        print(f"4. News Critique called: {mock_news_crit.called}")
        print(f"5. Financial Critique called: {mock_fin_crit.called}")
        print(f"6. Claims Critique called: {mock_claims_crit.called}")
        
        print(f"7. Judge Agent called: {mock_judge.called}")

        # Check State Flow
        # Since we mocked the returns, the final state should contain them IF the workflow passes them through
        # But wait, workflow.py merges results.
        # However, our mocks return dicts, and gather_intelligence merges them.
        # But judge_agent is the last node, and it returns a dict.
        # LangGraph updates the state with the return value of nodes.
        
        if mock_news_crit.called and mock_fin_crit.called and mock_judge.called:
            print("\n✅ SUCCESS: Debate workflow graph executed correct nodes.")
        else:
            print("\n❌ FAILURE: Debate phase nodes were not hit expectedly.")

if __name__ == "__main__":
    run_verification()
