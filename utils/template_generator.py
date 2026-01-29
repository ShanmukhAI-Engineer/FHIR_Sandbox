"""
Template Generator
Uses Faker to create high-fidelity 'Golden Templates' for LLM prompts.
"""

import json
import random
import string
import os
from uuid import uuid4
from typing import Dict, Any
from pathlib import Path
from faker import Faker

# Initialize Faker
fake = Faker()
Faker.seed(42)  # For reproducibility during testing

def generate_clean_id():
    """Generates a UUID4 string without hyphens."""
    return str(uuid4()).replace("-", "")

def generate_custom_string():
    """Generates a string like 'X68KNSHZY' with an optional '30' suffix."""
    alphanumeric_chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(alphanumeric_chars, k=8))
    has_suffix = random.choice([True, False])
    suffix = "30" if has_suffix else ""
    return f"X{random_part}{suffix}"

def generate_mock_patient() -> Dict[str, Any]:
    """Generate a high-fidelity patient record matching Snowflake DDL structure"""
    
    gender = random.choice(['male', 'female', 'other', 'unknown'])
    is_female = gender == 'female'
    first_name = fake.first_name_female() if is_female else fake.first_name_male()
    last_name = fake.last_name()
    birth_date = fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat()
    
    identifiers = [
        {
            "system": "https://genhealthey.com/MemberID",
            "type": {"coding": [{"code": "MB", "system": "http://terminology.hl7.org/CodeSystem/v2-0203"}]},
            "use": "official",
            "value": generate_custom_string()
        }
    ]
    
    patient = {
        "SRC_TYPE": "FHIR",
        "ID": generate_clean_id(),
        "MCID": fake.random_number(digits=9),
        "META": {"versionId": "1", "lastUpdated": "2023-01-01T12:00:00Z"},
        "ACTIVE": "true",
        "GENDER": gender,
        "BIRTHDATE": birth_date,
        "DECEASED": None,
        "NAME": [{"use": "official", "family": last_name, "given": [first_name]}],
        "TELECOM": [{"system": "phone", "value": fake.phone_number(), "use": "home"}],
        "ADDRESS": [{"use": "home", "line": [fake.street_address()], "city": fake.city(), "state": fake.state_abbr(), "postalCode": fake.zipcode(), "country": "USA"}],
        "MARITAL_STATUS": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus", "code": "M", "display": "Married"}]},
        "COMMUNICATION": [{"language": {"coding": [{"code": "en", "display": "English"}]}}],
        "MULTIPLE_BIRTH_INDEX": None,
        "PCP": {"reference": f"Practitioner/{generate_clean_id()}", "display": f"Dr. {fake.last_name()}"},
        "MANAGING_ORG": {"reference": "Organization/1"},
        "LINK": [],
        "EXTENSIONS": [],
        "IDENTIFIER": identifiers,
        "PHOTO": [],
        "CONTACT": []
    }
    return patient

def generate_mock_coverage() -> Dict[str, Any]:
    """Generate a high-fidelity coverage record matching FHIR_COVERAGE_RESOURCE_STG"""
    patient_id = generate_clean_id()
    
    coverage = {
        "ID": generate_clean_id()[:32],
        "MCID": fake.random_number(digits=9),
        "STATUS": "active",
        "SUBSCRIBERID": generate_custom_string()[:15],
        "DEPENDENT": "0",
        "SUBSCRIBER_SYS": "https://genhealthey.com/MemberID",
        "POLICY_HOLDER": "Y",
        "INSURER_NETWORK": "P",
        "SUBROGATION": "N",
        "CONTRACT": "N",
        "COSTTOBENEFICIARY": "Y",
        "BENEFICIARY": {"reference": f"Patient/{patient_id}"},
        "SUBSCRIBER": {"reference": f"Patient/{patient_id}"},
        "PERIOD": {"start": "2023-01-01", "end": "2023-12-31"},
        "META": {"versionId": "1", "lastUpdated": "2023-01-01T12:00:00Z"},
        "EXTENSIONS": [],
        "CONTAINED": [],
        "CLASS": [{"type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/coverage-class", "code": "group"}]}, "value": "GP1234"}],
        "RELATIONSHIP": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/subscriber-relationship", "code": "self"}]},
        "PAYOR": [{"reference": "Organization/2", "display": "Blue Cross Blue Shield"}],
        "IDENTIFIER": [],
        "TYPE": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "EXTMEVM"}]},
        "HASH_KEY": "".join(random.choices(string.hexdigits, k=64)).lower()
    }
    return coverage

