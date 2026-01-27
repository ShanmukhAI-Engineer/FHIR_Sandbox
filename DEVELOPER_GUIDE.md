# SynthFHIR Developer Guide

## Quick Reference - Where to Make Changes

| What You Want to Change | File to Edit |
|------------------------|--------------|
| **System Prompt** (LLM Instructions) | `generator/prompt_builder.py` → `SYSTEM_PROMPT` |
| **DDL (Table Structure)** | `ddl/*.sql` files |
| **Sample Output Format** | `templates/*_golden.json` files |
| **Resource Settings** (which columns to exclude, relationships) | `config/resources.py` |
| **Enterprise LLM Settings** | `.env` file |
| **UI Layout** | `app.py` |
| **Guidelines/Knowledge Base** | `knowledge/` folders |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        app.py (Streamlit UI)                    │
│                                                                 │
│  User Input → select resources → generate → export CSV          │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    generator/table_generator.py                 │
│                                                                 │
│  TableGenerator: Orchestrates the entire generation process    │
│  1. Loads DDL from ddl/*.sql                                   │
│  2. Retrieves guidelines from knowledge base (RAG)             │
│  3. Builds prompt using PromptBuilder                          │
│  4. Calls Enterprise LLM                                       │
│  5. Parses JSON response                                       │
└─────────────────────┬───────────────────────────────────────────┘
                      │
          ┌──────────┴──────────┐
          ▼                     ▼
┌──────────────────┐  ┌──────────────────────────┐
│ prompt_builder.py │  │ generator/llm/           │
│                   │  │                          │
│ PromptBuilder:    │  │ enterprise_llm.py:       │
│ - SYSTEM_PROMPT   │  │ - OAuth2 authentication  │
│ - build_prompt()  │  │ - send request to API    │
└──────────────────┘  └──────────────────────────┘
```

---

## 1. Changing the System Prompt

The system prompt tells the LLM HOW to generate data. It's the most important instruction.

### File: `generator/prompt_builder.py`

```python
class PromptBuilder:
    SYSTEM_PROMPT = """You are a synthetic healthcare data generator...
    
CRITICAL RULES:
1. Output MUST be valid JSON array
2. Each object MUST contain ALL specified columns
...
"""
```

### How to Modify:

1. Open `generator/prompt_builder.py`
2. Find the `SYSTEM_PROMPT` class variable (around line 14)
3. Edit the text inside the triple quotes
4. Save and restart the app

### Example Changes:

```python
# Add a new rule:
SYSTEM_PROMPT = """You are a synthetic healthcare data generator...

CRITICAL RULES:
1. Output MUST be valid JSON array
...
8. All dates must be in YYYY-MM-DD format  # NEW RULE
9. Never use placeholder values like "TBD" or "N/A"  # NEW RULE
"""
```

---

## 2. Changing DDL (Table Structure)

DDL files define what columns the LLM should generate.

### Location: `ddl/` folder

```
ddl/
├── patient.sql      # Patient table structure
├── coverage.sql     # Coverage table structure  
├── claim.sql        # Claim table structure
└── observation.sql  # Observation table structure
```

### How to Modify:

1. Open the relevant `.sql` file (e.g., `ddl/patient.sql`)
2. Add/remove/modify columns
3. Save the file
4. The app will use the new structure on next generation

### Example DDL:

```sql
CREATE TABLE PATIENT (
    ID VARCHAR(32) NOT NULL,
    ACTIVE BOOLEAN,
    NAME ARRAY,
    GENDER VARCHAR(10),
    BIRTH_DATE DATE,
    -- Add new column:
    MARITAL_STATUS VARCHAR(20),
    -- ...more columns
);
```

### Important:
- After changing DDL, also update the corresponding template in `templates/`
- Update `config/resources.py` if you need to exclude new metadata columns

---

## 3. Changing Sample Templates (Golden Templates)

Templates show the LLM the EXACT format you expect for output.

### Location: `templates/` folder

```
templates/
├── patient_golden.json
├── coverage_golden.json
├── claim_golden.json
└── observation_golden.json
```

### How to Modify:

1. Open the relevant `_golden.json` file
2. Update the sample data structure
3. Save the file

### Example:

```json
[
  {
    "ID": "3f987ee038494bddb2433e7f0113948e",
    "ACTIVE": true,
    "NAME": [
      {
        "use": "official",
        "family": "Smith",
        "given": ["John", "Michael"]
      }
    ],
    // Add new field to match new DDL:
    "MARITAL_STATUS": "married"
  }
]
```

---

## 4. Changing Resource Configuration

### File: `config/resources.py`

This file controls:
- Which resources are enabled
- What columns to exclude (ETL metadata)
- Which fields to hash (PHI protection)
- Relationships between resources

### Example - Add a new resource:

```python
RESOURCES = {
    "patient": {...},
    "coverage": {...},
    
    # Add new resource:
    "medication": {
        "enabled": True,
        "display_name": "Medication",
        "description": "FHIR Medication resource",
        "ddl_file": str(DDL_DIR / "medication.sql"),
        "knowledge_dir": str(KNOWLEDGE_DIR / "medication"),
        "template_file": str(TEMPLATES_DIR / "medication_golden.json"),
        "exclude_columns": ["EDL_LOAD_DTM", "HASH_KEY"],
        "md5_fields": [],
        "relationships": [
            {"column": "SUBJECT", "references": "patient.ID"},
        ],
    },
}
```

### Example - Exclude new columns:

```python
"patient": {
    "exclude_columns": [
        "EDL_LOAD_DTM",
        "EDL_RUN_ID",
        "NEW_METADATA_COLUMN",  # Add here
    ],
}
```

---

## 5. Changing Enterprise LLM Settings

### File: `.env`

```bash
# Enterprise LLM endpoint
ENTERPRISE_BASE_URL=https://your-enterprise-llm.company.com
ENTERPRISE_CLIENT_ID=your-client-id
ENTERPRISE_CLIENT_SECRET=your-client-secret

# Optional
ENTERPRISE_MODEL=your-model-name
ENTERPRISE_TOKEN_PATH=/v2/oauth2/token
ENTERPRISE_CHAT_PATH=/v2/text/chats
```

---

## 6. Adding Guidelines/Knowledge

The RAG system uses guidelines from the `knowledge/` folder.

### Location: `knowledge/` folder

```
knowledge/
├── global/           # Guidelines for all resources
│   └── general.md
├── patient/          # Patient-specific guidelines
└── claim/            # Claim-specific guidelines
```

### How to Add Guidelines:

1. Create a markdown or text file in the appropriate folder
2. Write your guidelines in plain text
3. Run "Reindex Documents" from the Settings page in the app

### Example: `knowledge/patient/demographics.md`

```markdown
# Patient Demographics Guidelines

## Name Generation
- Use realistic American names
- Include middle names for 60% of patients
- Use proper capitalization

## Address Generation
- Use real US city/state combinations
- ZIP codes must match the state
```

---

## Class Reference

### Main Classes

| Class | File | Purpose |
|-------|------|---------|
| `TableGenerator` | `generator/table_generator.py` | Main orchestrator - calls LLM, parses response |
| `PromptBuilder` | `generator/prompt_builder.py` | Constructs system + user prompts |
| `EnterpriseLLM` | `generator/llm/enterprise_llm.py` | OAuth2 + API calls to enterprise LLM |
| `Retriever` | `rag/retriever.py` | Fetches relevant guidelines from vector store |

### Data Flow

```
User Request
    ↓
TableGenerator.generate()
    ↓
PromptBuilder.build_prompt() → System Prompt + User Prompt
    ↓
Retriever.retrieve() → Guidelines Context
    ↓
EnterpriseLLM.generate() → Call API
    ↓
TableGenerator._parse_response() → JSON Array
    ↓
CSV Export
```

---

## Common Tasks

### Task: Change how IDs are generated

**File:** `generator/prompt_builder.py`  
**Line:** System prompt, rule #7

```python
SYSTEM_PROMPT = """...
7. All IDs MUST be alphanumeric strings exactly 32 characters long...
"""
```

### Task: Add a new column to Patient

1. Edit `ddl/patient.sql` - add the column
2. Edit `templates/patient_golden.json` - add sample value
3. (Optional) Edit `config/resources.py` - if it's metadata to exclude

### Task: Change temperature or token limits

**File:** `generator/table_generator.py`  
**Method:** `generate()` parameters

```python
def generate(
    self,
    ...
    temperature: float = 0.7,  # Change this default
    max_tokens: int = 4000     # Change this default
)
```

### Task: Add new quick input option

**File:** `generator/prompt_builder.py`  
**Method:** `_format_quick_inputs()`

```python
def _format_quick_inputs(self, quick_inputs: Dict) -> str:
    # Add handling for new input type:
    if quick_inputs.get("blood_type"):
        constraints.append(f"- Blood type: {quick_inputs['blood_type']}")
```

---

## Testing Changes Locally

```bash
# 1. Make your changes to the files

# 2. Restart the Streamlit app
streamlit run app.py

# 3. Test with a simple prompt
#    "Generate 2 patients in Texas"

# 4. Check the output matches your expectations
```

---

## Git Workflow for Changes

```bash
# 1. Create a feature branch
git checkout -b feature/update-patient-ddl

# 2. Make your changes
# ... edit files ...

# 3. Test locally

# 4. Commit
git add .
git commit -m "feat: add marital_status column to patient"

# 5. Push
git push origin feature/update-patient-ddl
```
