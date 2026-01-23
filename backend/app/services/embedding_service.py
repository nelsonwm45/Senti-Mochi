from typing import List
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    """
    Service for generating text embeddings using SentenceTransformers.
    Shared by Document Ingestion and News Ingestion.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self._model = None
    
    @property
    def model(self):
        """Lazy load the model"""
        if self._model is None:
            print(f"Loading embedding model: {self.model_name}...")
            self._model = SentenceTransformer(self.model_name, device='cpu')
        return self._model

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        Returns a list of vectors (lists of floats).
        """
        if not texts:
            return []
            
        try:
            embeddings = self.model.encode(texts, show_progress_bar=False)
            return embeddings.tolist()
        except Exception as e:
            print(f"Embedding generation failed: {e}")
            # Return zero vectors as fallback (384 dimensions for all-MiniLM-L6-v2)
            return [[0.0] * 384 for _ in texts]

# Singleton instance
embedding_service = EmbeddingService()
