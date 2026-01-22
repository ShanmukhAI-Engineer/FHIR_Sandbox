"""
Embeddings Module - Generate embeddings using sentence-transformers
Uses all-MiniLM-L6-v2 by default (local, no API calls)
"""

import os
from typing import List, Optional
import numpy as np


class EmbeddingModel:
    """Wrapper for sentence-transformers embedding model"""
    
    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", self.DEFAULT_MODEL)
        self.model = None
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model"""
        try:
            from sentence_transformers import SentenceTransformer
            
            print(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            print(f"Model loaded. Embedding dimension: {self.dimension}")
            
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        embeddings = self.model.encode(
            texts, 
            convert_to_numpy=True,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100
        )
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension


# Singleton instance for caching
_embedding_model = None


def get_embedding_model() -> EmbeddingModel:
    """Get or create singleton embedding model instance"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model


def embed_text(text: str) -> List[float]:
    """Convenience function to embed a single text"""
    model = get_embedding_model()
    return model.embed(text)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Convenience function to embed multiple texts"""
    model = get_embedding_model()
    return model.embed_batch(texts)
