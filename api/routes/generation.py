"""
Generation Routes
"""

from fastapi import APIRouter, HTTPException
from api.models import GenerationRequest, GenerationResponse, GenerationResult
from generator.table_generator import TableGenerator
from utils import MD5Hasher, validate_data
from config import get_resource_config
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/generate", response_model=GenerationResponse)
async def generate_data(request: GenerationRequest):
    """
    Generate synthetic FHIR data based on user prompt and selected resources
    """
    try:
        logger.info(f"Generation request: {request.user_prompt[:50]}... Resources: {request.resources}")
        
        # Initialize generator
        generator = TableGenerator()
        
        # Convert quick_inputs to dict if provided
        quick_inputs_dict = None
        if request.quick_inputs:
            quick_inputs_dict = request.quick_inputs.model_dump(exclude_none=True)
        
        # Generate data
        results = generator.generate(
            user_prompt=request.user_prompt,
            resources=request.resources,
            record_count=request.record_count,
            quick_inputs=quick_inputs_dict,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Process results
        response_results = {}
        for resource, result in results.items():
            if result.success:
                data = result.data
                validation_errors = []
                
                # Apply MD5 if needed
                config = get_resource_config(resource)
                md5_fields = config.get("md5_fields", [])
                if md5_fields:
                    hasher = MD5Hasher()
                    data = hasher.hash_fields(data, md5_fields)
                
                # Validate data
                validation = validate_data(data)
                if not validation.valid:
                    validation_errors = [str(e) for e in validation.errors[:10]]
                    logger.warning(f"Validation errors for {resource}: {len(validation.errors)}")
                
                response_results[resource] = GenerationResult(
                    success=True,
                    data=data,
                    validation_errors=validation_errors if validation_errors else None
                )
                logger.info(f"Successfully generated {len(data)} records for {resource}")
            else:
                response_results[resource] = GenerationResult(
                    success=False,
                    error=result.error
                )
                logger.error(f"Failed to generate {resource}: {result.error}")
        
        return GenerationResponse(
            results=response_results,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.exception("Fatal error during generation")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
