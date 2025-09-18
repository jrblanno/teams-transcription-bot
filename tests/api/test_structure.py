"""Tests for API code structure and imports."""

import pytest
import sys
from pathlib import Path

# Add src to Python path for testing
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestAPIStructure:
    """Test API code structure and basic imports."""

    def test_api_models_structure(self):
        """Test that API model files exist and have expected structure."""
        api_models_path = src_path / "api" / "models"

        # Check that model files exist
        assert (api_models_path / "__init__.py").exists()
        assert (api_models_path / "transcript.py").exists()
        assert (api_models_path / "meeting.py").exists()
        assert (api_models_path / "responses.py").exists()

    def test_api_services_structure(self):
        """Test that API service files exist."""
        api_services_path = src_path / "api" / "services"

        assert (api_services_path / "__init__.py").exists()
        assert (api_services_path / "storage_service.py").exists()
        assert (api_services_path / "transcript_service.py").exists()

    def test_api_routers_structure(self):
        """Test that API router files exist."""
        api_routers_path = src_path / "api" / "routers"

        assert (api_routers_path / "__init__.py").exists()
        assert (api_routers_path / "transcripts.py").exists()
        assert (api_routers_path / "meetings.py").exists()
        assert (api_routers_path / "health.py").exists()

    def test_fastapi_main_exists(self):
        """Test that FastAPI main application exists."""
        main_path = src_path / "api" / "main.py"
        assert main_path.exists()

    def test_dependencies_exists(self):
        """Test that dependencies file exists."""
        deps_path = src_path / "api" / "dependencies.py"
        assert deps_path.exists()

    def test_basic_import_structure(self):
        """Test basic import structure without external dependencies."""
        # Test that we can import basic Python structures
        try:
            # These imports should work without external dependencies
            from api.models.transcript import TranscriptFormat
            from api.models.meeting import MeetingStatus
            from api.models.responses import APIStatus

            # Test enum values
            assert TranscriptFormat.JSON == "json"
            assert MeetingStatus.IN_PROGRESS == "in_progress"
            assert APIStatus.SUCCESS == "success"

        except ImportError as e:
            pytest.fail(f"Failed to import basic structures: {e}")


class TestTerraformStructure:
    """Test that terraform infrastructure updates are in place."""

    def test_terraform_main_exists(self):
        """Test that terraform main file exists."""
        terraform_path = Path(__file__).parent.parent.parent / "terraform" / "main.tf"
        assert terraform_path.exists()

    def test_storage_account_in_terraform(self):
        """Test that Azure Storage Account is configured in terraform."""
        terraform_path = Path(__file__).parent.parent.parent / "terraform" / "main.tf"
        content = terraform_path.read_text()

        # Check for storage account resource
        assert "azurerm_storage_account" in content
        assert "transcripts" in content
        assert "azurerm_storage_container" in content

    def test_app_settings_updated(self):
        """Test that app settings include storage configuration."""
        terraform_path = Path(__file__).parent.parent.parent / "terraform" / "main.tf"
        content = terraform_path.read_text()

        # Check for storage-related app settings
        assert "AZURE_STORAGE_ACCOUNT_NAME" in content
        assert "AZURE_STORAGE_CONTAINER_NAME" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])