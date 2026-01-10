
import sys
import os
import unittest
from datetime import datetime

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.pii_detection import PIIDetector
from app.core.encryption import encrypt_data, decrypt_data
from app.plugins.financial_statement_parser import FinancialStatementParser
from app.models import Document, Workflow

class TestPhase3Features(unittest.TestCase):
    
    def test_pii_detection(self):
        print("\nTesting PII Detection...")
        detector = PIIDetector()
        text = "Contact me at alice@example.com or 555-0199."
        detected = detector.detect(text)
        self.assertIn("email", detected)
        self.assertIn("alice@example.com", detected["email"])
        
        redacted = detector.redact(text)
        self.assertNotIn("alice@example.com", redacted)
        self.assertIn("[EMAIL_REDACTED]", redacted)
        print("PII Detection Passed.")

    def test_encryption(self):
        print("\nTesting Encryption...")
        original = "SecretData123"
        encrypted = encrypt_data(original)
        self.assertNotEqual(original, encrypted)
        
        decrypted = decrypt_data(encrypted)
        self.assertEqual(original, decrypted)
        print("Encryption Passed.")

    def test_plugin_system(self):
        print("\nTesting Plugin System...")
        plugin = FinancialStatementParser()
        # Mock document
        doc = Document(
            filename="balance_sheet.pdf", 
            content_type="application/pdf", 
            file_size=1024, 
            s3_key="key",
            token_count=100,
            chunk_index=0
        )
        
        # We need to run async method in sync test
        import asyncio
        result = asyncio.run(plugin.process(doc))
        
        self.assertEqual(result["type"], "financial_statement")
        self.assertEqual(result["extracted_data"]["revenue"], 1000000)
        print("Plugin System Passed.")

    def test_workflow_model(self):
        print("\nTesting Workflow Model Instantiation...")
        workflow = Workflow(
            name="Test Workflow",
            trigger={"type": "DOCUMENT"},
            actions=[{"type": "WEBHOOK"}]
        )
        self.assertEqual(workflow.name, "Test Workflow")
        self.assertEqual(workflow.trigger["type"], "DOCUMENT")
        print("Workflow Model Passed.")

if __name__ == '__main__':
    unittest.main()
