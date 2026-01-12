## Relevant Files

- `backend/app/ai_service.py` - Core interaction with LLMs.
- `backend/app/services/sentiment_engine.py` (New) - Logic for classification.
- `backend/app/services/ner_engine.py` (New) - Named Entity Recognition.
- `backend/app/services/financial_extractor.py` (New) - Regex/LLM logic for table parsing.

### Notes

- Sentiment analysis should produce structured outputs (Score + Rationale).
- Financial extraction is critical; consider using specialized libraries like `tabula-py` for tables before sending to LLM.

## Tasks

- [x] 0.0 Create feature branch
  - [x] 0.1 Create branch `feature/phase3-analytics`
- [x] 1.0 Sentiment Analysis Engine
  - [x] 1.1 Design prompt for "Financial Sentiment" (Positive/Adverse/Neutral) with rationale.
  - [x] 1.2 Implement `analyze_sentiment(text)` function using `ai_service`.
  - [x] 1.3 Store results in `SentimentAnalysis` table.
- [x] 2.0 Topic & Entity Extraction (NER)
  - [x] 2.1 Develop standard categories (M&A, Director Dealing, Litigation).
  - [x] 2.2 Implement NER to extract Director names and Parties interactions.
- [x] 3.0 Financial Extraction Module
  - [x] 3.1 Build parser to identifying "Balance Sheet" and "Income Statement" pages in PDFs.
  - [x] 3.2 Implement algorithms to extract Top 10 Ratios (Current Ratio, D/E, NPM).
  - [x] 3.3 Add validation flags (e.g., "Confidence Low" if numbers don't balance).
