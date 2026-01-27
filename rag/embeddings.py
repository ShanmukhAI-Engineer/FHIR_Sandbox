"""
Embeddings Module - Supports local and enterprise embedding providers
"""

import os
import time
import requests
from typing import List, Optional
from datetime import datetime, timedelta
import numpy as np


class EnterpriseEmbeddingModel:
    """Enterprise embedding model using OAuth2 and /openai/v1/embeddings"""
    
    def __init__(self):
        self.base_url = os.getenv("ENTERPRISE_BASE_URL", "")
        self.client_id = os.getenv("ENTERPRISE_CLIENT_ID", "")
        self.client_secret = os.getenv("ENTERPRISE_CLIENT_SECRET", "")
        self.token_path = os.getenv("ENTERPRISE_TOKEN_PATH", "/v2/oauth2/token")
        self.embedding_path = os.getenv("ENTERPRISE_EMBEDDING_PATH", "/openai/v1/embeddings")
        self.embedding_model = os.getenv("ENTERPRISE_EMBEDDING_MODEL", "text-embedding-ada-002")
        self.timeout = 60
        
        # Token caching
        self._access_token = None
        self._token_expires_at = None
        
        # Dimension (will be set after first call, default for ada-002)
        self.dimension = 1536
        
        print(f"Enterprise embedding initialized: {self.base_url}{self.embedding_path}")
    
    def _get_token(self) -> str:
        """Get OAuth2 access token, refreshing if expired"""
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(minutes=1):
                return self._access_token
        
        token_url = f"{self.base_url}{self.token_path}"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        response = requests.post(token_url, data=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        token_data = response.json()
        self._access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 3600)
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        return self._access_token
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        return self.embed_batch([text])[0]
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        token = self._get_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # OpenAI-compatible payload
        payload = {
            "input": texts,
            "model": self.embedding_model
        }
        
        url = f"{self.base_url}{self.embedding_path}"
        response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract embeddings from OpenAI-compatible response
        embeddings = [item["embedding"] for item in data.get("data", [])]
        
        # Update dimension from response
        if embeddings:
            self.dimension = len(embeddings[0])
        
        return embeddings
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension


class LocalEmbeddingModel:
    """Local embedding model using sentence-transformers"""
    
    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", self.DEFAULT_MODEL)
        self.model = None
        self.dimension = 384
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


# Wrapper class with automatic fallback
class EmbeddingModel:
    """Unified embedding model with automatic fallback: Enterprise → Local MiniLM"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.provider = os.getenv("EMBEDDING_PROVIDER", "auto").lower()
        self._model = None
        self.dimension = 384  # Default for MiniLM
        self.active_provider = None
        
        self._initialize_model(model_name)
    
    def _initialize_model(self, model_name: Optional[str] = None):
        """Initialize model with fallback logic"""
        
        # If explicitly set to local, use local only
        if self.provider == "local":
            print("[Embeddings] Using local embedding model (EMBEDDING_PROVIDER=local)")
            self._model = LocalEmbeddingModel(model_name)
            self.active_provider = "local"
            self.dimension = self._model.dimension
            return
        
        # Try enterprise first if configured (provider=enterprise or auto)
        if self.provider in ["enterprise", "auto"]:
            enterprise_url = os.getenv("ENTERPRISE_BASE_URL", "")
            enterprise_id = os.getenv("ENTERPRISE_CLIENT_ID", "")
            
            if enterprise_url and enterprise_id:
                try:
                    print("[Embeddings] Trying enterprise embedding provider...")
                    self._model = EnterpriseEmbeddingModel()
                    # Test connection with a simple embed
                    test_result = self._model.embed("test")
                    if test_result:
                        self.active_provider = "enterprise"
                        self.dimension = self._model.dimension
                        print(f"[Embeddings] ✅ Enterprise embeddings active (dim={self.dimension})")
                        return
                except Exception as e:
                    print(f"[Embeddings] ⚠️ Enterprise embedding failed: {e}")
        
        # Fallback to local MiniLM
        print("[Embeddings] Falling back to local MiniLM model...")
        try:
            self._model = LocalEmbeddingModel(model_name or "sentence-transformers/all-MiniLM-L6-v2")
            self.active_provider = "local"
            self.dimension = self._model.dimension
            print(f"[Embeddings] ✅ Local MiniLM active (dim={self.dimension})")
        except ImportError as e:
            raise RuntimeError(
                f"No embedding provider available. "
                f"Either configure enterprise embeddings or install sentence-transformers: {e}"
            )
    
    def embed(self, text: str) -> List[float]:
        return self._model.embed(text)
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        return self._model.embed_batch(texts, batch_size)
    
    def get_dimension(self) -> int:
        return self._model.get_dimension()
    
    def get_provider_info(self) -> str:
        """Return info about active provider"""
        return f"{self.active_provider} (dim={self.dimension})"


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
