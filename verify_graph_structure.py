import sys
import os
# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.agents.workflow import app_workflow

def verify_graph():
    graph = app_workflow.get_graph()
    print("=== NODES ===")
    for node in graph.nodes:
        print(f"- {node}")
        
    print("\n=== EDGES ===")
    for edge in graph.edges:
        # Edge might be tuple or object
        if hasattr(edge, 'source'):
             if hasattr(edge, 'conditional') and edge.conditional:
                 print(f"- {edge.source} -> {edge.target} (CONDITIONAL)")
             else:
                 print(f"- {edge.source} -> {edge.target}")
        else:
             print(f"- {edge}")

if __name__ == "__main__":
    verify_graph()
