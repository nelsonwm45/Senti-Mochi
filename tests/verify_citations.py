import sys
import os
# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.rag import RAGService

def test_renumbering():
    rag = RAGService()
    
    # Mock Chunks (0-indexed in list, but 1-indexed in Source ID)
    chunks = [
        {"content": "Content A", "id": "A"}, # Source 1
        {"content": "Content B", "id": "B"}, # Source 2
        {"content": "Content C", "id": "C"}, # Source 3
        {"content": "Content D", "id": "D"}, # Source 4
        {"content": "Content E", "id": "E"}, # Source 5
    ]
    
    # Scenario: LLM used Source 3 and Source 5
    text = "According to [Source 3], the sky is blue. Also, [Source 5] says grass is green."
    
    print(f"Original Text: {text}")
    print(f"Original Chunks: {[c['id'] for c in chunks]}")
    
    new_text, new_chunks = rag.reindex_citations(text, chunks)
    
    print(f"\nNew Text: {new_text}")
    print(f"New Chunks: {[c['id'] for c in new_chunks]}")
    
    # Assertions
    expected_text = "According to [Source 1], the sky is blue. Also, [Source 2] says grass is green."
    if new_text != expected_text:
        print("FAIL: Text was not renumbered correctly.")
        return
        
    # Expected Chunks order: Source 3 (C) -> New Source 1, Source 5 (E) -> New Source 2, then rest
    if new_chunks[0]['id'] != 'C' or new_chunks[1]['id'] != 'E':
        print("FAIL: Chunks were not reordered correctly.")
        print(f"Expected start: ['C', 'E'], Got: {[c['id'] for c in new_chunks[:2]]}")
        return
        
    print("\nSUCCESS: Renumbering works!")

if __name__ == "__main__":
    test_renumbering()
