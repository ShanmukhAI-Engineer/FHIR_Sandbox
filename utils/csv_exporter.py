"""
CSV Exporter - Export generated data to CSV files
"""

import os
import json
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class CSVExporter:
    """Export data to CSV files"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def export(
        self, 
        data: List[Dict[str, Any]], 
        resource: str,
        filename: str = None,
        include_timestamp: bool = True,
        flatten_json: bool = False
    ) -> str:
        """
        Export data to CSV file.
        
        Args:
            data: List of records to export
            resource: Resource name (used in filename)
            filename: Custom filename (optional)
            include_timestamp: Add timestamp to filename
            flatten_json: Flatten nested JSON or keep as string
            
        Returns:
            Path to exported file
        """
        if not data:
            raise ValueError("No data to export")
        
        # Generate filename
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if include_timestamp else ""
            filename = f"{resource}_{timestamp}.csv" if timestamp else f"{resource}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Process data
        processed_data = self._process_data(data, flatten_json)
        
        # Get all columns
        columns = self._get_all_columns(processed_data)
        
        # Write CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(processed_data)
        
        return filepath
    
    def _process_data(
        self, 
        data: List[Dict[str, Any]], 
        flatten_json: bool
    ) -> List[Dict[str, Any]]:
        """Process data for CSV export"""
        processed = []
        
        for record in data:
            processed_record = {}
            
            for key, value in record.items():
                if isinstance(value, (dict, list)):
                    if flatten_json and isinstance(value, dict):
                        # Flatten dict into separate columns
                        for sub_key, sub_value in value.items():
                            flat_key = f"{key}_{sub_key}"
                            processed_record[flat_key] = self._serialize_value(sub_value)
                    else:
                        # Keep as JSON string
                        processed_record[key] = json.dumps(value, ensure_ascii=False)
                else:
                    processed_record[key] = value
            
            processed.append(processed_record)
        
        return processed
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize a value to string for CSV"""
        if value is None:
            return ""
        elif isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        else:
            return str(value)
    
    def _get_all_columns(self, data: List[Dict[str, Any]]) -> List[str]:
        """Get all unique columns from data, preserving order"""
        columns = []
        seen = set()
        
        for record in data:
            for key in record.keys():
                if key not in seen:
                    columns.append(key)
                    seen.add(key)
        
        return columns
    
    def export_multiple(
        self, 
        data_dict: Dict[str, List[Dict[str, Any]]],
        include_timestamp: bool = True
    ) -> Dict[str, str]:
        """
        Export multiple resources to separate CSV files.
        
        Args:
            data_dict: Dict mapping resource name to data list
            include_timestamp: Add timestamp to filenames
            
        Returns:
            Dict mapping resource name to file path
        """
        results = {}
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if include_timestamp else ""
        
        for resource, data in data_dict.items():
            if data:
                filename = f"{resource}_{timestamp}.csv" if timestamp else f"{resource}.csv"
                filepath = self.export(
                    data=data,
                    resource=resource,
                    filename=filename,
                    include_timestamp=False  # Already handled above
                )
                results[resource] = filepath
        
        return results


def export_to_csv(
    data: List[Dict[str, Any]], 
    resource: str,
    output_dir: str = "output"
) -> str:
    """Convenience function to export data to CSV"""
    exporter = CSVExporter(output_dir=output_dir)
    return exporter.export(data, resource)
