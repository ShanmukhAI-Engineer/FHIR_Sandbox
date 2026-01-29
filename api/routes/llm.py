"""
LLM Status Routes
"""

from fastapi import APIRouter, HTTPException
from api.models import LLMStatusResponse, EnterpriseConfig
from generator.llm import get_active_llm_name
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/status", response_model=LLMStatusResponse)
async def get_llm_status():
    """
    Get LLM configuration and connection status
    """
    try:
        # Get active LLM name
        active_llm = get_active_llm_name()
        
        # Check enterprise configuration
        base_url = os.getenv("ENTERPRISE_BASE_URL")
        client_id = os.getenv("ENTERPRISE_CLIENT_ID")
        client_secret = os.getenv("ENTERPRISE_CLIENT_SECRET")
        
        enterprise_configured = bool(base_url and client_id and client_secret)
        
        # Determine connection status
        connection_status = "connected" if enterprise_configured else "disconnected"
        
        # Build enterprise config if available
        enterprise_config = None
        if base_url:
            enterprise_config = EnterpriseConfig(
                base_url=base_url,
                has_client_id=bool(client_id),
                has_client_secret=bool(client_secret)
            )
        
        return LLMStatusResponse(
            active_llm=active_llm,
            enterprise_configured=enterprise_configured,
            enterprise_config=enterprise_config,
            connection_status=connection_status
        )
    except Exception as e:
        logger.exception("Failed to get LLM status")
        raise HTTPException(status_code=500, detail=f"Failed to get LLM status: {str(e)}")
