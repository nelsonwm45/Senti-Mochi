import re

class PIIDetector:
    def __init__(self):
        # Simple regex patterns for demonstration
        self.patterns = {
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "ssn": r"\d{3}-\d{2}-\d{4}",
            "phone": r"\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}",
        }

    def detect(self, text: str) -> dict:
        results = {}
        for key, pattern in self.patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                results[key] = matches
        return results

    def redact(self, text: str) -> str:
        for key, pattern in self.patterns.items():
            text = re.sub(pattern, f"[{key.upper()}_REDACTED]", text)
        return text
