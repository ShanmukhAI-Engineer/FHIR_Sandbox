"""
Horizon LLM Implementation (Enterprise)
Template for in-house LLM integration
"""

import os
import time
import requests
from typing import Optional

from .base_llm import BaseLLM, LLMResponse, LLMConfig


class HorizonLLM(BaseLLM):
    """Horizon (Enterprise) LLM implementation"""
    
    def __init__(self, config: dict):
        self.endpoint = config.get("endpoint", "")
        self.api_key = os.getenv(config.get("api_key_env", "HORIZON_API_KEY"))
        self.model = config.get("model", "horizon-default")
        self.timeout = config.get("timeout_seconds", 60)
        
        # Custom headers if needed
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Add any custom headers from config
        custom_headers = config.get("custom_headers", {})
        self.headers.update(custom_headers)
    
    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        
        # Build messages (OpenAI-compatible format)
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        # Build payload - modify this based on Horizon's actual API format
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            latency_ms = (time.time() - start_time) * 1000
            
            # Parse response - modify based on Horizon's actual response format
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            
            return LLMResponse(
                content=content,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                latency_ms=latency_ms,
                model=self.model,
                success=True
            )
            
        except Exception as e:
            return LLMResponse(
                content="",
                prompt_tokens=0,
                completion_tokens=0,
                latency_ms=(time.time() - start_time) * 1000,
                model=self.model,
                success=False,
                error=str(e)
            )
    
    def get_config(self) -> LLMConfig:
        return LLMConfig(
            name="Horizon",
            endpoint=self.endpoint,
            model=self.model,
            supports_temperature=True,
            supports_max_tokens=True,
            max_context_length=8192
        )
    
    def health_check(self) -> bool:
        try:
            response = self.generate("Hello", max_tokens=10)
            return response.success
        except:
            return False
