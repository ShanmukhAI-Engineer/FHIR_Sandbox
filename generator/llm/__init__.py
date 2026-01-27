"""
LLM Module - Enterprise LLM Only

This module provides the Enterprise LLM implementation with OAuth2 authentication.
"""

import os
from .base_llm import BaseLLM, LLMResponse, LLMConfig


# ============ CONFIGURATION ============

# Enterprise LLM is the only provider
DEFAULT_LLM = "enterprise"
ACTIVE_LLM = "enterprise"

# Provider configuration
PROVIDERS = {
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
    Factory function to get the Enterprise LLM instance.
    """
    from .enterprise_llm import EnterpriseLLM
    return EnterpriseLLM(PROVIDERS["enterprise"])


def get_active_llm_name() -> str:
    """Get name of active LLM"""
    return "enterprise"


def get_available_llms() -> list:
    """Get list of available LLMs"""
    return ["enterprise"]


__all__ = [
    "get_llm",
    "get_active_llm_name",
    "get_available_llms",
    "BaseLLM",
    "LLMResponse",
    "LLMConfig"
]
