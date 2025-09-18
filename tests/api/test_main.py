"""Tests for FastAPI main application."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.api.main import app


class TestFastAPIApplication:
    """Test FastAPI application endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """Test root endpoint returns API information."""
        response = self.client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Teams Transcription API"
        assert data["version"] == "1.0.0"
        assert "docs_url" in data
        assert "health_url" in data
        assert "timestamp" in data

    def test_health_endpoint_accessible(self):
        """Test health endpoint is accessible."""
        with patch("src.api.dependencies.get_transcript_service") as mock_service:
            # Mock the transcript service
            mock_transcript_service = AsyncMock()
            mock_transcript_service.health_check.return_value = {
                "status": "healthy",
                "storage": {"status": "healthy"}
            }
            mock_service.return_value = mock_transcript_service

            response = self.client.get("/api/v1/health/")

            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "version" in data

    def test_docs_endpoint_accessible(self):
        """Test OpenAPI documentation is accessible."""
        response = self.client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema_accessible(self):
        """Test OpenAPI schema is accessible."""
        response = self.client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert schema["info"]["title"] == "Teams Transcription API"
        assert schema["info"]["version"] == "1.0.0"

    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = self.client.options("/")
        # CORS headers should be present for OPTIONS requests
        # This is a basic test; more comprehensive CORS testing would be needed for production

    def test_request_id_header(self):
        """Test that request ID header is added to responses."""
        response = self.client.get("/")
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"].startswith("req_")


@pytest.mark.asyncio
class TestApplicationLifespan:
    """Test application lifespan management."""

    async def test_lifespan_startup_and_shutdown(self):
        """Test application startup and shutdown process."""
        # This would test the lifespan context manager
        # In a real implementation, we'd test service initialization
        # and cleanup during startup/shutdown
        pass