def generate_mock_claim() -> Dict[str, Any]:
    """Generate a high-fidelity claim record matching FHIR_CLAIM_RESOURCE_STG"""
    patient_id = generate_clean_id()
    
    claim = {
        "STATUS": "active",
        "ID": generate_clean_id(),
        "MCID": fake.random_number(digits=9),
        "META": {"versionId": "1", "lastUpdated": "2023-05-05T10:00:00Z"},
        "IDENTIFIER": [],
        "TYPE": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/claim-type", "code": "institutional"}]},
        "SUBTYPE": [],
        "USE": "claim",
        "PATIENT": {"reference": f"Patient/{patient_id}"},
        "PROVIDER": {"reference": "Organization/3", "display": "Mayo Clinic"},
        "CREATED_DATE_TIME": "2023-05-05T10:00:00Z",
        "BILLABLE_PERIOD": {"start": "2023-05-01", "end": "2023-05-01"},
        "FUNDS_RESERVE": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/fundsreserve", "code": "provider"}]},
        "INSURANCE": [{"sequence": 1, "focal": True, "coverage": {"reference": "Coverage/1"}}],
        "RELATED": [],
        "INSURER": {"reference": "Organization/2"},
        "ENTERER": {"reference": "Practitioner/1"},
        "PRESCRIPTION": None,
        "ORIGINAL_PRESCRIPTION": None,
        "PAYEE": {"type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/payeetype", "code": "provider"}]}},
        "REFERRAL": None,
        "FACILITY": {"reference": "Location/1"},
        "CARE_TEAM": [],
        "DIAGNOSIS": [{"sequence": 1, "diagnosisCodeableConcept": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "E11.9"}]}}],
        "PROCEDURE": [],
        "ACCIDENT": None,
        "SUPPORTING_INFO": [],
        "ITEM": [{"sequence": 1, "productOrService": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/ex-USCLS", "code": "1200"}]}}],
        "PRIORITY": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/processpriority", "code": "normal"}]},
        "EXTENSIONS": [],
        "TOTAL": {"value": 150.0, "currency": "USD"},
        "CONTAINED": [],
        "HASH_KEY": "".join(random.choices(string.hexdigits, k=64)).lower()
    }
    return claim

def generate_mock_observation() -> Dict[str, Any]:
    """Generate a high-fidelity observation record matching FHIR_OBSERVATION_RESOURCE_STG"""
    patient_id = generate_clean_id()
    
    observation = {
        "ID": generate_clean_id(),
        "MCID": str(fake.random_number(digits=9)),
        "META": {"versionId": "1"},
        "IDENTIFIER": {},
        "BASED_ON": [],
        "PART_OF": {},
        "STATUS": "final",
        "CATEGORY": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
        "CODE": {"coding": [{"system": "http://loinc.org", "code": "85354-9"}]},
        "SUBJECT_REF": {"reference": f"Patient/{patient_id}"},
        "FOCUS": {},
        "ENCOUNTER": {"reference": "Encounter/1"},
        "EFFECTIVE": {"start": "2023-06-01T10:30:00Z", "end": "2023-06-01T10:30:00Z"},
        "ISSUED": "2023-06-01T10:35:00Z",
        "PERFORMER": [{"reference": "Practitioner/1"}],
        "OBS_VAL": {"valueQuantity": {"value": 120, "unit": "mmHg"}},
        "OBS_VAL_QTY_CD": "mm[Hg]",
        "INTERPRETATION": [],
        "NOTE": [],
        "BODY_SITE": {},
        "METHOD": {},
        "SPECIMEN": {},
        "DEVICE": {},
        "REF_RANGE": [],
        "HAS_MBR": {},
        "DERIVED_FROM": {},
        "COMPONENT": [],
        "EXTENSIONS": [],
        "DATA_ABSNT_RSN": {},
        "STATUS_EXTENSION": {},
        "HASH_KEY": "".join(random.choices(string.hexdigits, k=64)).lower()
    }
    return observation

def generate_mock_encounter() -> Dict[str, Any]:
    """Generate a high-fidelity encounter record"""
    patient_id = generate_clean_id()
    return {
        "ID": generate_clean_id(),
        "STATUS": "finished",
        "CLASS": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB", "display": "ambulatory"},
        "TYPE": [{"coding": [{"system": "http://snomed.info/sct", "code": "185345009", "display": "Encounter for symptom"}]}],
        "SUBJECT": {"reference": f"Patient/{patient_id}"},
        "PERIOD": {"start": "2023-10-01T10:00:00Z", "end": "2023-10-01T10:30:00Z"},
        "REASON_CODE": [{"coding": [{"system": "http://snomed.info/sct", "code": "386661002", "display": "Fever"}]}],
        "SERVICE_PROVIDER": {"reference": "Organization/1"},
        "META": {"versionId": "1"},
        "IDENTIFIER": []
    }

def generate_mock_condition() -> Dict[str, Any]:
    """Generate a high-fidelity condition record"""
    patient_id = generate_clean_id()
    return {
        "ID": generate_clean_id(),
        "CLINICAL_STATUS": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
        "VERIFICATION_STATUS": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]},
        "CATEGORY": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-category", "code": "encounter-diagnosis"}]}],
        "CODE": {"coding": [{"system": "http://snomed.info/sct", "code": "386661002", "display": "Fever"}]},
        "SUBJECT": {"reference": f"Patient/{patient_id}"},
        "ENCOUNTER": {"reference": f"Encounter/{generate_clean_id()}"},
        "RECORDED_DATE": "2023-10-01",
        "META": {"versionId": "1"},
        "IDENTIFIER": []
    }

