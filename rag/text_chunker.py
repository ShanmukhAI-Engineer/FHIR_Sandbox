"""
Text Chunker - Split documents into chunks for embedding
"""

from typing import List, Dict
from dataclasses import dataclass


@dataclass
class Chunk:
    """Represents a chunk of text"""
    text: str
    metadata: Dict
    chunk_index: int
    start_char: int
    end_char: int


class TextChunker:
    """Split text into overlapping chunks"""
    
    def __init__(
        self, 
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Chunk]:
        """Split text into chunks with overlap"""
        if not text or len(text.strip()) == 0:
            return []
        
        metadata = metadata or {}
        chunks = []
        
        # Clean text
        text = text.strip()
        
        # If text is smaller than chunk_size, return as single chunk
        if len(text) <= self.chunk_size:
            return [Chunk(
                text=text,
                metadata=metadata,
                chunk_index=0,
                start_char=0,
                end_char=len(text)
            )]
        
        # Split into chunks with overlap
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence or paragraph boundary
            if end < len(text):
                # Look for sentence boundary (. ! ?)
                boundary = self._find_boundary(text, end, self.chunk_overlap)
                if boundary > start + self.min_chunk_size:
                    end = boundary
            
            chunk_text = text[start:end].strip()
            
            if len(chunk_text) >= self.min_chunk_size:
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_index"] = chunk_index
                chunk_metadata["total_length"] = len(text)
                
                chunks.append(Chunk(
                    text=chunk_text,
                    metadata=chunk_metadata,
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end
                ))
                chunk_index += 1
            
            # Move start position (with overlap)
            start = end - self.chunk_overlap
            
            # Prevent infinite loop
            if start >= len(text) - self.min_chunk_size:
                break
        
        return chunks
    
    def _find_boundary(self, text: str, position: int, search_range: int) -> int:
        """Find a good breaking point near the position"""
        # Search backwards from position for sentence boundary
        search_start = max(0, position - search_range)
        search_text = text[search_start:position]
        
        # Look for sentence endings
        for boundary_char in ['. ', '.\n', '! ', '!\n', '? ', '?\n', '\n\n']:
            idx = search_text.rfind(boundary_char)
            if idx != -1:
                return search_start + idx + len(boundary_char)
        
        # Look for paragraph break
        idx = search_text.rfind('\n')
        if idx != -1:
            return search_start + idx + 1
        
        # Look for space (word boundary)
        idx = search_text.rfind(' ')
        if idx != -1:
            return search_start + idx + 1
        
        return position


def chunk_document(text: str, metadata: Dict = None, chunk_size: int = 500) -> List[Chunk]:
    """Convenience function to chunk a document"""
    chunker = TextChunker(chunk_size=chunk_size)
    return chunker.chunk_text(text, metadata)
