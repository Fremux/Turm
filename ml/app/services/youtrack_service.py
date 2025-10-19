"""YouTrack integration service for creating tasks."""

import requests
import json
from typing import Optional, Dict, Any

from app.core.config import settings
from app.core.logging import logger


class YouTrackService:
    """Service for interacting with YouTrack API."""
    
    def __init__(self):
        """Initialize YouTrack service with settings."""
        self.base_url = settings.YOUTRACK_URL
        self.token = settings.YT_TOKEN
        self.default_project = settings.YOUTRACK_DEFAULT_PROJECT
        self._enabled = bool(self.base_url and self.token)
        
        if not self._enabled:
            logger.warning(
                "youtrack_integration_disabled",
                reason="Missing YOUTRACK_URL or YT_TOKEN in environment"
            )
    
    def is_enabled(self) -> bool:
        """Check if YouTrack integration is enabled."""
        return self._enabled
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for YouTrack API."""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def get_project_id_by_name(self, project_name: str) -> Optional[str]:
        """Get YouTrack project ID by name or short name.
        
        Args:
            project_name: Project name or short name
            
        Returns:
            Project ID if found, None otherwise
        """
        if not self._enabled:
            return None
            
        try:
            response = requests.get(
                f"{self.base_url}/api/admin/projects",
                headers=self.get_auth_headers(),
                params={
                    'fields': 'id,name,shortName'
                },
                timeout=10
            )
            response.raise_for_status()
            
            projects = response.json()
            
            # Search for project by name or shortName
            for project in projects:
                if (project.get('name', '').lower() == project_name.lower() or
                    project.get('shortName', '').lower() == project_name.lower()):
                    project_id = project.get('id')
                    logger.info(
                        "youtrack_project_found",
                        project_name=project_name,
                        project_id=project_id
                    )
                    return project_id
            
            logger.warning(
                "youtrack_project_not_found",
                project_name=project_name,
                available_projects=[p.get('shortName', p.get('name', 'Unknown')) for p in projects[:5]]
            )
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(
                "youtrack_get_project_failed",
                project_name=project_name,
                error=str(e),
                error_details=getattr(e.response, 'text', None) if hasattr(e, 'response') else None
            )
            return None
    
    def create_task(
        self,
        summary: str,
        description: str
    ) -> Optional[Dict[str, Any]]:
        """Create a task in YouTrack.
        
        Args:
            summary: Task summary (title)
            description: Task description
            
        Returns:
            Created task data if successful, None otherwise
        """
        if not self._enabled:
            logger.debug("youtrack_task_creation_skipped", reason="Integration disabled")
            return None
        
        # Always use default project
        project_id = self.get_project_id_by_name(self.default_project)
        
        if not project_id:
            logger.warning(
                "youtrack_task_creation_failed",
                reason="Project not found",
                project_name=self.default_project
            )
            return None
        
        # Prepare task data - only summary and description
        task_data = {
            "project": {"id": project_id},
            "summary": summary,
            "description": description
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/issues",
                headers=self.get_auth_headers(),
                data=json.dumps(task_data),
                params={
                    'fields': 'id,idReadable,summary'
                },
                timeout=15
            )
            response.raise_for_status()
            
            created_task = response.json()
            logger.info(
                "youtrack_task_created",
                task_id=created_task.get('idReadable'),
                summary=summary,
                project=self.default_project
            )
            return created_task
            
        except requests.exceptions.RequestException as e:
            logger.error(
                "youtrack_task_creation_error",
                summary=summary,
                project=self.default_project,
                error=str(e),
                error_details=getattr(e.response, 'text', None) if hasattr(e, 'response') else None
            )
            return None


# Global instance
youtrack_service = YouTrackService()

