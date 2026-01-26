"""
LLM Module - Pluggable LLM Architecture

To swap LLMs:
1. Change DEFAULT_LLM in this file, OR
2. Set ACTIVE_LLM environment variable

To add a new LLM:
1. Create new file (e.g., new_llm.py) implementing BaseLLM
2. Add to PROVIDERS dict
3. Update get_llm() factory
"""

import os
from .base_llm import BaseLLM, LLMResponse, LLMConfig


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
    "enterprise": {
        "base_url": os.getenv("ENTERPRISE_BASE_URL", ""),
        "token_path": os.getenv("ENTERPRISE_TOKEN_PATH", "/v2/oauth2/token"),
        "chat_path": os.getenv("ENTERPRISE_CHAT_PATH", "/v2/text/chats"),
        "model": os.getenv("ENTERPRISE_MODEL", ""),
        "timeout_seconds": 120,
    },
}

# ========================================

def get_llm() -> BaseLLM:
    """
    Factory function to get the active LLM instance using LAZY LOADING.
    This prevents ModuleNotFound errors if a provider's dependencies are missing.
    """
    
    if ACTIVE_LLM not in PROVIDERS:
        available = list(PROVIDERS.keys())
        raise ValueError(f"Unknown LLM Provider: {ACTIVE_LLM}. Available: {available}")
    
    llm_config = PROVIDERS[ACTIVE_LLM]
    
    try:
        if ACTIVE_LLM == "openai":
            from .openai_llm import OpenAILLM
            return OpenAILLM(llm_config)
            
        elif ACTIVE_LLM == "horizon":
            from .horizon_llm import HorizonLLM
            return HorizonLLM(llm_config)
            
        elif ACTIVE_LLM == "enterprise":
            from .enterprise_llm import EnterpriseLLM
            return EnterpriseLLM(llm_config)
            
        else:
            raise ValueError(f"LLM provider {ACTIVE_LLM} is registered but not implemented in factory.")
            
    except ImportError as e:
        raise ImportError(
            f"Could not load LLM provider '{ACTIVE_LLM}'. "
            f"Ensure its dependencies are installed. Error: {e}"
        )


def get_active_llm_name() -> str:
    """Get name of active LLM"""
    return ACTIVE_LLM


def get_available_llms() -> list:
    """Get list of available LLMs"""
    return list(PROVIDERS.keys())


__all__ = [
    "get_llm",
    "get_active_llm_name",
    "get_available_llms",
    "BaseLLM",
    "LLMResponse",
    "LLMConfig"
]
