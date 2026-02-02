"""
Table Generator - Generate synthetic data matching DDL structure
"""

import json
import re
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path

from .llm import get_llm, LLMResponse
from .prompt_builder import PromptBuilder
from rag import get_retriever, RetrievalResult
from config import get_resource_config
from utils.logger import get_logger
from utils.ddl_parser import get_columns_from_ddl
from utils.dependency_graph import DependencyGraph
import random

logger = get_logger("generator")


@dataclass
class GenerationResult:
    """Result from data generation"""
    success: bool
    data: List[Dict[str, Any]]
    resource: str
    record_count: int
    llm_response: LLMResponse
    error: Optional[str] = None
    warnings: List[str] = None


class TableGenerator:
    """Generate synthetic tabular data using LLM"""
    
    def __init__(self):
        self.llm = get_llm()
        self.retriever = get_retriever()
        self.prompt_builder = PromptBuilder()
        logger.debug("TableGenerator initialized")
    
    def generate(
        self,
        user_prompt: str,
        resources: List[str],
        record_count: Union[int, Dict[str, int]] = 10,
        quick_inputs: Dict = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        session_context: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> Dict[str, GenerationResult]:
        """
        Generate synthetic data for specified resources.
        """
        results = {}
        context_data = {} # Keep track of generated records for relationships
        
        # If we have session context, pre-seed context_data with it
        if session_context:
            context_data.update(session_context)
        
        # Auto-sort resources based on dependencies
        dep_graph = DependencyGraph(resources)
        sorted_resources = dep_graph.get_execution_order()
        logger.info(f"Execution order: {sorted_resources}")
        
        for resource in sorted_resources:
            # Determine count for this specific resource
            res_count = 10
            if isinstance(record_count, int):
                res_count = record_count
            elif isinstance(record_count, dict):
                res_count = record_count.get(resource, 5)

            result = self._generate_resource(
                resource=resource,
                user_prompt=user_prompt,
                record_count=res_count,
                quick_inputs=quick_inputs,
                temperature=temperature,
                max_tokens=max_tokens,
                relationship_context=context_data,
                session_context=session_context
            )
            
            # Post-processing: Enforce Integrity
            if result.success and result.data:
                 result.data = self._enforce_referential_integrity(
                     resource=resource,
                     data=result.data,
                     context=context_data
                 )
            results[resource] = result
            
            # Store newly generated records for the next resource
            if result.success and result.data:
                context_data[resource] = result.data
        
        return results
    
    def _generate_resource(
        self,
        resource: str,
        user_prompt: str,
        record_count: int,
        quick_inputs: Dict = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        relationship_context: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        session_context: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> GenerationResult:
        # Filter context to ONLY what is needed for this resource
        filtered_context = {}
        if relationship_context:
            res_config = get_resource_config(resource)
            if res_config:
                # Get list of parent resources this resource actually depends on
                needed_parents = set()
                for rel in res_config.get("relationships", []):
                     ref = rel.get("references", "").split(".")[0]
                     if ref:
                         needed_parents.add(ref)
                
                # Filter context
                for parent, data in relationship_context.items():
                    if parent in needed_parents:
                        filtered_context[parent] = data

        """Generate data for a single resource"""
        warnings = []
        
        # Retrieve context from RAG
        retrieval = self.retriever.retrieve(
            query=user_prompt,
            resources=[resource],
            include_ddl=True
        )
        
        if retrieval.warning:
            warnings.append(retrieval.warning)
            logger.warning(f"RAG warning for {resource}: {retrieval.warning}")
        
        logger.info(f"RAG retrieved {retrieval.total_found} chunks for {resource}")
        
        # Extract required columns from DDL if available
        required_columns = []
        ddl_text = self.retriever.get_ddl_for_resource(resource)
        if ddl_text:
             # If exact DDL file content is available, use it
             required_columns = get_columns_from_ddl(ddl_text)
        elif retrieval.context:
             # Try to extract from context (less reliable but fallback)
             # Better to rely on retrieving the DDL specifically
             pass
             
        if required_columns:
            logger.debug(f"Enforcing {len(required_columns)} columns for {resource}")
 
        # Load template if configured
        sample_template = None
        config = get_resource_config(resource)
        if config and config.get("template_file"):
            template_path = Path(config["template_file"])
            if template_path.exists():
                try:
                    with open(template_path, "r", encoding="utf-8") as f:
                        sample_template = f.read()
                    logger.debug(f"Loaded custom template for {resource} from {template_path}")
                except Exception as e:
                    logger.error(f"Failed to load template for {resource}: {e}")

        # Build prompt
        system_message, user_message = self.prompt_builder.build_prompt(
            user_prompt=user_prompt,
            resources=[resource],
            ddl_context=retrieval.context,
            guidelines_context="",  # Already included in retrieval.context
            sample_template=sample_template,
            quick_inputs=quick_inputs,
            record_count=record_count,
            required_columns=required_columns,
            relationship_context=filtered_context,
            session_context=session_context
        )
        
        logger.debug(f"Prompt built for {resource}. System msg length: {len(system_message)}")
        
        # Call LLM
        llm_response = self.llm.generate(
            prompt=user_message,
            system_message=system_message,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        logger.info(f"LLM completed in {llm_response.latency_ms:.2f}ms. Tokens: {llm_response.completion_tokens}")
        
        if not llm_response.success:
            logger.error(f"LLM generation failed for {resource}: {llm_response.error}")
            return GenerationResult(
                success=False,
                data=[],
                resource=resource,
                record_count=0,
                llm_response=llm_response,
                error=f"LLM Error: {llm_response.error}",
                warnings=warnings
            )
        
        # Parse response
        data, parse_error = self._parse_response(llm_response.content)
        
        if parse_error:
            logger.error(f"Failed to parse response for {resource}: {parse_error}")
            return GenerationResult(
                success=False,
                data=[],
                resource=resource,
                record_count=0,
                llm_response=llm_response,
                error=f"Parse Error: {parse_error}",
                warnings=warnings
            )
        
        # Validate count
        if len(data) != record_count:
            warning = f"Requested {record_count} records, got {len(data)}"
            warnings.append(warning)
            logger.warning(f"{resource}: {warning}")
        
        return GenerationResult(
            success=True,
            data=data,
            resource=resource,
            record_count=len(data),
            llm_response=llm_response,
            warnings=warnings
        )
    
    def _parse_response(self, response: str) -> tuple[List[Dict], Optional[str]]:
        """Parse LLM response into JSON data"""
        try:
            # DEBUG: Log what we received from LLM
            logger.info(f"[PARSE DEBUG] Response length: {len(response) if response else 0}")
            if not response:
                logger.error("[PARSE DEBUG] Response is EMPTY!")
                return [], "LLM returned empty response"
            logger.info(f"[PARSE DEBUG] First 200 chars: {response[:200] if len(response) > 200 else response}")
            
            # Clean response - remove markdown code blocks if present
            cleaned = response.strip()
            
            # Remove markdown code blocks
            if cleaned.startswith("```"):
                # Remove opening ```json or ```
                cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned)
                # Remove closing ```
                cleaned = re.sub(r'\n?```\s*$', '', cleaned)
            
            # Try to find JSON array in response
            # Look for [ ... ] pattern
            match = re.search(r'\[[\s\S]*\]', cleaned)
            if match:
                cleaned = match.group(0)
            
            # Parse JSON
            data = json.loads(cleaned)
            
            # Ensure it's a list
            if isinstance(data, dict):
                data = [data]
            
            if not isinstance(data, list):
                return [], "Response is not a JSON array"
            
            return data, None
            
        except json.JSONDecodeError as e:
            logger.error(f"[PARSE DEBUG] JSON decode failed. Cleaned content: {cleaned[:300] if cleaned else 'EMPTY'}")
            return [], f"Invalid JSON: {str(e)}"
        except Exception as e:
            return [], f"Unexpected error: {str(e)}"

    def _enforce_referential_integrity(
        self,
        resource: str,
        data: List[Dict[str, Any]],
        context: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Post-process generated data to ensure referential integrity.
        - Verifies FKs match existing parents
        - Backfills missing links
        - Propagates attributes (e.g. Patient Name -> Claim)
        """
        config = get_resource_config(resource)
        if not config or not config.get("relationships"):
            return data

        relationships = config.get("relationships", [])
        
        for row in data:
            for rel in relationships:
                col_name = rel["column"]
                ref = rel["references"]
                
                # Parse reference (e.g., "patient.ID")
                parent_res_name, parent_col = ref.split(".")
                
                # specific validation logic only if we have context for this parent
                parent_data = context.get(parent_res_name)
                if not parent_data:
                    continue
                
                # Get generated FK value
                fk_val = row.get(col_name)
                
                # Find matching parent record
                parent_record = None
                
                # 1. Try to find the record that matches the generated FK
                if fk_val:
                    for p in parent_data:
                        # Check ID match (handling potential type mismatches)
                        if str(p.get(parent_col)) == str(fk_val):
                            parent_record = p
                            break
                            
                # 2. If no match (or invalid FK), pick a random parent
                if not parent_record:
                    parent_record = random.choice(parent_data)
                    # FIX: Overwrite the invalid FK with the valid one
                    row[col_name] = parent_record.get(parent_col)
                    logger.debug(f"Repaired FK for {resource}.{col_name}: {fk_val} -> {row[col_name]}")
                
                # 3. Propagate Attributes (if configured)
                # Map parent attributes to child columns as defined in config
                map_attrs = rel.get("map_attributes", {})
                for parent_attr_path, child_col in map_attrs.items():
                    # parent_attr_path is like "patient.MCID" or just "MCID"
                    p_attr = parent_attr_path.split(".")[-1] # take the last part
                    
                    if p_attr in parent_record:
                        row[child_col] = parent_record[p_attr]
    
        return data
    
    def generate_simple(
        self,
        resource: str,
        ddl: str,
        record_count: int = 10,
        additional_instructions: str = "",
        temperature: float = 0.7
    ) -> GenerationResult:
        """
        Simple generation with just DDL and count.
        Useful for testing without RAG.
        """
        system_message, user_message = self.prompt_builder.build_simple_prompt(
            resource=resource,
            ddl=ddl,
            record_count=record_count,
            additional_instructions=additional_instructions
        )
        
        llm_response = self.llm.generate(
            prompt=user_message,
            system_message=system_message,
            temperature=temperature,
            max_tokens=4000
        )
        
        if not llm_response.success:
            return GenerationResult(
                success=False,
                data=[],
                resource=resource,
                record_count=0,
                llm_response=llm_response,
                error=f"LLM Error: {llm_response.error}"
            )
        
        data, parse_error = self._parse_response(llm_response.content)
        
        if parse_error:
            return GenerationResult(
                success=False,
                data=[],
                resource=resource,
                record_count=0,
                llm_response=llm_response,
                error=f"Parse Error: {parse_error}"
            )
        
        return GenerationResult(
            success=True,
            data=data,
            resource=resource,
            record_count=len(data),
            llm_response=llm_response
        )


# Convenience function
def generate_synthetic_data(
    user_prompt: str,
    resources: List[str],
    record_count: int = 10,
    quick_inputs: Dict = None,
    temperature: float = 0.7
) -> Dict[str, GenerationResult]:
    """Convenience function to generate synthetic data"""
    generator = TableGenerator()
    return generator.generate(
        user_prompt=user_prompt,
        resources=resources,
        record_count=record_count,
        quick_inputs=quick_inputs,
        temperature=temperature
    )
