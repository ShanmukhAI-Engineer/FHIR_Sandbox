"""
Resource Configuration - Define available resources and their settings
"""

from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DDL_DIR = BASE_DIR / "ddl"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
TEMPLATES_DIR = BASE_DIR / "templates"

# Standard columns to exclude (ETL/Platform metadata)
STANDARD_EXCLUDES = [
    "EDL_LOAD_DTM",
    "EDL_RUN_ID",
    "EDL_SCRTY_LVL_CD",
    "EDL_LOB_CD",
    "EDL_EXTRNL_LOAD_CD",
    "EDL_SOR_CD",
    "RCRD_EXCLSN_CD",
    "SCRTY_LVL_CD",
    "HASH_KEY",
]

# Resource Configurations
RESOURCES = {
    "patient": {
        "enabled": True,
        "display_name": "Patient",
        "description": "FHIR Patient resource - demographics and identifiers",
        "ddl_file": str(DDL_DIR / "patient.sql"),
        "knowledge_dir": str(KNOWLEDGE_DIR / "patient"),
        "template_file": str(TEMPLATES_DIR / "patient_golden.json"),
        "exclude_columns": STANDARD_EXCLUDES,
        "md5_fields": [],
        "relationships": [],
        "smart_ratio": 1.0,
    },
    
    "coverage": {
        "enabled": True,
        "display_name": "Coverage",
        "description": "FHIR Coverage resource - insurance information",
        "ddl_file": str(DDL_DIR / "coverage.sql"),
        "knowledge_dir": str(KNOWLEDGE_DIR / "coverage"),
        "template_file": str(TEMPLATES_DIR / "coverage_golden.json"),
        "exclude_columns": STANDARD_EXCLUDES,
        "md5_fields": [],
        "relationships": [
            {"column": "BENEFICIARY", "references": "patient.ID"},
        ],
        "smart_ratio": 1.0,
    },
    
    "claim": {
        "enabled": True,
        "display_name": "Claim",
        "description": "FHIR Claim resource - billing and claims data",
        "ddl_file": str(DDL_DIR / "claim.sql"),
        "knowledge_dir": str(KNOWLEDGE_DIR / "claim"),
        "template_file": str(TEMPLATES_DIR / "claim_golden.json"),
        "exclude_columns": STANDARD_EXCLUDES,
        "md5_fields": [],
        "relationships": [
            {"column": "PATIENT", "references": "patient.ID"},
            {"column": "INSURANCE_COVERAGE", "references": "coverage.ID"},
        ],
        "smart_ratio": 5.0,
    },
    
    "observation": {
        "enabled": True,
        "display_name": "Observation",
        "description": "FHIR Observation resource - clinical observations and lab results",
        "ddl_file": str(DDL_DIR / "observation.sql"),
        "knowledge_dir": str(KNOWLEDGE_DIR / "observation"),
        "template_file": str(TEMPLATES_DIR / "observation_golden.json"),
        "exclude_columns": STANDARD_EXCLUDES,
        "md5_fields": [],
        "relationships": [
            {"column": "SUBJECT", "references": "patient.ID"},
            {"column": "SUBJECT_REF", "references": "patient.ID"},
        ],
        "smart_ratio": 10.0,
    },
    
    "practitioner": {
        "enabled": True,
        "display_name": "Practitioner",
        "description": "FHIR Practitioner resource - healthcare professionals",
        "ddl_file": str(DDL_DIR / "practitioner.sql"),
        "knowledge_dir": str(KNOWLEDGE_DIR / "practitioner"),
        "template_file": str(TEMPLATES_DIR / "practitioner_golden.json"),
        "exclude_columns": STANDARD_EXCLUDES,
        "md5_fields": [],
        "relationships": [],
        "smart_ratio": 1.0,
    },
    
    "location": {
        "enabled": True,
        "display_name": "Location",
        "description": "FHIR Location resource - physical locations",
        "ddl_file": str(DDL_DIR / "location.sql"),
        "knowledge_dir": str(KNOWLEDGE_DIR / "location"),
        "template_file": str(TEMPLATES_DIR / "location_golden.json"),
        "exclude_columns": STANDARD_EXCLUDES,
        "md5_fields": [],
        "relationships": [
            {"column": "MANAGING_ORGANIZATION", "references": "organization.ID"},
        ],
        "smart_ratio": 1.0,
    },
    
    "organization": {
        "enabled": True,
        "display_name": "Organization",
        "description": "FHIR Organization resource - healthcare organizations",
        "ddl_file": str(DDL_DIR / "organization.sql"),
        "knowledge_dir": str(KNOWLEDGE_DIR / "organization"),
        "template_file": str(TEMPLATES_DIR / "organization_golden.json"),
        "exclude_columns": STANDARD_EXCLUDES,
        "md5_fields": [],
        "relationships": [],
        "smart_ratio": 1.0,
    },
    
    "encounter": {
        "enabled": True,
        "display_name": "Encounter",
        "description": "FHIR Encounter resource - clinical interactions",
        "ddl_file": str(DDL_DIR / "encounter.sql"),
        "knowledge_dir": str(KNOWLEDGE_DIR / "encounter"),
        "template_file": str(TEMPLATES_DIR / "encounter_golden.json"),
        "exclude_columns": STANDARD_EXCLUDES,
        "md5_fields": [],
        "relationships": [
            {"column": "SUBJECT", "references": "patient.ID"},
            {"column": "SERVICE_PROVIDER", "references": "organization.ID"},
        ],
        "smart_ratio": 3.0,
    },
    
    "condition": {
        "enabled": True,
        "display_name": "Condition",
        "description": "FHIR Condition resource - diagnoses and health concerns",
        "ddl_file": str(DDL_DIR / "condition.sql"),
        "knowledge_dir": str(KNOWLEDGE_DIR / "condition"),
        "template_file": str(TEMPLATES_DIR / "condition_golden.json"),
        "exclude_columns": STANDARD_EXCLUDES,
        "md5_fields": [],
        "relationships": [
            {"column": "SUBJECT", "references": "patient.ID"},
            {"column": "ENCOUNTER", "references": "encounter.ID"},
        ],
        "smart_ratio": 2.0,
    },
    
    "medication_request": {
        "enabled": True,
        "display_name": "Medication Request",
        "description": "FHIR MedicationRequest resource - prescriptions",
        "ddl_file": str(DDL_DIR / "medication_request.sql"),
        "knowledge_dir": str(KNOWLEDGE_DIR / "medication_request"),
        "template_file": str(TEMPLATES_DIR / "medication_request_golden.json"),
        "exclude_columns": STANDARD_EXCLUDES,
        "md5_fields": [],
        "relationships": [
            {
                "column": "SUBJECT", 
                "references": "patient.ID",
                "map_attributes": {
                    "patient.MCID": "SUBJECT_MCID",
                    "patient.FIRST_NAME": "SUBJECT_FIRST_NAME",
                    "patient.LAST_NAME": "SUBJECT_LAST_NAME"
                }
            },
            {
                "column": "ENCOUNTER", 
                "references": "encounter.ID"
            },
            {
                "column": "REQUESTER", 
                "references": "practitioner.ID",
                "map_attributes": {
                    "practitioner.NPI": "REQUESTER_NPI",
                    "practitioner.NAME_TEXT": "REQUESTER_NAME"
                }
            },
        ],
        "smart_ratio": 2.0,
    },
}


def get_enabled_resources():
    """Get list of enabled resource names"""
    return [name for name, config in RESOURCES.items() if config.get("enabled", False)]


def get_resource_config(resource_name: str):
    """Get configuration for a specific resource"""
    return RESOURCES.get(resource_name)


def get_resource_display_names():
    """Get dict mapping resource name to display name"""
    return {
        name: config["display_name"] 
        for name, config in RESOURCES.items() 
        if config.get("enabled", False)
    }
