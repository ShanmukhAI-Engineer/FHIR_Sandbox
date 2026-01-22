"""
Generator Module - FHIR Data Generation
"""

from .llm import get_llm, get_active_llm_name

__all__ = ["get_llm", "get_active_llm_name"]
