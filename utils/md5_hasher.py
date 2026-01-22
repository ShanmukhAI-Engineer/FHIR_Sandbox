"""
MD5 Hasher - Apply MD5 hashing to sensitive fields (PHI protection)
"""

import hashlib
import json
from typing import List, Dict, Any, Optional


class MD5Hasher:
    """Apply MD5 hashing to specified fields in data"""
    
    def __init__(self, salt: str = ""):
        """
        Initialize hasher with optional salt.
        
        Args:
            salt: Optional salt to add to values before hashing
        """
        self.salt = salt
    
    def hash_value(self, value: Any) -> str:
        """Hash a single value"""
        if value is None:
            return None
        
        # Convert to string and add salt
        str_value = f"{self.salt}{str(value)}"
        
        # Generate MD5 hash
        return hashlib.md5(str_value.encode('utf-8')).hexdigest()
    
    def hash_fields(
        self, 
        data: List[Dict[str, Any]], 
        fields: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Hash specified fields in a list of records.
        
        Args:
            data: List of records (dicts)
            fields: List of field paths to hash
                   Supports nested paths like:
                   - "SSN" (simple field)
                   - "IDENTIFIER[*].value" (all values in array)
                   - "NAME[*].family" (specific field in array objects)
        
        Returns:
            Data with specified fields hashed
        """
        result = []
        
        for record in data:
            hashed_record = self._hash_record(record.copy(), fields)
            result.append(hashed_record)
        
        return result
    
    def _hash_record(self, record: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Hash fields in a single record"""
        for field_path in fields:
            self._hash_field_path(record, field_path)
        return record
    
    def _hash_field_path(self, record: Dict[str, Any], field_path: str):
        """
        Hash a field at the given path.
        
        Supports patterns:
        - "FIELD" - simple field
        - "ARRAY[*].field" - field in all array elements
        - "ARRAY[*]" - all values in array
        """
        if "[*]" in field_path:
            # Handle array pattern
            parts = field_path.split("[*]")
            array_key = parts[0]
            sub_path = parts[1].lstrip(".") if len(parts) > 1 else ""
            
            if array_key in record and isinstance(record[array_key], list):
                for item in record[array_key]:
                    if sub_path:
                        if isinstance(item, dict) and sub_path in item:
                            item[sub_path] = self.hash_value(item[sub_path])
                    else:
                        # Hash the entire item if it's a simple value
                        if not isinstance(item, (dict, list)):
                            idx = record[array_key].index(item)
                            record[array_key][idx] = self.hash_value(item)
        else:
            # Simple field
            if field_path in record:
                record[field_path] = self.hash_value(record[field_path])
    
    def get_hash_preview(
        self, 
        data: List[Dict[str, Any]], 
        fields: List[str],
        preview_count: int = 3
    ) -> Dict[str, List[Dict]]:
        """
        Show before/after preview of hashing.
        
        Returns:
            Dict with "before" and "after" lists
        """
        preview_data = data[:preview_count]
        hashed_data = self.hash_fields(
            [record.copy() for record in preview_data], 
            fields
        )
        
        return {
            "before": preview_data,
            "after": hashed_data,
            "fields_hashed": fields
        }


def hash_phi_fields(
    data: List[Dict[str, Any]], 
    fields: List[str],
    salt: str = ""
) -> List[Dict[str, Any]]:
    """Convenience function to hash PHI fields"""
    hasher = MD5Hasher(salt=salt)
    return hasher.hash_fields(data, fields)
