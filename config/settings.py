"""
Application Settings - Central configuration
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
DDL_DIR = BASE_DIR / "ddl"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure directories exist
for dir_path in [DATA_DIR, OUTPUT_DIR, DDL_DIR, KNOWLEDGE_DIR, TEMPLATES_DIR]:
    dir_path.mkdir(exist_ok=True)

# LLM Settings
LLM_SETTINGS = {
    "default_temperature": 0.7,
    "default_max_tokens": 4000,
    "timeout_seconds": 60,
}

# RAG Settings
RAG_SETTINGS = {
    "chunk_size": 500,
    "chunk_overlap": 50,
    "top_k": 10,
    "max_context_tokens": 4000,
    "persist_directory": str(DATA_DIR / "chroma"),
    "collection_name": "synthfhir_knowledge",
}

# Embedding Settings
EMBEDDING_SETTINGS = {
    "model": os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
    "dimension": 384,
}

# Generation Settings
GENERATION_SETTINGS = {
    "default_record_count": 10,
    "max_record_count": 1000,
    "min_record_count": 1,
}

# Output Settings
OUTPUT_SETTINGS = {
    "directory": str(OUTPUT_DIR),
    "format": "csv",
    "timestamp_files": True,
}

# Quick Input Options (for UI dropdowns)
QUICK_INPUT_OPTIONS = {
    "gender": ["male", "female", "other", "unknown"],
    "states": [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
    ],
    "insurance_types": ["Commercial", "Medicare", "Medicaid", "Self-Pay", "Other"],
    "age_range": {"min": 0, "max": 120, "default_min": 18, "default_max": 65},
}
