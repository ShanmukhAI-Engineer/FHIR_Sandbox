"""
Knowledge Base Routes
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from api.models import KnowledgeStatusResponse, ResourceKnowledgeStatus, IndexRequest, IndexResponse
from rag import get_retriever, get_vector_store
from config import get_enabled_resources, get_resource_config
from pathlib import Path
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/status", response_model=KnowledgeStatusResponse)
async def get_knowledge_status():
    """
    Get knowledge base status including document counts per resource
    """
    try:
        vector_store = get_vector_store()
        total_documents = vector_store.count()
        
        resources_status = {}
        for resource in get_enabled_resources():
            config = get_resource_config(resource)
            
            # Check if DDL and knowledge directories exist
            ddl_exists = os.path.exists(config.get("ddl_file", ""))
            knowledge_dir = config.get("knowledge_dir", "")
            knowledge_exists = (
                os.path.exists(knowledge_dir) and 
                any(Path(knowledge_dir).iterdir()) if os.path.exists(knowledge_dir) else False
            )
            
            # Get document count
            doc_count = 0
            
            resources_status[resource] = ResourceKnowledgeStatus(
                ddl_exists=ddl_exists,
                knowledge_exists=knowledge_exists,
                document_count=doc_count
            )
        
        return KnowledgeStatusResponse(
            total_documents=total_documents,
            resources=resources_status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge status: {str(e)}")

@router.post("/index", response_model=IndexResponse)
async def index_resource(request: IndexRequest):
    """
    Index a specific resource's DDL and guidelines
    """
    try:
        resource = request.resource
        config = get_resource_config(resource)
        
        if not config:
            raise HTTPException(status_code=404, detail=f"Resource {resource} not found")
        
        retriever = get_retriever()
        total_chunks = 0
        
        # Index DDL
        ddl_file = config.get("ddl_file", "")
        if os.path.exists(ddl_file):
            chunks = retriever.index_ddl(ddl_file, resource)
            total_chunks += chunks
            logger.info(f"Indexed {chunks} chunks from DDL for {resource}")
        
        # Index knowledge directory
        knowledge_dir = config.get("knowledge_dir", "")
        if os.path.exists(knowledge_dir):
            chunks = retriever.index_directory(knowledge_dir, resource)
            total_chunks += chunks
            logger.info(f"Indexed {chunks} chunks from knowledge dir for {resource}")
        
        return IndexResponse(
            success=True,
            chunks_indexed=total_chunks,
            resource=resource
        )
    except Exception as e:
        logger.exception(f"Failed to index resource {request.resource}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

@router.post("/index/all", response_model=IndexResponse)
async def index_all_resources():
    """
    Index all enabled resources
    """
    try:
        total_chunks = 0
        for resource in get_enabled_resources():
            response = await index_resource(IndexRequest(resource=resource))
            total_chunks += response.chunks_indexed
        
        # Also index global knowledge
        global_dir = "knowledge/global"
        if os.path.exists(global_dir):
            retriever = get_retriever()
            chunks = retriever.index_directory(global_dir, "global")
            total_chunks += chunks
        
        return IndexResponse(
            success=True,
            chunks_indexed=total_chunks,
            resource="all"
        )
    except Exception as e:
        logger.exception("Failed to index all resources")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

@router.post("/upload", response_model=IndexResponse)
async def upload_document(
    file: UploadFile = File(...),
    target_resource: str = Form(...)
):
    """
    Upload and index a document file
    """
    try:
        # Validate file type
        allowed_extensions = [".txt", ".pdf", ".csv"]
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not allowed. Allowed: {allowed_extensions}"
            )
        
        # Determine target directory
        if target_resource == "global":
            target_dir = Path("knowledge/global")
        else:
            config = get_resource_config(target_resource)
            if not config:
                raise HTTPException(status_code=404, detail=f"Resource {target_resource} not found")
            target_dir = Path(config.get("knowledge_dir", f"knowledge/{target_resource}"))
        
        # Create directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = target_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Saved file to {file_path}")
        
        # Index the file
        retriever = get_retriever()
        chunks = retriever.index_directory(str(target_dir), target_resource)
        
        return IndexResponse(
            success=True,
            chunks_indexed=chunks,
            resource=target_resource
        )
    except Exception as e:
        logger.exception("Failed to upload document")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
