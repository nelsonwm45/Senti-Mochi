from app.services.ner_engine import NEREngine
from app.services.financial_extractor import FinancialExtractor
from app.ai_service import analyze_financial_sentiment

def verify_phase3():
    print("--- Verifying Sentiment Analysis ---")
    text = "Company XYZ reported a massive loss due to unexpected litigation."
    sentiment = analyze_financial_sentiment(text)
    print(f"Text: {text}")
    print(f"Sentiment: {sentiment}")

    print("\n--- Verifying NER Engine ---")
    ner_text = "Datuk Seri John Doe resigned from Maybank yesterday."
    ner = NEREngine()
    entities = ner.extract_entities(ner_text)
    print(f"Text: {ner_text}")
    print(f"Entities: {entities}")

    print("\n--- Verifying Financial Extractor ---")
    fin_text = "The company's Net Profit Margin increased to 12.5% while Current Ratio remains steady at 1.8."
    fe = FinancialExtractor()
    ratios = fe.extract_ratios_from_text(fin_text)
    print(f"Text: {fin_text}")
    print(f"Ratios: {ratios}")

if __name__ == "__main__":
    verify_phase3()
