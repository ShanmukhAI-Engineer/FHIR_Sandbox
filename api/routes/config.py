"""
Configuration Routes
"""

from fastapi import APIRouter, HTTPException
from api.models import AppConfigResponse, ResourceConfigModel
from config import (
    RESOURCES,
    get_enabled_resources,
    get_resource_display_names,
    QUICK_INPUT_OPTIONS,
    LLM_SETTINGS
)

router = APIRouter()

@router.get("/config", response_model=AppConfigResponse)
async def get_config():
    """
    Get application configuration including resources, settings, and quick inputs
    """
    try:
        # Convert RESOURCES dict to Pydantic models
        resources_dict = {}
        for key, value in RESOURCES.items():
            resources_dict[key] = ResourceConfigModel(**value)
        
        return AppConfigResponse(
            resources=resources_dict,
            enabled_resources=get_enabled_resources(),
            display_names=get_resource_display_names(),
            quick_inputs=QUICK_INPUT_OPTIONS,
            llm_settings=LLM_SETTINGS
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")
