# SynthFHIR - Extending Resources & Deployment Guide

## Part 1: Extending Resources (Adding New FHIR Resources)

### Step-by-Step: Add a New Resource (e.g., "Medication")

#### Step 1: Create the DDL file
Create `ddl/medication.sql`:

```sql
CREATE TABLE FHIR_MEDICATION_RESOURCE_STG (
    ID VARCHAR(32) NOT NULL,
    RESOURCE_TYPE VARCHAR(20) DEFAULT 'Medication',
    STATUS VARCHAR(20),
    CODE VARIANT,
    MANUFACTURER VARCHAR(100),
    FORM VARIANT,
    AMOUNT VARIANT,
    INGREDIENT ARRAY,
    BATCH VARIANT,
    -- Metadata (will be excluded)
    EDL_LOAD_DTM TIMESTAMP,
    EDL_RUN_ID VARCHAR(50),
    HASH_KEY VARCHAR(64)
);
```

#### Step 2: Create the Golden Template
Create `templates/medication_golden.json`:

```json
[
  {
    "ID": "3f987ee038494bddb2433e7f0113948e",
    "RESOURCE_TYPE": "Medication",
    "STATUS": "active",
    "CODE": {
      "coding": [
        {
          "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
          "code": "1049502",
          "display": "Acetaminophen 325 MG Oral Tablet"
        }
      ]
    },
    "MANUFACTURER": "Generic Pharma Inc",
    "FORM": {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "385055001",
          "display": "Tablet"
        }
      ]
    },
    "AMOUNT": {
      "numerator": {"value": 100, "unit": "tablets"},
      "denominator": {"value": 1, "unit": "bottle"}
    },
    "INGREDIENT": [],
    "BATCH": {
      "lotNumber": "LOT123456",
      "expirationDate": "2027-12-31"
    }
  }
]
```

#### Step 3: Add to Resource Configuration
Edit `config/resources.py`:

```python
RESOURCES = {
    # ...existing resources...
    
    "medication": {
        "enabled": True,
        "display_name": "Medication",
        "description": "FHIR Medication resource",
        "ddl_file": str(DDL_DIR / "medication.sql"),
        "knowledge_dir": str(KNOWLEDGE_DIR / "medication"),
        "template_file": str(TEMPLATES_DIR / "medication_golden.json"),
        "exclude_columns": [
            "EDL_LOAD_DTM",
            "EDL_RUN_ID",
            "HASH_KEY",
        ],
        "md5_fields": [],
        "relationships": [],  # Or link to patient if needed
    },
}
```

#### Step 4: (Optional) Add Guidelines
Create `knowledge/medication/guidelines.md`:

```markdown
# Medication Generation Guidelines

## Code Systems
- Use RxNorm for drug codes
- Use SNOMED CT for form codes

## Status Values
- active, inactive, entered-in-error
```

#### Step 5: Reindex Knowledge Base
In the Streamlit UI, go to Settings → Click "Reindex Documents"

---

## Part 2: Scaling the Application

### Current Architecture (Streamlit)
```
User Browser → Streamlit (app.py) → Enterprise LLM API
                     ↓
              ChromaDB (RAG)
```

**Limitations:**
- Single process
- In-memory session state
- Not designed for high concurrency

### Option A: Scale Streamlit (Simple)

For 5-20 concurrent users:

```bash
# Run multiple Streamlit instances behind nginx
streamlit run app.py --server.port 8501 &
streamlit run app.py --server.port 8502 &
streamlit run app.py --server.port 8503 &
```

Nginx load balancer config:
```nginx
upstream synthfhir {
    server localhost:8501;
    server localhost:8502;
    server localhost:8503;
}

server {
    listen 80;
    location / {
        proxy_pass http://synthfhir;
    }
}
```

### Option B: FastAPI Backend (Recommended for Scale)

For 50+ concurrent users or API access:

**When to use FastAPI:**
- Need REST API access (not just UI)
- High concurrency requirements
- Microservices architecture
- Kubernetes deployment

---

## Part 3: FastAPI Deployment

### Architecture with FastAPI

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐
│ Streamlit   │────▶│  FastAPI    │────▶│ Enterprise LLM   │
│ (UI)        │     │  (Backend)  │     │ API              │
└─────────────┘     └─────────────┘     └──────────────────┘
                          │
                    ┌─────┴─────┐
                    │ ChromaDB  │
                    │ (Shared)  │
                    └───────────┘
