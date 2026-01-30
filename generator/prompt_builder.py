"""
Prompt Builder - Construct prompts for LLM generation
"""

from typing import List, Dict, Optional
import os
import json
from pathlib import Path


class PromptBuilder:
    """Build structured prompts for FHIR data generation"""
    
    SYSTEM_PROMPT = """You are a synthetic healthcare data generator. Your task is to generate realistic data that matches the exact table structure provided.

CRITICAL RULES:
1. Output MUST be valid JSON array
2. Each object MUST contain ALL specified columns
3. Data types MUST match (VARCHAR→string, NUMBER→number, ARRAY→[], VARIANT→{})
4. Follow the sample format EXACTLY if provided
5. Apply all guidelines provided
6. Generate realistic, consistent data
7. All IDs MUST be alphanumeric strings exactly 32 characters long (e.g., '3f987ee038494bddb2433e7f0113948e')
8. Do NOT include any explanation, only the JSON array"""

    def __init__(self):
        pass
    
    def build_prompt(
        self,
        user_prompt: str,
        resources: List[str],
        ddl_context: str,
        guidelines_context: str,
        sample_template: Optional[str] = None,
        quick_inputs: Optional[Dict] = None,
        record_count: int = 10,
        required_columns: Optional[List[str]] = None,
        relationship_context: Optional[Dict[str, List[str]]] = None
    ) -> tuple[str, str]:
        """
        Build the complete prompt for LLM.
        
        Returns:
            Tuple of (system_message, user_message)
        """
        # Build user message parts
        parts = []
        
        # 1. Table Structure (DDL)
        if ddl_context:
            parts.append("## TABLE STRUCTURE")
            parts.append(ddl_context)
            parts.append("")
        
        # 2. Guidelines
        if guidelines_context:
            parts.append("## GUIDELINES")
            parts.append(guidelines_context)
            parts.append("")
        
        # 3. Sample Template
        if sample_template:
            parts.append("## SAMPLE FORMAT")
            parts.append("Follow this exact format for each record:")
            parts.append(sample_template)
            parts.append("")
        
        # 4. Quick Inputs (structured inputs from UI)
        if quick_inputs:
            parts.append("## CONSTRAINTS")
            constraints = self._format_quick_inputs(quick_inputs)
            parts.append(constraints)
            parts.append("")
        
        # 4. RELATIONSHIPS (Stateful ID mapping)
        if relationship_context:
            parts.append("## RELATIONSHIPS")
            parts.append("To maintain referential integrity, use the following IDs for reference fields:")
            for res_type, ids in relationship_context.items():
                if ids:
                    parts.append(f"- {res_type.upper()} IDs: {', '.join(ids[:20])}") # Limit to avoid token bloat
            parts.append("Randomly select from these IDs when a resource needs to reference another.")
            parts.append("")

        # 5. User Request
        parts.append("## USER REQUEST")
        parts.append(user_prompt)
        parts.append("")
        
        # 6. Output Instructions
        parts.append("## OUTPUT INSTRUCTIONS")
        parts.append(f"Generate exactly {record_count} records as a JSON array.")
        parts.append("Resources to generate: " + ", ".join(resources))
        
        if required_columns:
            parts.append("IMPORTANT: Each object MUST include the following keys exactly:")
            parts.append("[" + ", ".join(required_columns) + "]")
            parts.append("Do not omit any columns.")
            parts.append("For optional VARIANT/ARRAY fields (e.g., EXTENSIONS, LINK, PHOTO):")
            parts.append("- Use realistic values if they make sense for the patient.")
            parts.append("- Use null or [] ONLY if the field is truly not applicable.")
        
        parts.append("Return ONLY the JSON array, no explanations or markdown.")
        
        user_message = "\n".join(parts)
        
        return self.SYSTEM_PROMPT, user_message
    
    def _format_quick_inputs(self, quick_inputs: Dict) -> str:
        """Format quick inputs into readable constraints"""
        constraints = []
        
        if quick_inputs.get("first_name"):
            constraints.append(f"- First name should include: {quick_inputs['first_name']}")
        
        if quick_inputs.get("last_name"):
            constraints.append(f"- Last name should include: {quick_inputs['last_name']}")
        
        if quick_inputs.get("age_min") is not None and quick_inputs.get("age_max") is not None:
            constraints.append(f"- Age range: {quick_inputs['age_min']} to {quick_inputs['age_max']} years")
        
        if quick_inputs.get("gender"):
            constraints.append(f"- Gender: {quick_inputs['gender']}")
        
        if quick_inputs.get("state"):
            constraints.append(f"- State/Location: {quick_inputs['state']}")
        
        if quick_inputs.get("city"):
            constraints.append(f"- City: {quick_inputs['city']}")
        
        if quick_inputs.get("insurance_type"):
            constraints.append(f"- Insurance type: {quick_inputs['insurance_type']}")
        
        if quick_inputs.get("condition"):
            constraints.append(f"- Medical condition: {quick_inputs['condition']}")
        
        # Handle any additional custom inputs
        for key, value in quick_inputs.items():
            if key not in ['first_name', 'last_name', 'age_min', 'age_max', 
                          'gender', 'state', 'city', 'insurance_type', 'condition']:
                if value is not None and value != "":
                    constraints.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        return "\n".join(constraints) if constraints else "No specific constraints."
    
    def build_simple_prompt(
        self,
        resource: str,
        ddl: str,
        record_count: int = 10,
        additional_instructions: str = ""
    ) -> tuple[str, str]:
        """Build a simple prompt with just DDL and count"""
        
        user_message = f"""## TABLE STRUCTURE
{ddl}

## INSTRUCTIONS
Generate {record_count} realistic records for the {resource} table.
{additional_instructions}

Return ONLY a valid JSON array with {record_count} objects.
Each object must have all columns from the DDL.
For ARRAY columns, use JSON arrays.
For VARIANT columns, use JSON objects.
"""
        
        return self.SYSTEM_PROMPT, user_message


def build_generation_prompt(
    user_prompt: str,
    resources: List[str],
    ddl_context: str,
    guidelines_context: str = "",
    record_count: int = 10,
    quick_inputs: Dict = None
) -> tuple[str, str]:
    """Convenience function to build a generation prompt"""
    builder = PromptBuilder()
    return builder.build_prompt(
        user_prompt=user_prompt,
        resources=resources,
        ddl_context=ddl_context,
        guidelines_context=guidelines_context,
        quick_inputs=quick_inputs,
        record_count=record_count
    )
