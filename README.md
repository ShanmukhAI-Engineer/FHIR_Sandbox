# SynthFHIR - Synthetic FHIR Data Generator

🏥 Generate synthetic healthcare data matching your Snowflake DDL structure using Enterprise LLM and RAG.

## Features

- **FHIR R4 Compatible**: Generate Patient, Coverage, Claim, Observation resources
- **DDL-Driven**: Output matches your Snowflake table structure exactly
- **RAG-Enhanced**: Uses your guidelines and documentation for accurate generation
- **PHI Protection**: MD5 hashing for sensitive fields
- **Enterprise LLM**: OAuth2-authenticated enterprise LLM integration
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
# Edit .env with your enterprise credentials
```

**Required:**
```bash
ENTERPRISE_BASE_URL=https://your-enterprise-llm.company.com
ENTERPRISE_CLIENT_ID=your-oauth2-client-id
ENTERPRISE_CLIENT_SECRET=your-oauth2-client-secret
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
│   └── ddl_parser.py         # DDL parsing
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

---

## Enterprise LLM Configuration

### Required Environment Variables

```bash
ENTERPRISE_BASE_URL=https://your-enterprise-llm.company.com
ENTERPRISE_CLIENT_ID=your-oauth2-client-id
ENTERPRISE_CLIENT_SECRET=your-oauth2-client-secret

# Optional (defaults shown)
ENTERPRISE_MODEL=your-model-name
ENTERPRISE_TOKEN_PATH=/v2/oauth2/token
ENTERPRISE_CHAT_PATH=/v2/text/chats
```

### Expected API Endpoints

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
  {"choices": [{"message": {"content": "..."}}]}  # Standard format
  {"message": {"content": "..."}}                 # Direct message
  {"content": "..."}                              # Direct content
```

### Enterprise Embeddings (Optional)

If your enterprise also provides an embedding API:

```bash
EMBEDDING_PROVIDER=enterprise
ENTERPRISE_EMBEDDING_PATH=/openai/v1/embeddings
ENTERPRISE_EMBEDDING_MODEL=text-embedding-ada-002
```

---

## Configuration

### Resource Configuration

Edit `config/resources.py` to:
- Enable/disable resources
- Configure DDL paths
- Set MD5 fields for PHI
- Define relationships

### LLM Settings

Environment variables:
- `ENTERPRISE_BASE_URL` - Your enterprise LLM endpoint
- `ENTERPRISE_CLIENT_ID` - OAuth2 client ID
- `ENTERPRISE_CLIENT_SECRET` - OAuth2 client secret
- `ENTERPRISE_MODEL` - Model name (optional)

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