```

### Step 1: Create FastAPI Backend

Create `api/main.py`:

```python
"""
SynthFHIR FastAPI Backend
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import os

from generator.table_generator import TableGenerator
from config import get_enabled_resources

app = FastAPI(
    title="SynthFHIR API",
    description="Generate synthetic FHIR data",
    version="1.0.0"
)

# Request/Response Models
class GenerateRequest(BaseModel):
    prompt: str
    resources: List[str]
    record_count: int = 10
    temperature: float = 0.7

class GenerateResponse(BaseModel):
    success: bool
    data: Dict[str, List[dict]]
    errors: Optional[List[str]] = None

# Initialize generator (singleton)
generator = None

def get_generator():
    global generator
    if generator is None:
        generator = TableGenerator()
    return generator

# Endpoints
@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/resources")
async def list_resources():
    """List available FHIR resources"""
    return {"resources": get_enabled_resources()}

@app.post("/generate", response_model=GenerateResponse)
async def generate_data(request: GenerateRequest):
    """Generate synthetic FHIR data"""
    try:
        gen = get_generator()
        results = gen.generate(
            user_prompt=request.prompt,
            resources=request.resources,
            record_count=request.record_count,
            temperature=request.temperature
        )
        
        data = {}
        errors = []
        
        for result in results:
            if result.success:
                data[result.resource] = result.data
            else:
                errors.append(f"{result.resource}: {result.error}")
        
        return GenerateResponse(
            success=len(errors) == 0,
            data=data,
            errors=errors if errors else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {
        "message": "SynthFHIR API",
        "docs": "/docs",
        "health": "/health"
    }
```

### Step 2: Add Requirements

Add to `requirements.txt`:
```
fastapi>=0.100
uvicorn>=0.23
```

### Step 3: Run FastAPI

```bash
# Development
uvicorn api.main:app --reload --port 8000

# Production
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Step 4: Test the API

```bash
# List resources
curl http://localhost:8000/resources

# Generate data
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Generate 5 diabetic patients in Texas",
    "resources": ["patient"],
    "record_count": 5
  }'
```

---

## Part 4: Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose ports
EXPOSE 8000 8501

# Default: Run FastAPI
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENTERPRISE_BASE_URL=${ENTERPRISE_BASE_URL}
      - ENTERPRISE_CLIENT_ID=${ENTERPRISE_CLIENT_ID}
      - ENTERPRISE_CLIENT_SECRET=${ENTERPRISE_CLIENT_SECRET}
      - EMBEDDING_PROVIDER=auto
    volumes:
      - ./data:/app/data  # Persist ChromaDB
      - ./output:/app/output

  ui:
    build: .
    command: streamlit run app.py --server.port 8501
    ports:
      - "8501:8501"
    environment:
      - ENTERPRISE_BASE_URL=${ENTERPRISE_BASE_URL}
      - ENTERPRISE_CLIENT_ID=${ENTERPRISE_CLIENT_ID}
      - ENTERPRISE_CLIENT_SECRET=${ENTERPRISE_CLIENT_SECRET}
    volumes:
      - ./data:/app/data
      - ./output:/app/output
```

### Run with Docker

```bash
# Build and run
docker-compose up -d

# Access
# API: http://localhost:8000
# UI:  http://localhost:8501
```

---

## Part 5: Enterprise Kubernetes Deployment

### Basic Kubernetes manifests

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: synthfhir-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: synthfhir-api
  template:
    metadata:
      labels:
        app: synthfhir-api
    spec:
      containers:
      - name: api
        image: your-registry/synthfhir:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENTERPRISE_BASE_URL
          valueFrom:
            secretKeyRef:
              name: synthfhir-secrets
              key: enterprise-base-url
        - name: ENTERPRISE_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: synthfhir-secrets
              key: enterprise-client-id
        - name: ENTERPRISE_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: synthfhir-secrets
              key: enterprise-client-secret
---
apiVersion: v1
kind: Service
metadata:
  name: synthfhir-api
spec:
  selector:
    app: synthfhir-api
  ports:
  - port: 80
    targetPort: 8000
```

---

## Summary: Which Deployment to Choose?

| Users | Recommendation | Effort |
|-------|----------------|--------|
| 1-5 | Streamlit only | Low |
| 5-20 | Multiple Streamlit + nginx | Low-Medium |
| 20-100 | FastAPI + Streamlit | Medium |
| 100+ | Kubernetes + FastAPI | High |

**For your enterprise, I recommend:**
1. Start with **Streamlit** for internal testing
2. Add **FastAPI** when you need API access or more users
3. Move to **Docker/Kubernetes** for production
