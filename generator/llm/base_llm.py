"""
Base LLM Interface - All LLM implementations must follow this contract
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """Standardized response from any LLM"""
    content: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    model: str
    success: bool
    error: Optional[str] = None


@dataclass
class LLMConfig:
    """LLM configuration details"""
    name: str
    endpoint: str
    model: str
    supports_temperature: bool = True
    supports_max_tokens: bool = True
    max_context_length: int = 4096


class BaseLLM(ABC):
    """Abstract base class - all LLM implementations must follow this contract"""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """Generate text from prompt"""
        pass
    
    @abstractmethod
    def get_config(self) -> LLMConfig:
        """Return LLM configuration details"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if LLM service is available"""
        pass
