"""
Resource Configuration - Define available resources and their settings
"""

from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DDL_DIR = BASE_DIR / "ddl"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
TEMPLATES_DIR = BASE_DIR / "templates"

# Resource Configurations
RESOURCES = {
    "patient": {
        "enabled": True,
        "display_name": "Patient",
        "description": "FHIR Patient resource - demographics and identifiers",
        "ddl_file": str(DDL_DIR / "patient.sql"),
        "knowledge_dir": str(KNOWLEDGE_DIR / "patient"),
        "template_file": str(TEMPLATES_DIR / "patient_sample.json"),
        
        # Columns to exclude from generation (ETL metadata, etc.)
        "exclude_columns": [
            "EDL_LOAD_DTM",
            "EDL_RUN_ID",
            "EDL_SCRTY_LVL_CD",
            "EDL_LOB_CD",
            "EDL_EXTRNL_LOAD_CD",
            "EDL_SOR_CD",
            "RCRD_EXCLSN_CD",
            "SCRTY_LVL_CD",
            "HASH_KEY",
        ],
        
        # Fields to MD5 hash (PHI protection)
        "md5_fields": [
            # "IDENTIFIER[*].value",
            # "NAME[*].family",
            # "NAME[*].given[*]",
            # "TELECOM[*].value",
            # "ADDRESS[*].line[*]",
        ],
        
        # Relationships to other resources
        "relationships": [],
    },
    
    "coverage": {
        "enabled": True,
        "display_name": "Coverage",
        "description": "FHIR Coverage resource - insurance information",
        "ddl_file": str(DDL_DIR / "coverage.sql"),
        "knowledge_dir": str(KNOWLEDGE_DIR / "coverage"),
        "template_file": str(TEMPLATES_DIR / "coverage_sample.json"),
        "exclude_columns": [
            "EDL_LOAD_DTM",
            "EDL_RUN_ID", 
            "EDL_SCRTY_LVL_CD",
            "EDL_LOB_CD",
            "EDL_EXTRNL_LOAD_CD",
            "EDL_SOR_CD",
            "RCRD_EXCLSN_CD",
            "SCRTY_LVL_CD",
            "HASH_KEY",
        ],
        "md5_fields": [
            # "SUBSCRIBER_ID",
        ],
        "relationships": [
            {"column": "BENEFICIARY", "references": "patient.ID"},
        ],
    },
    
    "claim": {
        "enabled": True,
        "display_name": "Claim",
        "description": "FHIR Claim resource - billing and claims data",
        "ddl_file": str(DDL_DIR / "claim.sql"),
        "knowledge_dir": str(KNOWLEDGE_DIR / "claim"),
        "template_file": str(TEMPLATES_DIR / "claim_sample.json"),
        "exclude_columns": [
            "EDL_LOAD_DTM",
            "EDL_RUN_ID",
            "EDL_SCRTY_LVL_CD", 
            "EDL_LOB_CD",
            "EDL_EXTRNL_LOAD_CD",
            "EDL_SOR_CD",
            "RCRD_EXCLSN_CD",
            "SCRTY_LVL_CD",
            "HASH_KEY",
        ],
        "md5_fields": [],
        "relationships": [
            {"column": "PATIENT", "references": "patient.ID"},
            {"column": "INSURANCE_COVERAGE", "references": "coverage.ID"},
        ],
    },
    
    "observation": {
        "enabled": True,
        "display_name": "Observation",
        "description": "FHIR Observation resource - clinical observations and lab results",
        "ddl_file": str(DDL_DIR / "observation.sql"),
        "knowledge_dir": str(KNOWLEDGE_DIR / "observation"),
        "template_file": str(TEMPLATES_DIR / "observation_sample.json"),
        "exclude_columns": [
            "EDL_LOAD_DTM",
            "EDL_RUN_ID",
            "EDL_SCRTY_LVL_CD",
            "EDL_LOB_CD", 
            "EDL_EXTRNL_LOAD_CD",
            "EDL_SOR_CD",
            "RCRD_EXCLSN_CD",
            "SCRTY_LVL_CD",
            "HASH_KEY",
        ],
        "md5_fields": [],
        "relationships": [
            {"column": "SUBJECT", "references": "patient.ID"},
        ],
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
