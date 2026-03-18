"""Backend API client for the DONS Cloud Migration Platform."""

from typing import Any, Tuple, List, Optional
import requests


class DONSApiClient:
    """Client for communicating with the DONS backend API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.timeout = 120

    def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[dict] = None,
        files: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> Tuple[bool, Any]:
        """Make an HTTP request and return (success, data_or_error) tuple."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                json=json,
                files=files,
                params=params,
                timeout=self.timeout,
            )
            if response.status_code >= 400:
                error_detail = response.json().get("detail", response.text)
                return False, error_detail
            return True, response.json()
        except requests.exceptions.ConnectionError:
            return False, "Unable to connect to backend. Please ensure the API server is running."
        except requests.exceptions.Timeout:
            return False, "Request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"
        except ValueError:
            # JSON decode error - return raw text
            return True, response.text

    # Health check
    def health_check(self) -> Tuple[bool, Any]:
        """Check backend health status."""
        return self._request("GET", "/health")

    # Migration endpoints (existing backend)
    def upload_infrastructure(self, file) -> Tuple[bool, Any]:
        """Upload infrastructure file for analysis."""
        files = {"file": (file.name, file.getvalue(), "application/octet-stream")}
        return self._request("POST", "/api/upload", files=files)

    def analyze(self, upload_id: str) -> Tuple[bool, Any]:
        """Analyze uploaded infrastructure."""
        return self._request("POST", "/api/analyze", json={"upload_id": upload_id})

    def generate_escape_plan(self, upload_id: str) -> Tuple[bool, Any]:
        """Generate migration escape plan."""
        return self._request("POST", "/api/escape-plan", json={"upload_id": upload_id})

    def calculate_costs(self, upload_id: str) -> Tuple[bool, Any]:
        """Calculate cost comparison."""
        return self._request("POST", "/api/cost", json={"upload_id": upload_id})

    def generate_terraform(self, plan_id: str) -> Tuple[bool, Any]:
        """Generate Terraform code for migration."""
        return self._request("POST", "/api/generate-terraform", json={"plan_id": plan_id})

    def deploy(self, plan_id: str) -> Tuple[bool, Any]:
        """Deploy infrastructure to DigitalOcean."""
        url = f"{self.base_url}/api/deploy"
        try:
            response = requests.post(
                url,
                json={"plan_id": plan_id, "confirm": True},
                timeout=600,  # 10 min — deployments can take a while
            )
            if response.status_code >= 400:
                error_detail = response.json().get("detail", response.text)
                return False, error_detail
            return True, response.json()
        except requests.exceptions.Timeout:
            return False, "Deployment is still in progress. Check your DigitalOcean dashboard."
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"

    def destroy(self, plan_id: str) -> Tuple[bool, Any]:
        """Destroy deployed infrastructure."""
        return self._request("POST", "/api/destroy", json={"plan_id": plan_id, "confirm": True})

    # Store Intelligence endpoints (new - will be built later)
    def upload_documents(self, files: List) -> Tuple[bool, Any]:
        """Upload documents for Store Intelligence processing."""
        file_data = [
            ("files", (f.name, f.getvalue(), "application/octet-stream"))
            for f in files
        ]
        return self._request("POST", "/api/documents/upload", files=file_data)

    def get_knowledge_base_status(self) -> Tuple[bool, Any]:
        """Get knowledge base status."""
        return self._request("GET", "/api/knowledge-base/status")

    def ask_intelligence(self, question: str) -> Tuple[bool, Any]:
        """Ask a question to the Store Intelligence agent."""
        return self._request("POST", "/api/intelligence/ask", json={"question": question})

    def delete_document(self, document_id: str) -> Tuple[bool, Any]:
        """Delete a document from the knowledge base."""
        return self._request("DELETE", f"/api/documents/{document_id}")
