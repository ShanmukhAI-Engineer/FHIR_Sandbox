"""
Pydantic Models for API Request/Response Validation
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Literal

# Configuration Models
class LLMSettingsModel(BaseModel):
    default_temperature: float
    default_max_tokens: int
    timeout_seconds: int

class QuickInputOptionsModel(BaseModel):
    gender: List[str]
    states: List[str]
    insurance_types: List[str]
    age_range: Dict[str, int]

class ResourceConfigModel(BaseModel):
    enabled: bool
    display_name: str
    description: str
    ddl_file: str
    knowledge_dir: str
    template_file: str
    exclude_columns: List[str]
    md5_fields: List[str]
    relationships: List[Dict[str, str]]

class AppConfigResponse(BaseModel):
    resources: Dict[str, ResourceConfigModel]
    enabled_resources: List[str]
    display_names: Dict[str, str]
    quick_inputs: QuickInputOptionsModel
    llm_settings: LLMSettingsModel

# Generation Models
class QuickInputs(BaseModel):
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    gender: Optional[str] = None
    state: Optional[str] = None
    insurance_type: Optional[str] = None

class GenerationRequest(BaseModel):
    user_prompt: str = Field(..., min_length=1)
    resources: List[str] = Field(..., min_items=1)
    record_count: int = Field(default=5, ge=1, le=100)
    quick_inputs: Optional[QuickInputs] = None
    temperature: Optional[float] = Field(default=0.7, ge=0, le=1)
    max_tokens: Optional[int] = Field(default=4000, ge=500, le=8000)

class GenerationResult(BaseModel):
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    validation_errors: Optional[List[str]] = None

class GenerationResponse(BaseModel):
    results: Dict[str, GenerationResult]
    timestamp: str

# Knowledge Base Models
class ResourceKnowledgeStatus(BaseModel):
    ddl_exists: bool
    knowledge_exists: bool
    document_count: int

class KnowledgeStatusResponse(BaseModel):
    total_documents: int
    resources: Dict[str, ResourceKnowledgeStatus]

class IndexRequest(BaseModel):
    resource: str

class IndexResponse(BaseModel):
    success: bool
    chunks_indexed: int
    resource: str

# LLM Models
class EnterpriseConfig(BaseModel):
    base_url: str
    has_client_id: bool
    has_client_secret: bool

class LLMStatusResponse(BaseModel):
    active_llm: str
    enterprise_configured: bool
    enterprise_config: Optional[EnterpriseConfig] = None
    connection_status: Literal["connected", "disconnected", "error"]

# Export Models
class ExportRequest(BaseModel):
    data: List[Dict[str, Any]]
    apply_md5: bool = True

class ExportResponse(BaseModel):
    success: bool
    filepath: Optional[str] = None
    download_url: Optional[str] = None
    error: Optional[str] = None
