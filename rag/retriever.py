"""
Retriever - High-level RAG retrieval interface
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

from .document_loader import DocumentLoader, Document
from .text_chunker import TextChunker, Chunk
from .vector_store import VectorStore, SearchResult, get_vector_store


@dataclass
class RetrievalResult:
    """Result from RAG retrieval"""
    context: str
    chunks: List[SearchResult]
    total_found: int
    resources_searched: List[str]
    warning: Optional[str] = None


class Retriever:
    """High-level RAG retrieval interface"""
    
    def __init__(
        self, 
        vector_store: VectorStore = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        top_k: int = 10,
        max_context_tokens: int = 4000
    ):
        self.vector_store = vector_store or get_vector_store()
        self.chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.loader = DocumentLoader()
        self.top_k = top_k
        self.max_context_tokens = max_context_tokens
    
    def index_document(self, document: Document) -> int:
        """Index a single document into the vector store"""
        # Chunk the document
        chunks = self.chunker.chunk_text(document.content, document.metadata)
        
        if not chunks:
            return 0
        
        # Prepare for vector store
        texts = [chunk.text for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        # Add to vector store
        return self.vector_store.add_documents(texts, metadatas)
    
    def index_directory(self, directory: str, resource: str) -> int:
        """Index all documents in a directory"""
        documents = self.loader.load_directory(
            directory, 
            metadata={"resource": resource, "type": "guideline"}
        )
        
        total_indexed = 0
        for doc in documents:
            total_indexed += self.index_document(doc)
        
        return total_indexed
    
    def index_ddl(self, file_path: str, resource: str) -> int:
        """Index a DDL file"""
        doc = self.loader.load_file(
            file_path,
            metadata={"resource": resource, "type": "ddl"}
        )
        
        if doc:
            # For DDL, keep as single chunk (usually small enough)
            return self.vector_store.add_documents(
                texts=[doc.content],
                metadatas=[doc.metadata]
            )
        return 0
    
    def retrieve(
        self, 
        query: str, 
        resources: List[str],
        include_ddl: bool = True
    ) -> RetrievalResult:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: User's prompt/query
            resources: List of resources to search (e.g., ["patient", "claim"])
            include_ddl: Always include DDL even if not in top results
        """
        # Search vector store
        results = self.vector_store.search_by_resource(
            query=query,
            resources=resources,
            n_results=self.top_k * 2  # Get more for filtering
        )
        
        if not results:
            return RetrievalResult(
                context="",
                chunks=[],
                total_found=0,
                resources_searched=resources,
                warning="No relevant documents found. Using defaults."
            )
        
        # Separate DDL and guidelines
        ddl_results = [r for r in results if r.metadata.get("type") == "ddl"]
        guideline_results = [r for r in results if r.metadata.get("type") != "ddl"]
        
        # Build context with token limit
        context_parts = []
        current_length = 0
        included_chunks = []
        
        # Always include DDL first (priority)
        if include_ddl:
            for result in ddl_results:
                chunk_length = len(result.text)
                if current_length + chunk_length <= self.max_context_tokens * 4:  # Rough char estimate
                    resource = result.metadata.get("resource", "unknown")
                    context_parts.append(f"## DDL Structure: {resource.upper()}\n{result.text}")
                    current_length += chunk_length
                    included_chunks.append(result)
        
        # Add guidelines by relevance
        context_parts.append("\n## Guidelines:")
        for result in guideline_results[:self.top_k]:
            chunk_length = len(result.text)
            if current_length + chunk_length <= self.max_context_tokens * 4:
                context_parts.append(f"\n{result.text}")
                current_length += chunk_length
                included_chunks.append(result)
        
        context = "\n".join(context_parts)
        
        return RetrievalResult(
            context=context,
            chunks=included_chunks,
            total_found=len(results),
            resources_searched=resources,
            warning=None if included_chunks else "Limited context available."
        )
    
    def get_ddl_for_resource(self, resource: str) -> Optional[str]:
        """Get DDL content for a specific resource"""
        results = self.vector_store.collection.get(
            where={"$and": [
                {"resource": resource},
                {"type": "ddl"}
            ]},
            include=["documents"]
        )
        
        if results and results['documents']:
            return results['documents'][0]
        return None


# Singleton instance
_retriever = None


def get_retriever() -> Retriever:
    """Get or create singleton retriever instance"""
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever
