"""
Mock Enterprise LLM Gateway (FastAPI) with OAuth2 Support
Run this to test the EnterpriseLLM client locally.

Usage: 
  uvicorn utils.mock_enterprise_gateway:app --reload --port 8000

Then set in .env:
  ACTIVE_LLM=enterprise
  ENTERPRISE_BASE_URL=http://localhost:8000
  ENTERPRISE_CLIENT_ID=test-client
  ENTERPRISE_CLIENT_SECRET=test-secret
"""

import time
import uuid
import secrets
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, Header, HTTPException, Form
from pydantic import BaseModel

app = FastAPI(title="Mock Enterprise LLM Gateway (OAuth2)")

# --- In-memory token store (for testing only) ---
_tokens = {}

# --- Models ---

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None  # Optional for enterprise APIs
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000

class Choice(BaseModel):
    message: Message
    finish_reason: str = "stop"

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Usage

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600

# --- OAuth2 Endpoint ---

@app.post("/v2/oauth2/token", response_model=TokenResponse)
async def oauth2_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...)
):
    """OAuth2 token endpoint - returns access token for client_credentials grant"""
    
    # Validate grant type
    if grant_type != "client_credentials":
        raise HTTPException(status_code=400, detail="Unsupported grant type")
    
    # Simple validation (for testing, accept any non-empty credentials)
    if not client_id or not client_secret:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate token
    token = secrets.token_urlsafe(32)
    expires_in = 3600
    
    # Store for validation (in production, use proper token storage)
    _tokens[token] = {
        "client_id": client_id,
        "expires_at": datetime.now() + timedelta(seconds=expires_in)
    }
    
    return TokenResponse(
        access_token=token,
        expires_in=expires_in
    )

# --- Chat Completion Endpoint (Enterprise /v2 format) ---

@app.post("/v2/text/chats", response_model=ChatCompletionResponse)
async def enterprise_chat(
    request: ChatCompletionRequest,
    authorization: Optional[str] = Header(None)
):
    """Enterprise chat endpoint - matches /v2/text/chats path"""
    
    # Validate token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")
    
    token = authorization.replace("Bearer ", "")
    if token not in _tokens:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Check expiry
    token_data = _tokens[token]
    if datetime.now() > token_data["expires_at"]:
        del _tokens[token]
        raise HTTPException(status_code=401, detail="Token expired")
    
    print(f"[Mock Gateway] Received chat request from client: {token_data['client_id']}")
    print(f"[Mock Gateway] Messages: {len(request.messages)}")
    
    # Mock response logic: Return a JSON array that TableGenerator expects
    content = """
[
  {
    "ID": "pat-101",
    "NAME": "John Doe",
    "GENDER": "male",
    "BIRTH_DATE": "1985-05-15",
    "STATE": "Texas"
  },
  {
    "ID": "pat-102",
    "NAME": "Jane Smith",
    "GENDER": "female",
    "BIRTH_DATE": "1992-08-22",
    "STATE": "California"
  }
]
"""
    
    # Simulate processing time
    time.sleep(0.3)
    
    return ChatCompletionResponse(
        id=f"mock-{uuid.uuid4()}",
        created=int(time.time()),
        model=request.model or "enterprise-mock",
        choices=[
            Choice(message=Message(role="assistant", content=content))
        ],
        usage=Usage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
    )

# --- Legacy OpenAI-compatible endpoint (for backward compatibility) ---

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def openai_compatible_chat(
    request: ChatCompletionRequest,
    authorization: Optional[str] = Header(None)
):
    """OpenAI-compatible endpoint for testing with openai_llm.py"""
    
    content = """
[
  {
    "ID": "pat-201",
    "NAME": "Legacy User",
    "GENDER": "male",
    "BIRTH_DATE": "1990-01-01",
    "STATE": "New York"
  }
]
"""
    
    time.sleep(0.2)
    
    return ChatCompletionResponse(
        id=f"mock-{uuid.uuid4()}",
        created=int(time.time()),
        model=request.model or "mock-openai",
        choices=[
            Choice(message=Message(role="assistant", content=content))
        ],
        usage=Usage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
    )

# --- Health Check ---

@app.get("/health")
async def health():
    return {"status": "ok", "provider": "mock-enterprise-oauth2"}
