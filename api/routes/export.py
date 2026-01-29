"""
Export Routes
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from api.models import ExportRequest, ExportResponse
from utils import CSVExporter
from pathlib import Path
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/export/{resource}", response_model=ExportResponse)
async def export_to_csv(resource: str, request: ExportRequest):
    """
    Export generated data to CSV file
    """
    try:
        if not request.data:
            raise HTTPException(status_code=400, detail="No data provided for export")
        
        # Create exporter instance
        exporter = CSVExporter()
        
        # Export to CSV
        filepath = exporter.export(request.data, resource)
        
        logger.info(f"Exported {len(request.data)} records to {filepath}")
        
        # Generate download URL
        filename = Path(filepath).name
        download_url = f"/api/download/{filename}"
        
        return ExportResponse(
            success=True,
            filepath=str(filepath),
            download_url=download_url
        )
    except Exception as e:
        logger.exception(f"Failed to export {resource}")
        return ExportResponse(
            success=False,
            error=str(e)
        )

@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download exported CSV file
    """
    try:
        # Construct file path
        from config import OUTPUT_DIR
        file_path = Path(OUTPUT_DIR) / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Security check: ensure file is within OUTPUT_DIR
        if not file_path.resolve().is_relative_to(Path(OUTPUT_DIR).resolve()):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return FileResponse(
            path=str(file_path),
            media_type="text/csv",
            filename=filename
        )
    except Exception as e:
        logger.exception(f"Failed to download file {filename}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
