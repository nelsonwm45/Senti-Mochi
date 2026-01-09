from typing import List, Dict

class MockIngestionService:
    def __init__(self):
        self.chunk_size = 10  # Small chunk size for testing
        self.chunk_overlap = 2

    def chunk_text(self, pages: List[Dict]) -> List[Dict]:
        """
        Split text into chunks with overlap, tracking line numbers
        """
        chunks = []
        chunk_index = 0
        
        for page in pages:
            content = page["content"]
            page_number = page["page_number"]
            
            # Map words to lines to verify where chunks come from
            # Structure: [(word, line_number), ...]
            words_with_lines = []
            
            # Split by lines first
            lines = content.split('\n')
            for line_idx, line in enumerate(lines):
                line_words = line.split()
                for word in line_words:
                    # Store word and its 1-based line number
                    words_with_lines.append((word, line_idx + 1))
            
            if not words_with_lines:
                continue

            chunk_size_words = self.chunk_size
            overlap_words = self.chunk_overlap
            
            # Sliding window
            for i in range(0, len(words_with_lines), chunk_size_words - overlap_words):
                # Get the slice of words+lines for this chunk
                chunk_data = words_with_lines[i:i + chunk_size_words]
                
                # Reconstruct text
                chunk_words = [item[0] for item in chunk_data]
                chunk_text = " ".join(chunk_words)
                
                if chunk_text.strip():
                    # Get line range
                    start_line = chunk_data[0][1]
                    end_line = chunk_data[-1][1]
                    
                    chunks.append({
                        "content": chunk_text,
                        "page_number": page_number,
                        "chunk_index": chunk_index,
                        "token_count": len(chunk_words),
                        "start_line": start_line,
                        "end_line": end_line
                    })
                    chunk_index += 1
        
        return chunks

# Test Data
sample_text = """Line 1: This is the first line.
Line 2: This is the second line with more text.
Line 3: Third line here.
Line 4: Fourth line.
Line 5: Fifth line is a bit longer to ensure we span multiple chunks.
Line 6: Sixth line."""

pages = [{"page_number": 1, "content": sample_text}]

service = MockIngestionService()
chunks = service.chunk_text(pages)

print(f"Input Text:\n{sample_text}\n")
print("-" * 50)
for chunk in chunks:
    print(f"Chunk {chunk['chunk_index']}: Lines {chunk['start_line']}-{chunk['end_line']}")
    print(f"Content: {chunk['content']}")
    print("-" * 20)
