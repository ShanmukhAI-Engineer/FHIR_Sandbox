"""
Mock Enterprise LLM Gateway (FastAPI)
Run this to test the EnterpriseLLM client locally.
Usage: uvicorn utils.mock_enterprise_gateway:app --reload --port 8000
"""

import time
import uuid
from typing import List, Optional
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Mock Enterprise LLM Gateway")

# --- Models ---

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
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

# --- Endpoints ---

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    authorization: Optional[str] = Header(None)
):
    print(f"Received request for model: {request.model}")
    print(f"Last message: {request.messages[-1].content[:50]}...")
    
    # Simple validation (optional for mock)
    if not authorization or not authorization.startswith("Bearer "):
        # In a real enterprise app, you'd check the token strictly
        pass

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
    time.sleep(0.5)
    
    return ChatCompletionResponse(
        id=f"mock-{uuid.uuid4()}",
        created=int(time.time()),
        model=request.model,
        choices=[
            Choice(message=Message(role="assistant", content=content))
        ],
        usage=Usage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
    )

@app.get("/health")
async def health():
    return {"status": "ok", "provider": "mock-enterprise"}
