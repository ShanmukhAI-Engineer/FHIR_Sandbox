"""
Enterprise LLM Implementation with OAuth2 Authentication
Supports custom enterprise endpoints with /v2/oauth2/token and /v2/text/chats
"""

import os
import time
import requests
from typing import Optional
from datetime import datetime, timedelta

from .base_llm import BaseLLM, LLMResponse, LLMConfig


class EnterpriseLLM(BaseLLM):
    """Enterprise LLM with OAuth2 authentication and custom /v2 endpoints"""
    
    def __init__(self, config: dict):
        # Base URL for enterprise API
        self.base_url = os.getenv("ENTERPRISE_BASE_URL", config.get("base_url", ""))
        
        # OAuth2 credentials
        self.client_id = os.getenv("ENTERPRISE_CLIENT_ID", "")
        self.client_secret = os.getenv("ENTERPRISE_CLIENT_SECRET", "")
        
        # Endpoint paths (configurable)
        self.token_path = config.get("token_path", "/v2/oauth2/token")
        self.chat_path = config.get("chat_path", "/v2/text/chats")
        
        # Model (optional - some enterprise APIs don't require it in body)
        self.model = os.getenv("ENTERPRISE_MODEL", config.get("model", ""))
        self.timeout = config.get("timeout_seconds", 120)
        
        # Token caching
        self._access_token = None
        self._token_expires_at = None
    
    def _get_token(self) -> str:
        """Get OAuth2 access token, refreshing if expired"""
        
        # Return cached token if still valid
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(minutes=1):
                return self._access_token
        
        # Request new token
        token_url = f"{self.base_url}{self.token_path}"
        
        # Standard OAuth2 client_credentials grant
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            response = requests.post(
                token_url,
                data=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            token_data = response.json()
            self._access_token = token_data.get("access_token")
            
            # Calculate expiry (default 1 hour if not provided)
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            return self._access_token
            
        except Exception as e:
            raise RuntimeError(f"OAuth2 token request failed: {e}")
    
    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        
        start_time = time.time()
        
        try:
            # Get OAuth token
            token = self._get_token()
            
            # Build request headers
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Build messages array
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            # Build payload - minimal format as per user's enterprise spec
            payload = {
                "messages": messages
            }
            
            # Add optional fields if configured
            if self.model:
                payload["model"] = self.model
            if temperature != 0.7:
                payload["temperature"] = temperature
            if max_tokens != 2000:
                payload["max_tokens"] = max_tokens
            
            # Make chat request
            chat_url = f"{self.base_url}{self.chat_path}"
            
            response = requests.post(
                chat_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            latency_ms = (time.time() - start_time) * 1000
            
            # Parse OpenAI-compatible response
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            
            return LLMResponse(
                content=content,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                latency_ms=latency_ms,
                model=self.model or "enterprise",
                success=True
            )
            
        except Exception as e:
            return LLMResponse(
                content="",
                prompt_tokens=0,
                completion_tokens=0,
                latency_ms=(time.time() - start_time) * 1000,
                model=self.model or "enterprise",
                success=False,
                error=str(e)
            )
    
    def get_config(self) -> LLMConfig:
        return LLMConfig(
            name="Enterprise (OAuth2)",
            endpoint=f"{self.base_url}{self.chat_path}",
            model=self.model or "enterprise",
            supports_temperature=True,
            supports_max_tokens=True,
            max_context_length=8192
        )
    
    def health_check(self) -> bool:
        try:
            # Try to get a token as health check
            self._get_token()
            return True
        except:
            return False
