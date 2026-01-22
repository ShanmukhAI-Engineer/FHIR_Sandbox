"""
Table Generator - Generate synthetic data matching DDL structure
"""

import json
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from .llm import get_llm, LLMResponse
from .prompt_builder import PromptBuilder
from rag import get_retriever, RetrievalResult
from utils.logger import get_logger

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
        record_count: int = 10,
        quick_inputs: Dict = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> Dict[str, GenerationResult]:
        """
        Generate synthetic data for specified resources.
        
        Args:
            user_prompt: Natural language description of what to generate
            resources: List of resources to generate (e.g., ["patient", "claim"])
            record_count: Number of records to generate per resource
            quick_inputs: Structured inputs (age, gender, state, etc.)
            temperature: LLM temperature
            max_tokens: Max tokens for LLM response
            
        Returns:
            Dict mapping resource name to GenerationResult
        """
        results = {}
        
        for resource in resources:
            result = self._generate_resource(
                resource=resource,
                user_prompt=user_prompt,
                record_count=record_count,
                quick_inputs=quick_inputs,
                temperature=temperature,
                max_tokens=max_tokens
            )
            results[resource] = result
        
        return results
    
    def _generate_resource(
        self,
        resource: str,
        user_prompt: str,
        record_count: int,
        quick_inputs: Dict = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> GenerationResult:
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
        
        # Build prompt
        system_message, user_message = self.prompt_builder.build_prompt(
            user_prompt=user_prompt,
            resources=[resource],
            ddl_context=retrieval.context,
            guidelines_context="",  # Already included in retrieval.context
            quick_inputs=quick_inputs,
            record_count=record_count
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
            return [], f"Invalid JSON: {str(e)}"
        except Exception as e:
            return [], f"Unexpected error: {str(e)}"
    
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
