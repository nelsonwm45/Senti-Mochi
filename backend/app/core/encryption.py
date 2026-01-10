from cryptography.fernet import Fernet
import os

# Ensure key is generated or loaded. For demo, generating if not present.
# In production, this should be consistent and secure (e.g., KMS)
KEY = os.getenv("ENCRYPTION_KEY")
if not KEY:
    KEY = Fernet.generate_key().decode()
    # print(f"WARNING: Generated temporary encryption key: {KEY}") 

cipher_suite = Fernet(KEY.encode())

def encrypt_data(data: str) -> str:
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(token: str) -> str:
    return cipher_suite.decrypt(token.encode()).decode()
