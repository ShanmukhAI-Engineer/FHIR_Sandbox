"""
LLM Module - Pluggable LLM Architecture

To swap LLMs:
1. Change DEFAULT_LLM in this file, OR
2. Set ACTIVE_LLM environment variable

To add a new LLM:
1. Create new file (e.g., new_llm.py) implementing BaseLLM
2. Add to PROVIDERS dict
3. Add to LLM_REGISTRY dict
"""

import os
from .base_llm import BaseLLM, LLMResponse, LLMConfig
from .openai_llm import OpenAILLM
from .horizon_llm import HorizonLLM


# ============ CONFIGURATION ============

# Default LLM (can be overridden by environment variable)
DEFAULT_LLM = "openai"

# Get active LLM from environment or use default
ACTIVE_LLM = os.getenv("ACTIVE_LLM", DEFAULT_LLM)

# Provider configurations
PROVIDERS = {
    "openai": {
        "endpoint": os.getenv("OPENAI_ENDPOINT", "https://api.openai.com/v1"),
        "api_key_env": "OPENAI_API_KEY",
        "model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        "timeout_seconds": 60,
    },
    "horizon": {
        "endpoint": os.getenv("HORIZON_ENDPOINT", "https://your-horizon-endpoint/v1/chat/completions"),
        "api_key_env": "HORIZON_API_KEY",
        "model": os.getenv("HORIZON_MODEL", "horizon-v1"),
        "timeout_seconds": 60,
    },
    # Add more providers here
    # "new_llm": {
    #     "endpoint": os.getenv("NEW_LLM_ENDPOINT", ""),
    #     "api_key_env": "NEW_LLM_API_KEY",
    #     "model": os.getenv("NEW_LLM_MODEL", ""),
    #     "timeout_seconds": 60,
    # },
}

# ========================================

# Registry of available LLMs
LLM_REGISTRY = {
    "openai": OpenAILLM,
    "horizon": HorizonLLM,
    # Add new LLMs here
}


def get_llm() -> BaseLLM:
    """
    Factory function to get the active LLM instance.
    
    Priority:
    1. ACTIVE_LLM environment variable
    2. DEFAULT_LLM in this file
    """
    if ACTIVE_LLM not in LLM_REGISTRY:
        available = list(LLM_REGISTRY.keys())
        raise ValueError(f"Unknown LLM: {ACTIVE_LLM}. Available: {available}")
    
    if ACTIVE_LLM not in PROVIDERS:
        raise ValueError(f"No configuration found for LLM: {ACTIVE_LLM}")
    
    llm_class = LLM_REGISTRY[ACTIVE_LLM]
    llm_config = PROVIDERS[ACTIVE_LLM]
    
    return llm_class(llm_config)


def get_active_llm_name() -> str:
    """Get name of active LLM"""
    return ACTIVE_LLM


def get_available_llms() -> list:
    """Get list of available LLMs"""
    return list(LLM_REGISTRY.keys())


__all__ = [
    "get_llm",
    "get_active_llm_name",
    "get_available_llms",
    "BaseLLM",
    "LLMResponse",
    "LLMConfig"
]
