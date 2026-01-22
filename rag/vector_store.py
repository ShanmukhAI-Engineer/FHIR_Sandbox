"""
Vector Store - ChromaDB wrapper for storing and querying embeddings
"""

import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from .embeddings import get_embedding_model


@dataclass
class SearchResult:
    """Result from vector search"""
    text: str
    metadata: Dict
    score: float
    id: str


class VectorStore:
    """ChromaDB-based vector store for RAG"""
    
    def __init__(
        self, 
        persist_directory: str = "data/chroma",
        collection_name: str = "synthfhir_knowledge"
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.embedding_model = None
        self._initialize()
    
    def _initialize(self):
        """Initialize ChromaDB client and collection"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Create persist directory if needed
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialize ChromaDB with persistence
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "SynthFHIR knowledge base"}
            )
            
            # Initialize embedding model
            self.embedding_model = get_embedding_model()
            
            print(f"Vector store initialized. Collection: {self.collection_name}")
            print(f"Documents in collection: {self.collection.count()}")
            
        except ImportError:
            raise ImportError(
                "chromadb not installed. "
                "Install with: pip install chromadb"
            )
    
    def add_documents(
        self, 
        texts: List[str], 
        metadatas: List[Dict] = None,
        ids: List[str] = None
    ) -> int:
        """Add documents to the vector store"""
        if not texts:
            return 0
        
        # Generate IDs if not provided
        if ids is None:
            import hashlib
            ids = [
                hashlib.md5(f"{text[:100]}_{i}".encode()).hexdigest()
                for i, text in enumerate(texts)
            ]
        
        # Generate embeddings
        embeddings = self.embedding_model.embed_batch(texts)
        
        # Prepare metadatas
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        # Add to collection
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        return len(texts)
    
    def search(
        self, 
        query: str, 
        n_results: int = 10,
        filter_metadata: Dict = None
    ) -> List[SearchResult]:
        """Search for similar documents"""
        # Generate query embedding
        query_embedding = self.embedding_model.embed(query)
        
        # Build query parameters
        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"]
        }
        
        if filter_metadata:
            query_params["where"] = filter_metadata
        
        # Execute search
        results = self.collection.query(**query_params)
        
        # Convert to SearchResult objects
        search_results = []
        if results and results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                search_results.append(SearchResult(
                    text=doc,
                    metadata=results['metadatas'][0][i] if results['metadatas'] else {},
                    score=1 - results['distances'][0][i] if results['distances'] else 0,
                    id=results['ids'][0][i] if results['ids'] else ""
                ))
        
        return search_results
    
    def search_by_resource(
        self, 
        query: str, 
        resources: List[str],
        n_results: int = 10
    ) -> List[SearchResult]:
        """Search within specific resources (metadata filter)"""
        # Include global resources
        resources_with_global = list(set(resources + ["global"]))
        
        # ChromaDB filter for multiple values
        filter_metadata = {
            "resource": {"$in": resources_with_global}
        }
        
        return self.search(query, n_results, filter_metadata)
    
    def get_all_by_resource(self, resource: str) -> List[SearchResult]:
        """Get all documents for a specific resource"""
        results = self.collection.get(
            where={"resource": resource},
            include=["documents", "metadatas"]
        )
        
        search_results = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents']):
                search_results.append(SearchResult(
                    text=doc,
                    metadata=results['metadatas'][i] if results['metadatas'] else {},
                    score=1.0,
                    id=results['ids'][i] if results['ids'] else ""
                ))
        
        return search_results
    
    def delete_by_resource(self, resource: str) -> int:
        """Delete all documents for a specific resource"""
        # Get IDs to delete
        results = self.collection.get(
            where={"resource": resource},
            include=[]
        )
        
        if results and results['ids']:
            self.collection.delete(ids=results['ids'])
            return len(results['ids'])
        
        return 0
    
    def clear(self):
        """Clear all documents from the collection"""
        # Delete and recreate collection
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "SynthFHIR knowledge base"}
        )
    
    def count(self) -> int:
        """Get total document count"""
        return self.collection.count()
    
    def count_by_resource(self, resource: str) -> int:
        """Get document count for a specific resource"""
        results = self.collection.get(
            where={"resource": resource},
            include=[]
        )
        return len(results['ids']) if results and results['ids'] else 0


# Singleton instance
_vector_store = None


def get_vector_store() -> VectorStore:
    """Get or create singleton vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
