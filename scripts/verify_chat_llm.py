import os
import asyncio
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.rag import RAGService

async def test_chat_llm():
    print("Testing RAGService Chat Upgrade...")
    rag = RAGService()
    
    query = "What are the latest sustainability trends for Maybank?"
    context = "[Source 1: Annual Report] Maybank is focusing on green financing. [Source 2: News] Maybank announced new ESG goals."
    
    print("\n[1] Testing generate_response (Non-streaming)...")
    try:
        result = rag.generate_response(query, context)
        print(f"Model used: {result.get('model')}")
        print(f"Response: {result['response'][:100]}...")
    except Exception as e:
        print(f"generate_response failed: {e}")

    print("\n[2] Testing generate_response_stream (Streaming)...")
    try:
        full_text = ""
        async for chunk in rag.generate_response_stream(query, context):
            full_text += chunk
            if len(full_text) < 50:
                print(chunk, end="", flush=True)
        print("\n[Stream Complete]")
        print(f"Total Stream Length: {len(full_text)}")
    except Exception as e:
        print(f"generate_response_stream failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat_llm())
