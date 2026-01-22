-- FHIR Patient Resource DDL
-- Snowflake Table Structure

CREATE OR REPLACE TABLE FHIR_PATIENT_RESOURCE_STG (
    SRC_TYPE VARCHAR(30) COLLATE 'utf8',
    ID VARCHAR(16777216) COLLATE 'utf8',
    MCID NUMBER(38,0),
    META VARIANT,
    ACTIVE VARCHAR(16777216) COLLATE 'utf8',
    GENDER VARCHAR(16777216) COLLATE 'utf8',
    BIRTHDATE VARCHAR(16777216) COLLATE 'utf8',
    DECEASED VARIANT,
    NAME ARRAY,
    TELECOM ARRAY,
    ADDRESS ARRAY,
    MARITAL_STATUS VARIANT,
    COMMUNICATION ARRAY,
    MULTIPLE_BIRTH_INDEX VARIANT,
    PCP VARIANT,
    MANAGING_ORG VARIANT,
    LINK ARRAY,
    EXTENSIONS ARRAY,
    IDENTIFIER ARRAY,
    PHOTO ARRAY,
    CONTACT ARRAY
);

-- Column Descriptions:
-- SRC_TYPE: Source type (e.g., "FHIR")
-- ID: Unique patient identifier
-- MCID: Master Consumer ID (numeric)
-- META: Resource metadata (JSON)
-- ACTIVE: Whether record is active ("true"/"false")
-- GENDER: Patient gender (male/female/other/unknown)
-- BIRTHDATE: Date of birth (YYYY-MM-DD)
-- DECEASED: Deceased information (boolean or dateTime)
-- NAME: Array of patient names [{use, family, given, prefix, suffix}]
-- TELECOM: Array of contact points [{system, value, use}]
-- ADDRESS: Array of addresses [{use, line, city, state, postalCode, country}]
-- MARITAL_STATUS: Marital status coding
-- COMMUNICATION: Array of languages [{language, preferred}]
-- MULTIPLE_BIRTH_INDEX: Multiple birth information
-- PCP: Primary care provider reference
-- MANAGING_ORG: Managing organization reference
-- LINK: Links to other patient records
-- EXTENSIONS: FHIR extensions
-- IDENTIFIER: Array of identifiers [{system, value}] - MRN, SSN, etc.
-- PHOTO: Patient photos
-- CONTACT: Emergency contacts
