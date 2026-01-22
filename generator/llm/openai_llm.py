"""
OpenAI LLM Implementation
Can be used with OpenAI API or any OpenAI-compatible endpoint (Horizon, etc.)
"""

import os
import time
from typing import Optional
from openai import OpenAI

from .base_llm import BaseLLM, LLMResponse, LLMConfig


class OpenAILLM(BaseLLM):
    """OpenAI-compatible LLM implementation"""
    
    def __init__(self, config: dict):
        self.endpoint = config.get("endpoint", "https://api.openai.com/v1")
        self.api_key = os.getenv(config.get("api_key_env", "OPENAI_API_KEY"))
        self.model = config.get("model", "gpt-3.5-turbo")
        self.timeout = config.get("timeout_seconds", 60)
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.endpoint,
            timeout=self.timeout
        )
    
    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            return LLMResponse(
                content=response.choices[0].message.content,
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
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
            name="OpenAI",
            endpoint=self.endpoint,
            model=self.model,
            supports_temperature=True,
            supports_max_tokens=True,
            max_context_length=16384 if "gpt-4" in self.model else 4096
        )
    
    def health_check(self) -> bool:
        try:
            response = self.generate("Hello", max_tokens=10)
            return response.success
        except:
            return False