def generate_mock_medication_request() -> Dict[str, Any]:
    """Generate a high-fidelity medication request record"""
    patient_id = generate_clean_id()
    return {
        "ID": generate_clean_id(),
        "STATUS": "active",
        "INTENT": "order",
        "MEDICATION": {"concept": {"coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "582400", "display": "Acetaminophen 500 MG Oral Tablet"}]}},
        "SUBJECT": {"reference": f"Patient/{patient_id}"},
        "ENCOUNTER": {"reference": f"Encounter/{generate_clean_id()}"},
        "AUTHORED_ON": "2023-10-01T10:30:00Z",
        "REQUESTER": {"reference": f"Practitioner/{generate_clean_id()}"},
        "DOSAGE_INSTRUCTION": [{"text": "Take 1 tablet every 4-6 hours as needed for fever"}],
        "META": {"versionId": "1"},
        "IDENTIFIER": []
    }

def generate_mock_organization() -> Dict[str, Any]:
    """Generate a high-fidelity organization record"""
    return {
        "ID": generate_clean_id(),
        "ACTIVE": "true",
        "NAME": fake.company(),
        "TELECOM": [{"system": "phone", "value": fake.phone_number(), "use": "work"}],
        "ADDRESS": [{"line": [fake.street_address()], "city": fake.city(), "state": fake.state_abbr(), "postalCode": fake.zipcode(), "country": "USA"}],
        "META": {"versionId": "1"},
        "IDENTIFIER": []
    }

def generate_mock_location() -> Dict[str, Any]:
    """Generate a high-fidelity location record"""
    return {
        "ID": generate_clean_id(),
        "STATUS": "active",
        "NAME": f"{fake.city()} Clinic",
        "MODE": "instance",
        "ADDRESS": {"line": [fake.street_address()], "city": fake.city(), "state": fake.state_abbr(), "postalCode": fake.zipcode(), "country": "USA"},
        "MANAGING_ORGANIZATION": {"reference": f"Organization/{generate_clean_id()}"},
        "META": {"versionId": "1"},
        "IDENTIFIER": []
    }

def generate_mock_practitioner() -> Dict[str, Any]:
    """Generate a high-fidelity practitioner record"""
    return {
        "ID": generate_clean_id(),
        "ACTIVE": "true",
        "NAME": [{"family": fake.last_name(), "given": [fake.first_name()], "prefix": ["Dr."]}],
        "TELECOM": [{"system": "phone", "value": fake.phone_number(), "use": "work"}],
        "GENDER": random.choice(["male", "female"]),
        "BIRTHDATE": "1980-05-15",
        "META": {"versionId": "1"},
        "IDENTIFIER": []
    }

def generate_and_save_template(resource: str, output_dir: str = "templates"):
    """Generate a template and save it to file"""
    Path(output_dir).mkdir(exist_ok=True)
    
    generators = {
        "patient": generate_mock_patient,
        "coverage": generate_mock_coverage,
        "claim": generate_mock_claim,
        "observation": generate_mock_observation,
        "encounter": generate_mock_encounter,
        "condition": generate_mock_condition,
        "medication_request": generate_mock_medication_request,
        "organization": generate_mock_organization,
        "location": generate_mock_location,
        "practitioner": generate_mock_practitioner
    }
    
    if resource not in generators:
        print(f"No generator for {resource}")
        return
    
    data = generators[resource]()
    filename = Path(output_dir) / f"{resource}_golden.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    print(f"Generated golden template: {filename}")

if __name__ == "__main__":
    resources = [
        "patient", "coverage", "claim", "observation", 
        "encounter", "condition", "medication_request",
        "organization", "location", "practitioner"
    ]
    for res in resources:
        generate_and_save_template(res)
