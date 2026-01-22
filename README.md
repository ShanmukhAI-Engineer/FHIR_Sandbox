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
│   │   └── horizon_llm.py    # Enterprise LLM template
│   ├── prompt_builder.py     # Prompt construction
│   └── table_generator.py    # Data generation
├── rag/
│   ├── document_loader.py    # Load documents
│   ├── embeddings.py         # Sentence transformers
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

## Swapping LLMs

### Option A: Environment Variable

```bash
set ACTIVE_LLM=horizon
```

### Option B: Change Default

Edit `generator/llm/__init__.py`:
```python
DEFAULT_LLM = "horizon"  # Change from "openai"
```

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
- `ACTIVE_LLM` (openai/horizon)

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
