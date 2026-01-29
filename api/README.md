# FastAPI Backend for SynthFHIR

FastAPI REST API for synthetic FHIR data generation.

## Running the API

```bash
# From repo root
uvicorn api.main:app --reload --port 8000
```

## API Documentation

Once running, visit:
- **Interactive Docs**: http://localhost:8000/docs  
- **Health Check**: http://localhost:8000/api/health

## Endpoints

- `GET /api/health` - Health check
- `GET /api/config` - Get app configuration
- `POST /api/generate` - Generate synthetic data
- `GET /api/knowledge/status` - Knowledge base status
- `POST /api/knowledge/index` - Index resource
- `POST /api/knowledge/upload` - Upload file
- `GET /api/llm/status` - LLM configuration status
- `POST /api/export/{resource}` - Export to CSV
- `GET /api/download/{filename}` - Download CSV file
