"""Adobe Cloud Storage integration for file management and collaboration."""

import os
import json
import tempfile
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class AdobeStorageClient:
    """
    Client for Adobe Cloud Storage API.
    
    Provides 1TB of cloud storage for dashboard exports, logs, reports,
    and operational data with team collaboration features.
    """
    
    def __init__(
        self,
        access_token: str,
        api_endpoint: str = "https://cc-api-storage.adobe.io",
        enabled: bool = True
    ):
        """
        Initialize Adobe Storage client.
        
        Args:
            access_token: Adobe API access token
            api_endpoint: Adobe Cloud Storage API endpoint
            enabled: Whether Adobe storage is enabled
        """
        self.access_token = access_token
        self.api_endpoint = api_endpoint
        self.enabled = enabled
        
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "x-api-key": os.getenv("ADOBE_CLIENT_ID", ""),
        }
        
        if enabled:
            logger.info("adobe_storage_initialized", endpoint=api_endpoint)
        else:
            logger.warning("adobe_storage_disabled")
    
    def upload_file(
        self,
        file_path: str,
        destination_folder: str = "paramount-ops",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload file to Adobe Cloud Storage.
        
        Args:
            file_path: Local file path to upload
            destination_folder: Folder path in Adobe Cloud
            metadata: Optional metadata tags
            
        Returns:
            Upload response with file ID and details
        """
        if not self.enabled:
            logger.warning("adobe_storage_not_enabled", message="Returning mock response")
            return {
                "id": f"mock_{os.path.basename(file_path)}",
                "name": os.path.basename(file_path),
                "folder": destination_folder,
                "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                "status": "mock_upload"
            }
        
        try:
            filename = os.path.basename(file_path)
            
            # Read file
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            # Prepare upload metadata
            upload_data = {
                "name": filename,
                "folder": destination_folder,
                "size": len(file_content),
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat(),
                "content_type": self._get_content_type(filename)
            }
            
            # Upload file
            # Note: Actual Adobe Cloud Storage API may differ
            # This is a generic implementation pattern
            response = requests.post(
                f"{self.api_endpoint}/files/upload",
                headers=self.headers,
                files={"file": (filename, file_content)},
                data={"metadata": json.dumps(upload_data)}
            )
            
            if response.status_code in [200, 201]:
                logger.info(
                    "file_uploaded",
                    filename=filename,
                    folder=destination_folder,
                    size=len(file_content)
                )
                return response.json()
            else:
                logger.error(
                    "upload_failed",
                    status=response.status_code,
                    error=response.text
                )
                return {"error": response.text, "status_code": response.status_code}
                
        except FileNotFoundError:
            logger.error("file_not_found", path=file_path)
            return {"error": f"File not found: {file_path}"}
        except Exception as e:
            logger.error("upload_exception", error=str(e), file=file_path)
            return {"error": str(e)}
    
    def upload_dashboard_export(
        self,
        data: Dict[str, Any],
        export_type: str = "json",
        name_prefix: str = "dashboard_export"
    ) -> Dict[str, Any]:
        """
        Export dashboard data to Adobe Cloud.
        
        Args:
            data: Dashboard data to export
            export_type: File format (json, csv)
            name_prefix: Prefix for filename
            
        Returns:
            Upload response with cloud file ID
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix=f'.{export_type}',
            prefix=f'{name_prefix}_{timestamp}_',
            delete=False
        )
        
        try:
            if export_type == "json":
                json.dump(data, temp_file, indent=2)
            elif export_type == "csv":
                # Simple CSV export (could be enhanced)
                import csv
                if isinstance(data, list) and len(data) > 0:
                    writer = csv.DictWriter(temp_file, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                else:
                    temp_file.write("No data available")
            
            temp_file.close()
            
            # Upload
            result = self.upload_file(
                file_path=temp_file.name,
                destination_folder="paramount-ops/exports",
                metadata={
                    "type": "dashboard_export",
                    "timestamp": timestamp,
                    "format": export_type,
                    "source": "paramount-ops-dashboard"
                }
            )
            
            return result
            
        finally:
            # Cleanup
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def upload_log_file(self, log_path: str) -> Dict[str, Any]:
        """
        Upload application logs to Adobe Cloud for archival.
        
        Args:
            log_path: Path to log file
            
        Returns:
            Upload response
        """
        return self.upload_file(
            file_path=log_path,
            destination_folder="paramount-ops/logs",
            metadata={
                "type": "application_log",
                "environment": os.getenv("ENVIRONMENT", "development"),
                "archived_at": datetime.utcnow().isoformat()
            }
        )
    
    def upload_pdf_report(self, pdf_path: str, report_type: str) -> Dict[str, Any]:
        """
        Upload generated PDF report to Adobe Cloud.
        
        Args:
            pdf_path: Path to PDF file
            report_type: Type of report (churn, incidents, executive)
            
        Returns:
            Upload response
        """
        return self.upload_file(
            file_path=pdf_path,
            destination_folder="paramount-ops/reports",
            metadata={
                "type": f"{report_type}_report",
                "format": "pdf",
                "generated_by": "adobe_pdf_services",
                "uploaded_at": datetime.utcnow().isoformat()
            }
        )
    
    def list_files(
        self,
        folder: str = "paramount-ops",
        file_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List files in Adobe Cloud folder.
        
        Args:
            folder: Folder path to list
            file_type: Optional filter by file type
            
        Returns:
            List of file metadata objects
        """
        if not self.enabled:
            logger.warning("adobe_storage_not_enabled", message="Returning mock list")
            return [
                {
                    "id": "mock_1",
                    "name": "sample_export.json",
                    "folder": folder,
                    "size": 1024,
                    "created": datetime.utcnow().isoformat()
                }
            ]
        
        try:
            response = requests.get(
                f"{self.api_endpoint}/files/list",
                headers=self.headers,
                params={"folder": folder, "type": file_type}
            )
            
            if response.status_code == 200:
                files = response.json().get('files', [])
                logger.info("files_listed", folder=folder, count=len(files))
                return files
            else:
                logger.error("list_failed", status=response.status_code)
                return []
                
        except Exception as e:
            logger.error("list_exception", error=str(e))
            return []
    
    def download_file(self, file_id: str, destination_path: str) -> bool:
        """
        Download file from Adobe Cloud.
        
        Args:
            file_id: Cloud file ID
            destination_path: Local path to save file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning("adobe_storage_not_enabled", message="Cannot download in mock mode")
            return False
        
        try:
            response = requests.get(
                f"{self.api_endpoint}/files/{file_id}/download",
                headers=self.headers,
                stream=True
            )
            
            if response.status_code == 200:
                with open(destination_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info("file_downloaded", file_id=file_id, path=destination_path)
                return True
            else:
                logger.error("download_failed", status=response.status_code)
                return False
                
        except Exception as e:
            logger.error("download_exception", error=str(e))
            return False
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete file from Adobe Cloud.
        
        Args:
            file_id: Cloud file ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning("adobe_storage_not_enabled", message="Cannot delete in mock mode")
            return False
        
        try:
            response = requests.delete(
                f"{self.api_endpoint}/files/{file_id}",
                headers=self.headers
            )
            
            if response.status_code in [200, 204]:
                logger.info("file_deleted", file_id=file_id)
                return True
            else:
                logger.error("delete_failed", status=response.status_code)
                return False
                
        except Exception as e:
            logger.error("delete_exception", error=str(e))
            return False
    
    def get_storage_usage(self) -> Dict[str, Any]:
        """
        Get storage usage statistics.
        
        Returns:
            Storage usage data (used, available, total)
        """
        if not self.enabled:
            return {
                "total_bytes": 1099511627776,  # 1TB
                "used_bytes": 0,
                "available_bytes": 1099511627776,
                "status": "mock"
            }
        
        try:
            response = requests.get(
                f"{self.api_endpoint}/storage/usage",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error("usage_check_failed", status=response.status_code)
                return {"error": "Failed to get storage usage"}
                
        except Exception as e:
            logger.error("usage_exception", error=str(e))
            return {"error": str(e)}
    
    def _get_content_type(self, filename: str) -> str:
        """Determine content type from filename."""
        ext = os.path.splitext(filename)[1].lower()
        
        content_types = {
            '.pdf': 'application/pdf',
            '.json': 'application/json',
            '.csv': 'text/csv',
            '.txt': 'text/plain',
            '.log': 'text/plain',
            '.html': 'text/html',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.mp4': 'video/mp4'
        }
        
        return content_types.get(ext, 'application/octet-stream')


def create_adobe_storage_client() -> Optional[AdobeStorageClient]:
    """
    Create Adobe Storage client from environment variables.
    
    Returns:
        AdobeStorageClient if configured, None otherwise
    """
    access_token = os.getenv("ADOBE_ACCESS_TOKEN", "")
    api_endpoint = os.getenv("ADOBE_STORAGE_API_ENDPOINT", "https://cc-api-storage.adobe.io")
    enabled = os.getenv("ADOBE_STORAGE_ENABLED", "false").lower() == "true"
    
    if not access_token or not enabled:
        logger.info(
            "adobe_storage_not_configured",
            message="Set ADOBE_ACCESS_TOKEN and ADOBE_STORAGE_ENABLED=true"
        )
        # Return client with enabled=False for mock mode
        return AdobeStorageClient(
            access_token="mock_token",
            api_endpoint=api_endpoint,
            enabled=False
        )
    
    return AdobeStorageClient(
        access_token=access_token,
        api_endpoint=api_endpoint,
        enabled=enabled
    )

