
import os
import random
from typing import List, Optional

def get_rotated_gemini_key() -> Optional[str]:
    """
    Retrieves a random Gemini API key from the environment variables
    pattern GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.
    Falls back to GEMINI_API_KEY if no numbered keys are found.
    """
    keys: List[str] = []
    
    # Check for numbered keys 1-10
    for i in range(1, 11):
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if key:
            keys.append(key)
            
    # Check for standard key
    std_key = os.getenv("GEMINI_API_KEY")
    if std_key and std_key not in keys:
        keys.append(std_key)
        
    if not keys:
        return None
        
    selected_key = random.choice(keys)
    # Mask key for logging
    masked = f"...{selected_key[-4:]}"
    print(f"[Key Rotation] Selected Gemini Key: {masked} from pool of {len(keys)}")
    return selected_key
