from abc import ABC, abstractmethod
from app.models import Document

class DocumentProcessorPlugin(ABC):
    @abstractmethod
    async def process(self, document: Document) -> dict:
        """Custom processing logic"""
        pass

class EmbeddingPlugin(ABC):
    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Custom embedding generation"""
        pass
