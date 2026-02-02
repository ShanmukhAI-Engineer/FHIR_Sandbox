# Developer Guide: Adding Resources & Referential Integrity

This guide explains how to extend SynthFHIR with new resources and ensure they maintain referential integrity with existing data.

## 1. Adding a New Resource

### Step A: Add DDL Schema
Create a new `.sql` file in the `ddl/` directory. Use standard Snowflake syntax.
- **File**: `ddl/my_new_resource.sql`
- **Rule**: Ensure an `ID` column exists (32-character string).

### Step B: Update the Template Generator
The LLM uses "Golden Templates" to understand the data structure. You should update `utils/template_generator.py` to support the new resource.
1. Add a `generate_mock_my_new_resource()` function.
2. Register it in the `generators` dictionary at the bottom of the file.
3. Run `python utils/template_generator.py` to create `templates/my_new_resource_golden.json`.

### Step C: Register in Configuration
Update `config/resources.py` to enable the resource.
```python
"my_new_resource": {
    "enabled": True,
    "display_name": "My New Resource",
    "ddl_file": str(DDL_DIR / "my_new_resource.sql"),
    "template_file": str(TEMPLATES_DIR / "my_new_resource_golden.json"),
    "exclude_columns": STANDARD_EXCLUDES,
    "relationships": [
        {"column": "PATIENT_REF", "references": "patient.ID"}
    ],
}
```

### Step D: Reindex RAG
Open the application and click **"🔄 Reindex Documents"** in the sidebar. This ensures the LLM can find your new DDL schema during generation.

---

## 2. Implementing Referential Integrity (Code-Enforced)

The system now enforces referential integrity **programmatically** after the LLM generates data. This ensures 100% consistency even if the LLM hallucinates or makes a mistake.

### A. Configuration (`config/resources.py`)
You define relationships in the `relationships` list. You can now also map specific attributes from the parent to the child using `map_attributes`.

```python
"relationships": [
    {
        "column": "SUBJECT",           # Column in the Child table (e.g., Claim)
        "references": "patient.ID",    # Reference to Parent table (e.g., Patient)
        
        # OPTIONAL: Force Child columns to match Parent values exactly
        "map_attributes": {
            "patient.MCID": "SUBJECT_MCID",        # Copies Patient.MCID -> Claim.SUBJECT_MCID
            "patient.FIRST_NAME": "PATIENT_NAME",  # Copies Patient.FIRST_NAME -> Claim.PATIENT_NAME
        }
    }
]
```

### B. Automatic Enforcement Logic
1.  **ID Validation**: The system checks if the generated Foreign Key (e.g., `SUBJECT`) exists in the available Parent records.
2.  **Auto-Correction**: If the ID is invalid or missing, the system **automatically picks a valid Parent** from the context and overwrites the invalid ID.
3.  **Attribute Propagation**: If `map_attributes` is defined, the system copies the values from the selected Parent record to the Child record, overwriting whatever the LLM generated.

```

### C. Guide: Adding Custom Relationships & Mappings

If you need to link a new resource or add a custom field mapping (e.g., copying a "Group ID" from Coverage to Claim):

1.  **Open** `config/resources.py`.
2.  **Locate** the resource definition (e.g., `"claim"`).
3.  **Edit** the `relationships` list:
    *   **`column`**: The name of the column in your CURRENT resource (the Child).
    *   **`references`**: The `resource_name.column_name` of the PARENT resource.
    *   **`map_attributes`** (Optional): A dictionary where:
        *   Key = `parent_resource.column_name` (Source)
        *   Value = `child_column_name` (Target)

**Example Scenario**:
You want to make sure that when a `Claim` is generated, it inherits the `GROUP_ID` from the `Coverage` resource.

```python
# In config/resources.py > "claim"
"relationships": [
    # ... existing links ...
    {
        "column": "INSURANCE_COVERAGE",  # Claim.INSURANCE_COVERAGE
        "references": "coverage.ID",     # Links to Coverage.ID
        "map_attributes": {
            "coverage.GROUP_ID": "GROUP_NUMBER",  # Copy Coverage.GROUP_ID -> Claim.GROUP_NUMBER
            "coverage.PAYOR_NAME": "PAYOR",       # Copy Coverage.PAYOR_NAME -> Claim.PAYOR
        }
    }
]
```

**Note**: The source column (e.g., `coverage.GROUP_ID`) MUST exist in the generated Parent data for this to work.

---

## 3. Scalability & Dependencies

### Automatic Dependency Sorting
You do **not** need to worry about the order in which you select resources.
The system uses a **Topological Sort** to automatically determine the correct execution order based on the `relationships` defined in your config.

- **Example**: If you select `["claim", "patient"]`, the system detects that `Claim` depends on `Patient` and will automatically generate `Patient` first, then `Claim`.

### Smart Context Filtering
To support generating 40+ resources without exceeding token limits, the system uses **Context Filtering**.
- When generating a specific resource (e.g., `Claim`), the LLM *only* sees data from its direct parents (e.g., `Patient`, `Coverage`).
- It does *not* see unrelated data (e.g., `Practitioner`, `Location`), keeping the prompt clean and efficient.
---

## 4. Troubleshooting Missing Data

If specific columns are missing from your output CSVs, follow this checklist to identify and fix the issue.

### A. Check Exclusions (`config/resources.py`)
Ensure the column is not listed in `STANDARD_EXCLUDES` or the resource's `exclude_columns` list. The generator ignores these columns by design.

### B. Update the Golden Template (`templates/*.json`)
The LLM heavily relies on the "Golden Templates" for its output structure. 
- **Action**: Add the missing column to your `*_golden.json` file with a realistic sample value. This is the most reliable way to enforce population.

### C. Add Knowledge Rules (`knowledge/`)
If a column requires complex logic or is frequently skipped, add a specific instruction in the resource's knowledge folder (e.g., `knowledge/claim/rules.txt`).
- **Example**: "Every claim record MUST have a valid PROVIDER_ID from the DDL."
- **Action**: Always click **"🔄 Reindex Documents"** after adding new rules.

### D. Verify DDL Synced
Ensure the column exists in the `.sql` file in the `ddl/` folder and that you have reindexed the documents.

---

## 5. Managing Business Rules

SynthFHIR uses a **Multi-Layered Rule System** powered by RAG. This allows you to enforce clinical and business logic without changing code.

### A. Resource-Specific Rules
Use these for logic that only applies to one resource (e.g., "Claims must have a total > $0").
- **Action**: Place a `.txt` or `.md` file in `knowledge/[resource]/`.
- **Example**: `knowledge/claim/financial_rules.txt`

### B. Global Rules
Use these for logic that applies to EVERY record (e.g., "No field should contain 'NULL' as a string").
- **Action**: Place a file in `knowledge/global/`.
- **Note**: The system automatically searches the `global` folder for every generation request.

### C. Prompt-Level Rules
Use these for ad-hoc requests (e.g., "Generate only 2024 records").
- **Action**: Type these directly into the **Prompt** text area in the UI.

### D. Hard-Coded Rules (Config)
For structural rules like relationships or hashing:
- **Action**: Update the `relationships` or `md5_fields` in `config/resources.py`.

> [!IMPORTANT]
> **Reindexing is Required**: Whenever you add or change a file in the `knowledge/` or `ddl/` folders, you **must** click the **"🔄 Reindex Documents"** button in the Streamlit sidebar to update the "brain" of the generator.
