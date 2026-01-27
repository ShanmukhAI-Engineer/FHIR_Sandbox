# SynthFHIR - Synthetic FHIR Data Generator

🏥 Generate synthetic healthcare data matching your Snowflake DDL structure using LLM and RAG.

## Features

- **FHIR R4 Compatible**: Generate Patient, Coverage, Claim, Observation resources
- **DDL-Driven**: Output matches your Snowflake table structure exactly
- **RAG-Enhanced**: Uses your guidelines and documentation for accurate generation
- **PHI Protection**: MD5 hashing for sensitive fields
- **Pluggable LLM**: Easy swap between OpenAI, Horizon, or custom LLMs
- **Streamlit UI**: User-friendly web interface

## Quick Start

### 1. Clone and Setup

```bash
cd sandboxfhir
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env
# Edit .env with your API keys
```

**Required:**
```
OPENAI_API_KEY=your-openai-api-key
```

### 3. Run the Application

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Project Structure

```
sandboxfhir/
├── app.py                    # Streamlit UI
├── config/
│   ├── settings.py           # Application settings
│   └── resources.py          # Resource configurations
├── generator/
│   ├── llm/                  # LLM implementations
│   │   ├── base_llm.py       # Base interface
│   │   ├── openai_llm.py     # OpenAI implementation
│   │   ├── horizon_llm.py    # Legacy enterprise template
│   │   └── enterprise_llm.py # Enterprise LLM with OAuth2
│   ├── prompt_builder.py     # Prompt construction
│   └── table_generator.py    # Data generation
├── rag/
│   ├── document_loader.py    # Load documents
│   ├── embeddings.py         # Embeddings (local or enterprise)
│   ├── vector_store.py       # ChromaDB wrapper
│   └── retriever.py          # RAG retrieval
├── utils/
│   ├── md5_hasher.py         # PHI hashing
│   ├── data_validator.py     # Validation
│   ├── csv_exporter.py       # CSV export
│   ├── ddl_parser.py         # DDL parsing
│   └── mock_enterprise_gateway.py  # Mock OAuth2 gateway for testing
├── ddl/                      # Your DDL files
├── knowledge/                # Guidelines and docs
├── templates/                # Sample data templates
├── output/                   # Generated CSV files
└── data/                     # ChromaDB storage
```

## Usage

### 1. Add Your DDL Files

Place your Snowflake DDL files in the `ddl/` folder:
- `ddl/patient.sql`
- `ddl/coverage.sql`
- `ddl/claim.sql`
- `ddl/observation.sql`

### 2. Add Guidelines (Optional)

Add SME documentation to `knowledge/` folders:
- `knowledge/global/` - General guidelines
- `knowledge/patient/` - Patient-specific rules
- etc.

### 3. Generate Data

1. Open the Streamlit UI
2. Enter a prompt: "Generate 5 diabetic patients in Texas"
3. Select resources
4. Click Generate
5. Export to CSV

## Swapping LLMs

SynthFHIR supports multiple LLM backends:

| Provider | Use Case | Auth Type |
|----------|----------|-----------|
| `openai` | OpenAI API or compatible endpoints | API Key |
| `horizon` | Legacy enterprise template | API Key |
| `enterprise` | **Enterprise LLM with OAuth2** | OAuth2 Client Credentials |

### Option A: Environment Variable

```bash
# For OpenAI
set ACTIVE_LLM=openai

# For Enterprise LLM (OAuth2)
set ACTIVE_LLM=enterprise
```

### Option B: Change Default

Edit `generator/llm/__init__.py`:
```python
DEFAULT_LLM = "enterprise"  # Change from "openai"
```

---

## Enterprise LLM Setup (OAuth2)

For organizations using internal LLM APIs with OAuth2 authentication:

### 1. Configure Environment Variables

```bash
# Required
ACTIVE_LLM=enterprise
ENTERPRISE_BASE_URL=https://your-enterprise-llm.company.com
ENTERPRISE_CLIENT_ID=your-oauth2-client-id
ENTERPRISE_CLIENT_SECRET=your-oauth2-client-secret

# Optional (defaults shown)
ENTERPRISE_MODEL=your-model-name
ENTERPRISE_TOKEN_PATH=/v2/oauth2/token
ENTERPRISE_CHAT_PATH=/v2/text/chats
```

### 2. Expected API Endpoints

Your enterprise LLM must expose these endpoints:

**OAuth2 Token Endpoint** (`POST /v2/oauth2/token`):
```json
Request (form-urlencoded):
  grant_type=client_credentials
  client_id=xxx
  client_secret=xxx

Response:
  {"access_token": "...", "expires_in": 3600}
```

**Chat Completion Endpoint** (`POST /v2/text/chats`):
```json
Request:
  {"messages": [{"role": "user", "content": "..."}]}

Response (any of these formats):
  {"choices": [{"message": {"content": "..."}}]}  # OpenAI format
  {"message": {"content": "..."}}                 # Direct message
  {"content": "..."}                              # Direct content
```

### 3. Testing with Mock Gateway

For local development/testing without enterprise access:

```bash
# Terminal 1: Start mock gateway
uvicorn utils.mock_enterprise_gateway:app --reload --port 8000

# Terminal 2: Configure and run app
set ACTIVE_LLM=enterprise
set ENTERPRISE_BASE_URL=http://localhost:8000
set ENTERPRISE_CLIENT_ID=test-client
set ENTERPRISE_CLIENT_SECRET=test-secret
streamlit run app.py
```

### 4. Enterprise Embeddings (Optional)

If your enterprise also provides an embedding API:

```bash
EMBEDDING_PROVIDER=enterprise
ENTERPRISE_EMBEDDING_PATH=/openai/v1/embeddings
ENTERPRISE_EMBEDDING_MODEL=text-embedding-ada-002
```

---

### Adding New LLM

1. Create `generator/llm/new_llm.py` implementing `BaseLLM`
2. Add to `PROVIDERS` and `LLM_REGISTRY` in `__init__.py`

## Configuration

### Resource Configuration

Edit `config/resources.py` to:
- Enable/disable resources
- Configure DDL paths
- Set MD5 fields for PHI
- Define relationships

### LLM Settings

Edit `config/settings.py` or use environment variables:
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default: gpt-3.5-turbo)
- `ACTIVE_LLM` (openai/horizon/enterprise)

## Sample Prompts

```
Generate 5 patients with diabetes in Texas
Generate a family of 4 in California with linked coverage
Generate 10 elderly Medicare patients with observations
Generate pediatric patients aged 5-12 with immunization records
```

## License

Internal use only.

## Support

Contact your development team for support.
