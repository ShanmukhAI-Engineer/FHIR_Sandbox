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

## 2. Implementing Referential Integrity

### How it Works
The system uses a **Stateful Relationship Context**. When generating multiple resources (e.g., Patient then Claim):
1. **ID Tracking**: `TableGenerator` captures the IDs of the first resource (e.g., Patient).
2. **Context Injection**: These IDs are injected into the prompt of the second resource (e.g., Claim) as a list of available references.
3. **LLM Instruction**: The `PromptBuilder` tells the LLM: *"Use these IDs for the PATIENT field."*

### Best Practices for Linking
- **Order Matters**: Always list the "Parent" resource (e.g., Patient) before the "Child" resource (e.g., Claim) in your generation request.
- **Reference Format**: In your Golden Template, show the format clearly: `"REFERENCE": "Patient/3f987ee0..."`.
- **Relationship Meta**: Keep the `relationships` list in `config/resources.py` accurate for future automated validation features.
