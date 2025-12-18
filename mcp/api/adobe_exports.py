"""Adobe Cloud Services API endpoints for report generation and storage."""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, Literal
import structlog
import os
import json

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/adobe", tags=["adobe"])


# Request models
class ExportReportRequest(BaseModel):
    """Request to export operational report as PDF."""
    report_type: Literal["churn", "incidents", "executive"]
    data: Dict[str, Any]
    upload_to_cloud: bool = False


class UploadFileRequest(BaseModel):
    """Request to upload file to Adobe Cloud Storage."""
    file_path: str
    destination_folder: str = "paramount-ops"
    metadata: Optional[Dict[str, Any]] = None


# Endpoints
@router.post("/export-report")
async def export_operations_report(request: ExportReportRequest):
    """
    Export operations report as PDF using Adobe PDF Services.
    
    **Report Types:**
    - `churn`: Churn analysis with Pareto cohorts
    - `incidents`: Production incident summary
    - `executive`: Executive summary for leadership
    """
    from mcp.integrations.adobe_pdf_client import create_adobe_pdf_client
    from mcp.integrations.adobe_storage_client import create_adobe_storage_client
    from config import settings
    
    # Get Adobe PDF client
    adobe_pdf = create_adobe_pdf_client()
    if not adobe_pdf or (not adobe_pdf.enabled and not settings.mock_mode):
        raise HTTPException(
            status_code=503,
            detail="Adobe PDF Services not configured. Set ADOBE_PDF_ENABLED=true and credentials."
        )
    
    try:
        # Generate PDF based on report type
        if request.report_type == "churn":
            pdf_path = adobe_pdf.generate_churn_report(request.data)
        elif request.report_type == "incidents":
            pdf_path = adobe_pdf.generate_incident_report(request.data)
        elif request.report_type == "executive":
            pdf_path = adobe_pdf.generate_executive_summary(request.data)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown report type: {request.report_type}"
            )
        
        # Verify file was created
        if not os.path.exists(pdf_path):
            raise HTTPException(
                status_code=500,
                detail=f"PDF generation failed - file not created at {pdf_path}"
            )
        
        # Log file size for debugging
        file_size = os.path.getsize(pdf_path)
        logger.info("report_exported", type=request.report_type, path=pdf_path, size_bytes=file_size)
        
        # Optionally upload to Adobe Cloud Storage
        cloud_file_id = None
        if request.upload_to_cloud:
            storage_client = create_adobe_storage_client()
            if storage_client and storage_client.enabled:
                upload_result = storage_client.upload_pdf_report(
                    pdf_path=pdf_path,
                    report_type=request.report_type
                )
                cloud_file_id = upload_result.get('id')
                logger.info("report_uploaded_to_cloud", file_id=cloud_file_id)
        
        return {
            "status": "success",
            "report_type": request.report_type,
            "pdf_path": pdf_path,
            "filename": os.path.basename(pdf_path),
            "cloud_file_id": cloud_file_id,
            "message": f"Report exported successfully"
        }
        
    except Exception as e:
        logger.error("export_failed", error=str(e), report_type=request.report_type)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download-report/{filename}")
async def download_report(filename: str):
    """Download a generated PDF report."""
    # Security check: only allow downloading .pdf files from current dir
    if not filename.endswith(".pdf") or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = filename
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(
        path=file_path,
        media_type='application/pdf',
        filename=filename
    )


@router.post("/upload-dashboard-export")
async def upload_dashboard_export(
    data: Dict[str, Any],
    export_format: Literal["json", "csv"] = "json"
):
    """
    Upload dashboard data export to Adobe Cloud Storage.
    
    **Example:**
    ```json
    {
        "subscribers": 67500000,
        "churn_rate": 0.047,
        "revenue": 10200000000,
        "timestamp": "2025-12-18T10:30:00Z"
    }
    ```
    """
    from mcp.integrations.adobe_storage_client import create_adobe_storage_client
    
    storage_client = create_adobe_storage_client()
    if not storage_client or not storage_client.enabled:
        raise HTTPException(
            status_code=503,
            detail="Adobe Cloud Storage not configured. Set ADOBE_STORAGE_ENABLED=true and credentials."
        )
    
    try:
        result = storage_client.upload_dashboard_export(
            data=data,
            export_type=export_format
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        logger.info("dashboard_exported", file_id=result.get('id'), format=export_format)
        
        return {
            "status": "success",
            "file_id": result.get('id'),
            "format": export_format,
            "message": "Dashboard data exported to Adobe Cloud"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("upload_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list-files")
async def list_cloud_files(
    folder: str = "paramount-ops",
    file_type: Optional[str] = None
):
    """
    List files in Adobe Cloud Storage.
    
    **Example:** `/adobe/list-files?folder=paramount-ops/reports&file_type=pdf`
    """
    from mcp.integrations.adobe_storage_client import create_adobe_storage_client
    
    storage_client = create_adobe_storage_client()
    if not storage_client or not storage_client.enabled:
        raise HTTPException(
            status_code=503,
            detail="Adobe Cloud Storage not configured"
        )
    
    try:
        files = storage_client.list_files(folder=folder, file_type=file_type)
        
        return {
            "status": "success",
            "folder": folder,
            "file_count": len(files),
            "files": files
        }
        
    except Exception as e:
        logger.error("list_files_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/storage-usage")
async def get_storage_usage():
    """
    Get Adobe Cloud Storage usage statistics.
    
    **Returns:**
    - Total storage (1TB = 1,099,511,627,776 bytes)
    - Used storage
    - Available storage
    """
    from mcp.integrations.adobe_storage_client import create_adobe_storage_client
    
    storage_client = create_adobe_storage_client()
    if not storage_client or not storage_client.enabled:
        raise HTTPException(
            status_code=503,
            detail="Adobe Cloud Storage not configured"
        )
    
    try:
        usage = storage_client.get_storage_usage()
        
        if "error" in usage:
            raise HTTPException(status_code=500, detail=usage["error"])
        
        # Convert to human-readable
        total_gb = usage.get("total_bytes", 0) / (1024**3)
        used_gb = usage.get("used_bytes", 0) / (1024**3)
        available_gb = usage.get("available_bytes", 0) / (1024**3)
        
        return {
            "status": "success",
            "total_gb": round(total_gb, 2),
            "used_gb": round(used_gb, 2),
            "available_gb": round(available_gb, 2),
            "usage_percent": round((used_gb / total_gb * 100), 2) if total_gb > 0 else 0,
            "raw": usage
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("storage_usage_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def adobe_health_check():
    """
    Check Adobe services health status.
    
    **Returns:**
    - PDF Services: enabled/disabled
    - Cloud Storage: enabled/disabled
    """
    from mcp.integrations.adobe_pdf_client import create_adobe_pdf_client
    from mcp.integrations.adobe_storage_client import create_adobe_storage_client
    from config import settings
    
    pdf_client = create_adobe_pdf_client()
    storage_client = create_adobe_storage_client()
    
    return {
        "status": "success",
        "services": {
            "pdf_services": {
                "enabled": pdf_client.enabled if pdf_client else False,
                "status": "operational" if (pdf_client and pdf_client.enabled) else ("mock_operational" if settings.mock_mode else "disabled")
            },
            "cloud_storage": {
                "enabled": storage_client.enabled if storage_client else False,
                "status": "operational" if (storage_client and storage_client.enabled) else ("mock_operational" if settings.mock_mode else "disabled")
            }
        },
        "message": "Adobe services health check complete"
    }

