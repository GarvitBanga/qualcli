import requests
from typing import Dict, Any, List
import os
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

class APIError(Exception):
    """Custom exception for API errors."""
    pass

class APIClient:
    def __init__(self):
        self.base_url = os.getenv('API_URL', 'http://localhost:8002')

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and errors."""
        try:
            if response.status_code != 200:
                if response.status_code == 404:
                    raise APIError("Resource not found")
                elif response.status_code == 400:
                    raise APIError(f"Bad request: {response.text}")
                elif response.status_code >= 500:
                    raise APIError("Server error - please try again later")
                else:
                    raise APIError(f"API error: {response.text}")
            return response.json()
        except requests.exceptions.RequestException as e:
            raise APIError(f"API error: {str(e)}")

    def submit_job(self, 
                  org_id: str, 
                  app_version_id: str, 
                  test_path: str,
                  priority: int = 1,
                  target: str = "emulator") -> Dict[str, Any]:
        """Submit a new job to the backend."""
        url = f"{self.base_url}/jobs/submit"
        payload = {
            "org_id": org_id,
            "app_version_id": app_version_id,
            "test_path": test_path,
            "priority": priority,
            "target": target
        }
        
        try:
            response = requests.post(url, json=payload)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            raise APIError(f"API error: {str(e)}")

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a job."""
        url = f"{self.base_url}/jobs/{job_id}"
        try:
            response = requests.get(url)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            raise APIError(f"API error: {str(e)}")

    def get_grouped_jobs(self, app_version_id: str) -> List[Dict[str, Any]]:
        """Get all jobs for a specific app version."""
        url = f"{self.base_url}/jobs/group/{app_version_id}"
        try:
            response = requests.get(url)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            raise APIError(f"API error: {str(e)}")
    
    def get_devices(self) -> Dict[str, Any]:
        """Get all devices and their current status."""
        url = f"{self.base_url}/devices"
        
        try:
            response = requests.get(url)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            raise APIError(f"API error: {str(e)}")
    
    def get_device_status(self) -> Dict[str, Any]:
        """Get device pool status and utilization metrics."""
        url = f"{self.base_url}/devices/status"
        
        try:
            response = requests.get(url)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            raise APIError(f"API error: {str(e)}")
    
    def get_device_recommendations(self, target_type: str) -> Dict[str, Any]:
        """Get device allocation recommendations for a specific target type."""
        url = f"{self.base_url}/devices/recommendations/{target_type}"
        
        try:
            response = requests.get(url)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            raise APIError(f"API error: {str(e)}")
    
    def perform_health_check(self) -> Dict[str, Any]:
        """Perform health check on all devices."""
        url = f"{self.base_url}/devices/health-check"
        
        try:
            response = requests.post(url)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            raise APIError(f"API error: {str(e)}") 

class QualClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.Client()
    
    def submit_job(self, org_id: str, app_version_id: str, test_path: str, priority: int = 1, target: str = "local"):
        """Submit a new test job"""
        response = self.client.post(f"{self.base_url}/jobs/submit", json={
            "org_id": org_id,
            "app_version_id": app_version_id,
            "test_path": test_path,
            "priority": priority,
            "target": target
        })
        response.raise_for_status()
        return response.json()["job_id"]
    
    def get_job_status(self, job_id: int):
        """Get status of a specific job"""
        response = self.client.get(f"{self.base_url}/jobs/{job_id}")
        response.raise_for_status()
        return response.json()["status"]
    
    def get_jobs_by_app_version(self, app_version_id: str):
        """Get all jobs for a specific app version"""
        response = self.client.get(f"{self.base_url}/jobs/group/{app_version_id}")
        response.raise_for_status()
        # The response is a list of jobs directly
        return response.json() 