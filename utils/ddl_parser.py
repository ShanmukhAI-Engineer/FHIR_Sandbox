"""
DDL Parser - Parse Snowflake DDL to extract column information
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Column:
    """Represents a table column"""
    name: str
    data_type: str
    nullable: bool = True
    default: Optional[str] = None
    constraints: List[str] = None


@dataclass
class TableSchema:
    """Represents a table schema"""
    table_name: str
    columns: List[Column]
    raw_ddl: str


class DDLParser:
    """Parse Snowflake DDL statements"""
    
    def __init__(self):
        pass
    
    def parse(self, ddl: str) -> Optional[TableSchema]:
        """
        Parse a DDL statement and extract table schema.
        
        Args:
            ddl: CREATE TABLE statement
            
        Returns:
            TableSchema or None if parsing fails
        """
        try:
            # Extract table name
            table_name = self._extract_table_name(ddl)
            if not table_name:
                return None
            
            # Extract columns
            columns = self._extract_columns(ddl)
            
            return TableSchema(
                table_name=table_name,
                columns=columns,
                raw_ddl=ddl
            )
        except Exception as e:
            print(f"Error parsing DDL: {e}")
            return None
    
    def _extract_table_name(self, ddl: str) -> Optional[str]:
        """Extract table name from DDL"""
        # Match CREATE [OR REPLACE] TABLE [schema.]table_name
        pattern = r'CREATE\s+(?:OR\s+REPLACE\s+)?TABLE\s+(?:\w+\.)?(\w+)'
        match = re.search(pattern, ddl, re.IGNORECASE)
        
        if match:
            return match.group(1)
        return None
    
    def _extract_columns(self, ddl: str) -> List[Column]:
        """Extract column definitions from DDL"""
        columns = []
        
        # Find content between parentheses
        paren_match = re.search(r'\(([\s\S]+)\)', ddl)
        if not paren_match:
            return columns
        
        content = paren_match.group(1)
        
        # Split by lines and parse each column
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip().rstrip(',')
            if not line:
                continue
            
            # Skip comments and constraints
            if line.startswith('--') or line.upper().startswith(('PRIMARY KEY', 'FOREIGN KEY', 'CONSTRAINT', 'COMMENT', ')')):
                continue
            
            column = self._parse_column_line(line)
            if column:
                columns.append(column)
        
        return columns
    
    def _parse_column_line(self, line: str) -> Optional[Column]:
        """Parse a single column definition line"""
        # Pattern: column_name data_type [constraints]
        # Handle complex types like VARCHAR(100), NUMBER(38,0), TIMESTAMP_NTZ(9)
        
        pattern = r'^(\w+)\s+([\w\(\),\s]+?)(?:\s+(NOT\s+NULL|NULL|DEFAULT|PRIMARY|COLLATE|COMMENT).+)?$'
        match = re.match(pattern, line, re.IGNORECASE)
        
        if not match:
            # Try simpler pattern
            parts = line.split(None, 2)
            if len(parts) >= 2:
                return Column(
                    name=parts[0],
                    data_type=parts[1].rstrip(','),
                    nullable=True,
                    constraints=[]
                )
            return None
        
        name = match.group(1)
        data_type = match.group(2).strip().rstrip(',')
        rest = match.group(3) or ""
        
        # Determine nullable
        nullable = "NOT NULL" not in rest.upper()
        
        # Extract default
        default = None
        default_match = re.search(r"DEFAULT\s+(.+?)(?:\s+|$)", rest, re.IGNORECASE)
        if default_match:
            default = default_match.group(1).strip().rstrip(',')
        
        return Column(
            name=name,
            data_type=data_type,
            nullable=nullable,
            default=default,
            constraints=[]
        )
    
    def get_column_dict(self, ddl: str) -> Dict[str, str]:
        """
        Parse DDL and return simple dict of column_name -> data_type.
        Useful for validation.
        """
        schema = self.parse(ddl)
        if not schema:
            return {}
        
        return {col.name: col.data_type for col in schema.columns}
    
    def get_column_names(self, ddl: str, exclude: List[str] = None) -> List[str]:
        """Get list of column names, optionally excluding some"""
        schema = self.parse(ddl)
        if not schema:
            return []
        
        exclude = exclude or []
        return [col.name for col in schema.columns if col.name not in exclude]


def parse_ddl(ddl: str) -> Optional[TableSchema]:
    """Convenience function to parse DDL"""
    parser = DDLParser()
    return parser.parse(ddl)


def get_columns_from_ddl(ddl: str, exclude: List[str] = None) -> List[str]:
    """Get column names from DDL"""
    parser = DDLParser()
    return parser.get_column_names(ddl, exclude)
