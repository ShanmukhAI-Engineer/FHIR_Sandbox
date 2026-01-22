"""
Data Validator - Validate generated data against DDL and business rules
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ValidationError:
    """Represents a validation error"""
    record_index: int
    field: str
    error: str
    value: Any


@dataclass
class ValidationResult:
    """Result of validation"""
    valid: bool
    errors: List[ValidationError]
    warnings: List[str]
    records_checked: int
    records_valid: int


class DataValidator:
    """Validate generated data"""
    
    # Common FHIR/healthcare value sets
    VALID_GENDERS = ["male", "female", "other", "unknown"]
    
    def __init__(self):
        self.custom_rules = {}
    
    def validate(
        self, 
        data: List[Dict[str, Any]], 
        ddl_columns: Dict[str, str] = None,
        required_fields: List[str] = None
    ) -> ValidationResult:
        """
        Validate data against DDL and rules.
        
        Args:
            data: List of records to validate
            ddl_columns: Dict mapping column names to types
            required_fields: List of required field names
        """
        errors = []
        warnings = []
        valid_count = 0
        
        for i, record in enumerate(data):
            record_errors = self._validate_record(
                record, i, ddl_columns, required_fields
            )
            
            if record_errors:
                errors.extend(record_errors)
            else:
                valid_count += 1
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            records_checked=len(data),
            records_valid=valid_count
        )
    
    def _validate_record(
        self, 
        record: Dict[str, Any], 
        index: int,
        ddl_columns: Dict[str, str] = None,
        required_fields: List[str] = None
    ) -> List[ValidationError]:
        """Validate a single record"""
        errors = []
        
        # Check required fields
        if required_fields:
            for field in required_fields:
                if field not in record or record[field] is None:
                    errors.append(ValidationError(
                        record_index=index,
                        field=field,
                        error="Required field is missing or null",
                        value=None
                    ))
        
        # Validate data types against DDL
        if ddl_columns:
            for field, value in record.items():
                if field in ddl_columns:
                    type_error = self._validate_type(
                        value, ddl_columns[field], field
                    )
                    if type_error:
                        errors.append(ValidationError(
                            record_index=index,
                            field=field,
                            error=type_error,
                            value=value
                        ))
        
        # Common healthcare validations
        if "GENDER" in record:
            if record["GENDER"] and record["GENDER"].lower() not in self.VALID_GENDERS:
                errors.append(ValidationError(
                    record_index=index,
                    field="GENDER",
                    error=f"Invalid gender. Must be one of: {self.VALID_GENDERS}",
                    value=record["GENDER"]
                ))
        
        if "BIRTHDATE" in record:
            if record["BIRTHDATE"] and not self._is_valid_date(record["BIRTHDATE"]):
                errors.append(ValidationError(
                    record_index=index,
                    field="BIRTHDATE",
                    error="Invalid date format. Expected YYYY-MM-DD",
                    value=record["BIRTHDATE"]
                ))
        
        return errors
    
    def _validate_type(self, value: Any, expected_type: str, field: str) -> Optional[str]:
        """Validate value against expected DDL type"""
        if value is None:
            return None  # Allow nulls (separate check for required)
        
        expected_upper = expected_type.upper()
        
        # VARCHAR
        if "VARCHAR" in expected_upper:
            if not isinstance(value, str):
                return f"Expected string, got {type(value).__name__}"
            
            # Check length if specified
            match = re.search(r'VARCHAR\((\d+)\)', expected_upper)
            if match:
                max_len = int(match.group(1))
                if len(value) > max_len:
                    return f"String exceeds max length {max_len}"
        
        # NUMBER
        elif "NUMBER" in expected_upper or "INT" in expected_upper:
            if not isinstance(value, (int, float)):
                return f"Expected number, got {type(value).__name__}"
        
        # ARRAY
        elif "ARRAY" in expected_upper:
            if not isinstance(value, list):
                return f"Expected array, got {type(value).__name__}"
        
        # VARIANT (JSON object)
        elif "VARIANT" in expected_upper:
            if not isinstance(value, (dict, list, str, int, float, bool, type(None))):
                return f"Expected variant (JSON-compatible), got {type(value).__name__}"
        
        return None
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Check if string is valid YYYY-MM-DD date"""
        if not date_str:
            return False
        
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(pattern, date_str):
            return False
        
        try:
            year, month, day = map(int, date_str.split('-'))
            if month < 1 or month > 12:
                return False
            if day < 1 or day > 31:
                return False
            return True
        except:
            return False
    
    def add_custom_rule(self, field: str, rule_func, error_message: str):
        """Add a custom validation rule for a field"""
        self.custom_rules[field] = {
            "rule": rule_func,
            "message": error_message
        }


def validate_data(
    data: List[Dict[str, Any]], 
    required_fields: List[str] = None
) -> ValidationResult:
    """Convenience function to validate data"""
    validator = DataValidator()
    return validator.validate(data, required_fields=required_fields)
