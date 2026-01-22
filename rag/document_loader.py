"""
Document Loader - Load and parse various document formats
Supports: TXT, PDF, CSV, Excel, SQL (DDL)
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Document:
    """Represents a loaded document"""
    content: str
    metadata: Dict
    source: str
    doc_type: str


class DocumentLoader:
    """Load documents from various formats"""
    
    SUPPORTED_EXTENSIONS = {'.txt', '.pdf', '.csv', '.xlsx', '.xls', '.sql', '.md'}
    
    def __init__(self):
        self._loaders = {
            '.txt': self._load_text,
            '.md': self._load_text,
            '.sql': self._load_text,
            '.pdf': self._load_pdf,
            '.csv': self._load_csv,
            '.xlsx': self._load_excel,
            '.xls': self._load_excel,
        }
    
    def load_file(self, file_path: str, metadata: Optional[Dict] = None) -> Optional[Document]:
        """Load a single file"""
        path = Path(file_path)
        
        if not path.exists():
            print(f"Warning: File not found: {file_path}")
            return None
        
        ext = path.suffix.lower()
        if ext not in self._loaders:
            print(f"Warning: Unsupported file type: {ext}")
            return None
        
        try:
            content = self._loaders[ext](file_path)
            
            doc_metadata = {
                "filename": path.name,
                "extension": ext,
                "size_bytes": path.stat().st_size,
            }
            if metadata:
                doc_metadata.update(metadata)
            
            return Document(
                content=content,
                metadata=doc_metadata,
                source=str(path),
                doc_type=ext[1:]  # Remove the dot
            )
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None
    
    def load_directory(
        self, 
        directory: str, 
        recursive: bool = True,
        metadata: Optional[Dict] = None
    ) -> List[Document]:
        """Load all supported documents from a directory"""
        documents = []
        dir_path = Path(directory)
        
        if not dir_path.exists():
            print(f"Warning: Directory not found: {directory}")
            return documents
        
        pattern = "**/*" if recursive else "*"
        
        for file_path in dir_path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                doc = self.load_file(str(file_path), metadata)
                if doc:
                    documents.append(doc)
        
        return documents
    
    def _load_text(self, file_path: str) -> str:
        """Load text-based files (txt, md, sql)"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def _load_pdf(self, file_path: str) -> str:
        """Load PDF files"""
        try:
            import PyPDF2
            
            text_parts = []
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            
            return "\n\n".join(text_parts)
        except ImportError:
            print("Warning: PyPDF2 not installed. Install with: pip install PyPDF2")
            return ""
    
    def _load_csv(self, file_path: str) -> str:
        """Load CSV files and convert to readable text"""
        try:
            import pandas as pd
            
            df = pd.read_csv(file_path)
            
            # Convert to readable format
            lines = []
            lines.append(f"CSV File: {Path(file_path).name}")
            lines.append(f"Columns: {', '.join(df.columns.tolist())}")
            lines.append(f"Rows: {len(df)}")
            lines.append("")
            
            # Include sample data (first 50 rows max)
            lines.append("Data:")
            lines.append(df.head(50).to_string(index=False))
            
            return "\n".join(lines)
        except ImportError:
            print("Warning: pandas not installed. Install with: pip install pandas")
            return ""
    
    def _load_excel(self, file_path: str) -> str:
        """Load Excel files and convert to readable text"""
        try:
            import pandas as pd
            
            # Load all sheets
            xl = pd.ExcelFile(file_path)
            
            text_parts = []
            text_parts.append(f"Excel File: {Path(file_path).name}")
            text_parts.append(f"Sheets: {', '.join(xl.sheet_names)}")
            text_parts.append("")
            
            for sheet_name in xl.sheet_names:
                df = pd.read_excel(xl, sheet_name=sheet_name)
                text_parts.append(f"--- Sheet: {sheet_name} ---")
                text_parts.append(f"Columns: {', '.join(df.columns.astype(str).tolist())}")
                text_parts.append(df.head(50).to_string(index=False))
                text_parts.append("")
            
            return "\n".join(text_parts)
        except ImportError:
            print("Warning: openpyxl not installed. Install with: pip install openpyxl")
            return ""


def load_ddl(file_path: str, resource_name: str) -> Document:
    """Convenience function to load a DDL file with proper metadata"""
    loader = DocumentLoader()
    doc = loader.load_file(file_path, metadata={
        "resource": resource_name,
        "type": "ddl"
    })
    return doc


def load_guidelines(directory: str, resource_name: str) -> List[Document]:
    """Convenience function to load guidelines for a resource"""
    loader = DocumentLoader()
    docs = loader.load_directory(directory, metadata={
        "resource": resource_name,
        "type": "guideline"
    })
    return docs
