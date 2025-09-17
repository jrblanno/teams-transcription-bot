"""Test authentication functionality."""
import os
import pytest
from unittest.mock import Mock, patch
from src.auth.msal_client import MSALAuthClient


class TestMSALAuthClient:
    """Test MSAL authentication client."""

    def test_init_success(self):
        """Test successful initialization with real Azure credentials."""
        # Load real credentials from .env file
        from dotenv import load_dotenv
        load_dotenv()

        # Test with real credentials
        client = MSALAuthClient()
        assert client.client_id == os.getenv("BOT_APP_ID")
        assert client.client_secret == os.getenv("BOT_APP_PASSWORD")
        assert client.tenant_id == os.getenv("AZURE_TENANT_ID")
        assert client.authority == f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}"
        assert client.app is not None  # Verify MSAL app was created successfully

    @patch.dict("os.environ", {}, clear=True)
    def test_init_missing_env_vars(self):
        """Test initialization fails with missing environment variables."""
        with pytest.raises(ValueError, match="Missing required environment variables"):
            MSALAuthClient()

    @patch.dict("os.environ", {
        "BOT_APP_ID": "test-client-id",
        "BOT_APP_PASSWORD": "test-secret",
        "AZURE_TENANT_ID": "test-tenant-id"
    })
    @patch("src.auth.msal_client.msal.ConfidentialClientApplication")
    def test_get_token_success(self, mock_msal):
        """Test successful token acquisition."""
        # Mock MSAL response
        mock_app = Mock()
        mock_app.acquire_token_silent.return_value = None
        mock_app.acquire_token_for_client.return_value = {
            "access_token": "test-token",
            "expires_in": 3600
        }
        mock_msal.return_value = mock_app

        client = MSALAuthClient()
        token = client.get_token()

        assert token == "test-token"
        mock_app.acquire_token_for_client.assert_called_once_with(
            scopes=["https://graph.microsoft.com/.default"]
        )

    @patch.dict("os.environ", {
        "BOT_APP_ID": "test-client-id",
        "BOT_APP_PASSWORD": "test-secret",
        "AZURE_TENANT_ID": "test-tenant-id"
    })
    @patch("src.auth.msal_client.msal.ConfidentialClientApplication")
    def test_get_token_from_cache(self, mock_msal):
        """Test token retrieval from cache."""
        # Mock MSAL response
        mock_app = Mock()
        mock_app.acquire_token_silent.return_value = {
            "access_token": "cached-token",
            "expires_in": 3600
        }
        mock_msal.return_value = mock_app

        client = MSALAuthClient()
        token = client.get_token()

        assert token == "cached-token"
        mock_app.acquire_token_for_client.assert_not_called()

    @patch.dict("os.environ", {
        "BOT_APP_ID": "test-client-id",
        "BOT_APP_PASSWORD": "test-secret",
        "AZURE_TENANT_ID": "test-tenant-id"
    })
    @patch("src.auth.msal_client.msal.ConfidentialClientApplication")
    def test_get_token_failure(self, mock_msal):
        """Test token acquisition failure."""
        # Mock MSAL error response
        mock_app = Mock()
        mock_app.acquire_token_silent.return_value = None
        mock_app.acquire_token_for_client.return_value = {
            "error": "invalid_client",
            "error_description": "Invalid client credentials"
        }
        mock_msal.return_value = mock_app

        client = MSALAuthClient()

        with pytest.raises(Exception, match="Failed to get token: Invalid client credentials"):
            client.get_token()

    @patch.dict("os.environ", {
        "BOT_APP_ID": "test-client-id",
        "BOT_APP_PASSWORD": "test-secret",
        "AZURE_TENANT_ID": "test-tenant-id"
    })
    @patch("src.auth.msal_client.msal.ConfidentialClientApplication")
    def test_get_headers(self, mock_msal):
        """Test getting authorization headers."""
        # Mock MSAL response
        mock_app = Mock()
        mock_app.acquire_token_silent.return_value = None
        mock_app.acquire_token_for_client.return_value = {
            "access_token": "test-token",
            "expires_in": 3600
        }
        mock_msal.return_value = mock_app

        client = MSALAuthClient()
        headers = client.get_headers()

        expected_headers = {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json"
        }
        assert headers == expected_headers